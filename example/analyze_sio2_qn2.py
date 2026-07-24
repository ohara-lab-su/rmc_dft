#!/usr/bin/env python3
"""VASP POSCAR から SiO2 の Qn 分布を解析する。

RMC_POT の second-neighbour constraint (SNC) の定義に合わせて、
中心 Si、第一近接 O、第二近接 Si の関係を周期境界条件下で調べる。

このスクリプトはファイルへ結果を書き出さず、標準出力へ表示する。
"""

from collections import Counter
from pathlib import Path
import sys
from typing import Dict, List, Optional, Set, Tuple

from pymatgen.core import Structure
from rmc_dft import RmcPot, RmcPotLog
from x_logger import XLogger


# =============================================================================
# ユーザー設定
# =============================================================================

# 構造ファイルの探索候補。
DEFAULT_POSCAR_PATH = Path("POSCAR")
POSCAR_VASP_PATH = Path("POSCAR.vasp")
AAA_VASP_PATH = Path("aaa.vasp")
AAA_CFG_PATH = Path("aaa.cfg")

# Qn解析で使用する元素記号。
CENTER_ELEMENT = "Si"
FIRST_NEIGHBOR_ELEMENT = "O"
SECOND_NEIGHBOR_ELEMENT = "Si"

# CFGからPOSCARへ変換するときの元素順。
# aaa.cfg 内の元素番号の並びと一致させる。
CFG_ELEMENT_INFO = [
    "Si",
    "O",
]

# 中心元素から第一近接元素までの距離範囲 [Å]。
CENTER_FIRST_MIN = 1.40
CENTER_FIRST_MAX = 1.90

# 第一近接元素から第二近接元素までの距離範囲 [Å]。
FIRST_SECOND_MIN = 1.40
FIRST_SECOND_MAX = 1.90

# 画面へ必ず表示する Qn。
DISPLAY_QN = [4, 3, 2]

# Qnに分類されなかった中心原子の詳細を表示する。
DISPLAY_UNMATCHED_DETAILS = True



def get_structure_file_paths(
    argument_path: Optional[str],
) -> List[Path]:
    """構造ファイルの探索候補を作成する。

    Args:
        argument_path: コマンドライン引数で指定されたファイル名。
            指定されていない場合は ``None``。

    Returns:
        探索順に並べた4個のファイルパス。
    """
    if argument_path is None:
        first_path = DEFAULT_POSCAR_PATH
    else:
        first_path = Path(argument_path)

    return [
        first_path,
        POSCAR_VASP_PATH,
        AAA_VASP_PATH,
        AAA_CFG_PATH,
    ]


def convert_cfg_to_poscar(
    cfg_path: Path,
    output_path: Path,
) -> Path:
    """CFGをPOSCAR形式へ変換する。

    Args:
        cfg_path: 変換元CFGファイル。
        output_path: 生成するPOSCAR形式ファイル。

    Returns:
        生成されたPOSCAR形式ファイル。

    Raises:
        FileExistsError: 生成先が既に存在する場合。
        FileNotFoundError: 変換後のファイルが生成されなかった場合。
    """
    if output_path.exists():
        raise FileExistsError(
            f"既存ファイルは上書きしません: {output_path}"
        )

    cfg_name = str(cfg_path.with_suffix(""))
    element_info = CFG_ELEMENT_INFO

    print()
    print(f"[CONVERT] {cfg_path} から {output_path} を生成します")

    logger = XLogger(
        log_level="debug",
        logger_name="conv_cfg2poscar",
    )
    rmc_log = RmcPotLog(
        cfg_name=cfg_name,
        logger=logger,
    )
    rmc = RmcPot(
        rmc_log=rmc_log,
        cfg_name=cfg_name,
        logger=logger,
    )
    rmc.cfg2poscar(
        cfg_name=cfg_name,
        element_info=element_info,
    )

    if not output_path.exists():
        raise FileNotFoundError(
            "変換処理は終了しましたが、生成ファイルが見つかりません: "
            f"{output_path}"
        )

    print(f"[GENERATED] {output_path}")

    return output_path


def find_structure_file(
    argument_path: Optional[str],
) -> Path:
    """解析に使用する構造ファイルを決定する。

    Args:
        argument_path: コマンドライン引数で指定されたファイル名。
            指定されていない場合は ``None``。

    Returns:
        解析に使用するPOSCAR形式ファイル。

    Raises:
        FileNotFoundError: 候補ファイルがすべて存在しない場合。
    """
    candidate_paths = get_structure_file_paths(argument_path)

    for index, candidate_path in enumerate(candidate_paths, 1):
        print(f"[TRY {index}/4] {candidate_path}")

        if not candidate_path.exists():
            continue

        print(f"[FOUND] {candidate_path}")

        if candidate_path == AAA_CFG_PATH:
            structure_path = convert_cfg_to_poscar(
                cfg_path=candidate_path,
                output_path=AAA_VASP_PATH,
            )
            print(f"[USE] {structure_path}")
            return structure_path

        print(f"[USE] {candidate_path}")
        return candidate_path

    tried_names = ", ".join(
        str(candidate_path)
        for candidate_path in candidate_paths
    )
    raise FileNotFoundError(
        f"構造ファイルが見つかりません。探索対象: {tried_names}"
    )


def check_distance_range(
    minimum: float,
    maximum: float,
    name: str,
) -> None:
    """距離範囲を検証する。

    Args:
        minimum: 距離範囲の下限 [Å]。
        maximum: 距離範囲の上限 [Å]。
        name: エラーメッセージへ表示する距離範囲名。

    Raises:
        ValueError: 下限が負、または上限が下限以下の場合。
    """
    if minimum < 0.0:
        raise ValueError(f"{name} の下限は 0 以上で指定してください。")

    if maximum <= minimum:
        raise ValueError(
            f"{name} の上限は下限より大きくしてください。"
        )


def check_sio2_structure(structure: Structure) -> None:
    """構造が Si と O だけから構成されることを確認する。

    Args:
        structure: pymatgen で読み込んだ結晶構造。

    Raises:
        ValueError: Si と O 以外の元素を含む場合、または Si/O がない場合。

    Notes:
        Si:O=1:2 の厳密な組成比は要求しない。欠陥構造や非化学量論構造も
        Qn 解析対象にできるようにする。
    """
    elements: Set[str] = set()

    for site in structure:
        elements.add(site.specie.symbol)

    allowed = {
        CENTER_ELEMENT,
        FIRST_NEIGHBOR_ELEMENT,
        SECOND_NEIGHBOR_ELEMENT,
    }

    unsupported = elements - allowed
    if unsupported:
        names = ", ".join(sorted(unsupported))
        raise ValueError(
            "設定された解析元素以外を含む構造は扱いません。"
            f"検出元素: {names}"
        )

    required_elements = {
        CENTER_ELEMENT,
        FIRST_NEIGHBOR_ELEMENT,
        SECOND_NEIGHBOR_ELEMENT,
    }

    for required_element in required_elements:
        if required_element not in elements:
            raise ValueError(
                f"構造中に {required_element} がありません。"
            )


def unique_neighbor_indices(
    structure: Structure,
    center_index: int,
    neighbor_symbol: str,
    minimum: float,
    maximum: float,
) -> List[int]:
    """指定元素の近接原子インデックスを取得する。

    Args:
        structure: 解析対象構造。
        center_index: 中心原子の 0 始まりインデックス。
        neighbor_symbol: 対象とする近接元素記号。
        minimum: 距離範囲の下限 [Å]。
        maximum: 距離範囲の上限 [Å]。

    Returns:
        距離範囲内にある対象元素の 0 始まりインデックス一覧。

    Notes:
        pymatgen の近接探索は周期境界条件を考慮する。同じ原子インデックスが
        複数の周期像として返る場合、この解析では一つにまとめる。
        通常の非晶質 SiO2 セルではセル長が cutoff より十分大きいため、
        同一原子の複数周期像は近接範囲へ入らないことを想定する。
    """
    center_site = structure[center_index]
    neighbors = structure.get_neighbors(
        center_site,
        maximum,
    )

    indices: Set[int] = set()

    for neighbor in neighbors:
        neighbor_index = int(neighbor.index)

        if neighbor_index == center_index:
            continue

        symbol = neighbor.specie.symbol
        if symbol != neighbor_symbol:
            continue

        distance = float(neighbor.nn_distance)
        if distance < minimum:
            continue

        if distance > maximum:
            continue

        indices.add(neighbor_index)

    return sorted(indices)


def analyze_si_site(
    structure: Structure,
    si_index: int,
) -> Dict[str, object]:
    """一つの Si 原子について SNC の Qn 条件を評価する。

    Args:
        structure: 解析対象構造。
        si_index: 中心 Si の 0 始まりインデックス。

    Returns:
        第一近接 O 数、第二近接 Si を持つ O 数、Qn 判定、
        非該当理由などを含む辞書。

    Notes:
        RMC_POT の SNC では、中心 Si が n 個の第一近接 O を持ち、
        その各 O が中心 Si 以外の第二近接 Si を少なくとも一つ持つ場合に
        Qn 条件を満たす。

        第一近接 O が n 個あっても、そのうち一つでも第二近接 Si を
        持たなければ、その Si はこの SNC 定義の Qn には該当しない。
    """
    first_oxygen_indices = unique_neighbor_indices(
        structure=structure,
        center_index=si_index,
        neighbor_symbol=FIRST_NEIGHBOR_ELEMENT,
        minimum=CENTER_FIRST_MIN,
        maximum=CENTER_FIRST_MAX,
    )

    bridging_oxygen_indices: List[int] = []
    non_bridging_oxygen_indices: List[int] = []

    for oxygen_index in first_oxygen_indices:
        second_si_indices = unique_neighbor_indices(
            structure=structure,
            center_index=oxygen_index,
            neighbor_symbol=SECOND_NEIGHBOR_ELEMENT,
            minimum=FIRST_SECOND_MIN,
            maximum=FIRST_SECOND_MAX,
        )

        second_si_except_center: List[int] = []

        for second_si_index in second_si_indices:
            if second_si_index != si_index:
                second_si_except_center.append(second_si_index)

        if second_si_except_center:
            bridging_oxygen_indices.append(oxygen_index)
        else:
            non_bridging_oxygen_indices.append(oxygen_index)

    first_count = len(first_oxygen_indices)
    bridging_count = len(bridging_oxygen_indices)

    qn: int
    classified = False
    reason = ""

    if first_count == bridging_count:
        qn = first_count
        classified = True
        reason = "all_first_neighbours_have_second_si"
    else:
        qn = -1
        reason = "first_neighbour_without_second_si"

    return {
        "si_index": si_index,
        "first_oxygen_count": first_count,
        "bridging_oxygen_count": bridging_count,
        "non_bridging_oxygen_count": len(non_bridging_oxygen_indices),
        "first_oxygen_indices": first_oxygen_indices,
        "bridging_oxygen_indices": bridging_oxygen_indices,
        "non_bridging_oxygen_indices": non_bridging_oxygen_indices,
        "classified": classified,
        "qn": qn,
        "reason": reason,
    }


def analyze_qn(structure: Structure) -> Dict[str, object]:
    """構造中の全 Si について Qn 分布を計算する。

    Args:
        structure: 解析対象構造。

    Returns:
        Qn 別個数、非該当個数、Si ごとの詳細結果を含む辞書。
    """
    details: List[Dict[str, object]] = []
    counts: Counter[int] = Counter()
    unmatched_count = 0

    for index, site in enumerate(structure):
        if site.specie.symbol != CENTER_ELEMENT:
            continue

        result = analyze_si_site(
            structure=structure,
            si_index=index,
        )
        details.append(result)

        classified = bool(result["classified"])
        if classified:
            qn = int(result["qn"])
            counts[qn] += 1
        else:
            unmatched_count += 1

    total_si = len(details)

    return {
        "total_si": total_si,
        "qn_counts": counts,
        "unmatched_count": unmatched_count,
        "details": details,
    }


def print_summary(
    result: Dict[str, object],
    structure_path: Path,
) -> None:
    """Qn 分布と非該当数を標準出力へ表示する。

    Args:
        result: ``analyze_qn()`` の戻り値。
        structure_path: 解析に使用した構造ファイル。
    """
    total_si = int(result["total_si"])
    counts = result["qn_counts"]
    unmatched_count = int(result["unmatched_count"])

    if not isinstance(counts, Counter):
        raise TypeError("qn_counts の型が不正です。")

    print(f"{CENTER_ELEMENT} Qn analysis")
    print(f"POSCAR: {structure_path}")
    print(
        f"{CENTER_ELEMENT}-{FIRST_NEIGHBOR_ELEMENT} range: "
        f"{CENTER_FIRST_MIN:.6f} - {CENTER_FIRST_MAX:.6f} Å"
    )
    print(
        f"{FIRST_NEIGHBOR_ELEMENT}-{SECOND_NEIGHBOR_ELEMENT} range: "
        f"{FIRST_SECOND_MIN:.6f} - {FIRST_SECOND_MAX:.6f} Å"
    )
    print()
    print(f"Total {CENTER_ELEMENT}: {total_si}")
    print()
    print("Qn    Count    Ratio")

    qn_values: Set[int] = set(DISPLAY_QN)
    qn_values.update(counts.keys())

    for qn in sorted(qn_values, reverse=True):
        count = int(counts.get(qn, 0))

        ratio = 0.0
        if total_si > 0:
            ratio = 100.0 * count / total_si

        print(f"Q{qn:<3d} {count:8d} {ratio:10.4f} %")

    unmatched_ratio = 0.0
    if total_si > 0:
        unmatched_ratio = 100.0 * unmatched_count / total_si

    print(
        f"Other {unmatched_count:7d} "
        f"{unmatched_ratio:10.4f} %"
    )

    classified_count = total_si - unmatched_count
    classified_ratio = 0.0
    if total_si > 0:
        classified_ratio = 100.0 * classified_count / total_si

    print()
    print(
        f"Classified: {classified_count} "
        f"({classified_ratio:.4f} %)"
    )
    print(
        f"Unmatched:  {unmatched_count} "
        f"({unmatched_ratio:.4f} %)"
    )


def print_unmatched_details(result: Dict[str, object]) -> None:
    """Qn 非該当 Si の詳細を標準出力へ表示する。

    Args:
        result: ``analyze_qn()`` の戻り値。
    """
    details = result["details"]

    if not isinstance(details, list):
        raise TypeError("details の型が不正です。")

    unmatched: List[Dict[str, object]] = []

    for item in details:
        classified = bool(item["classified"])
        if not classified:
            unmatched.append(item)

    if not unmatched:
        return

    print()
    print(f"Unmatched {CENTER_ELEMENT} details")
    print(
        "VASP index    First O    Bridging O    "
        "Non-bridging O    Reason"
    )

    for item in unmatched:
        vasp_index = int(item["si_index"]) + 1
        first_count = int(item["first_oxygen_count"])
        bridging_count = int(item["bridging_oxygen_count"])
        non_bridging_count = int(item["non_bridging_oxygen_count"])
        reason = str(item["reason"])

        print(
            f"{vasp_index:10d} "
            f"{first_count:10d} "
            f"{bridging_count:13d} "
            f"{non_bridging_count:17d} "
            f"{reason}"
        )


def main() -> None:
    """構造ファイルを決定し、SiO2 の Qn 分布を表示する。"""
    check_distance_range(
        CENTER_FIRST_MIN,
        CENTER_FIRST_MAX,
        "CENTER_FIRST",
    )
    check_distance_range(
        FIRST_SECOND_MIN,
        FIRST_SECOND_MAX,
        "FIRST_SECOND",
    )

    argument_path: Optional[str] = None
    if len(sys.argv) >= 2:
        argument_path = sys.argv[1]

    structure_path = find_structure_file(argument_path)

    structure = Structure.from_file(
        str(structure_path)
    )
    check_sio2_structure(structure)

    result = analyze_qn(structure)

    print()
    print_summary(
        result=result,
        structure_path=structure_path,
    )
    if DISPLAY_UNMATCHED_DETAILS:
        print_unmatched_details(result)


if __name__ == "__main__":
    main()
