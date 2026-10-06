#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""VASP 構造から Qn 分布の個数と比率を表示する。

Qn network の判定条件は、既定では RMC_POT 自由形式 ``*.dat`` の
``[ SNC ]`` から取得する。手動設定へコメントアウト・コメントインで切替できる。

外部 JSON 設定ファイルは使用しない。
CSV、TOP、FNC などのファイルは生成せず、解析結果だけを標準出力する。
"""

from pathlib import Path

from rmc_dft import RmcPot, RmcPotLog
from rmc_dft.rmc_pot.rmc_pot_dat import RmcPotDat
from rmc_dft.rmc_pot.rmc_pot_snc import RmcPotSnc

# from rmc_dft.rmc_pot.qn.qn_network_analysis import QnNetworkAnalysis
# from rmc_dft.rmc_pot.qn.vasp_structure import VaspStructure

from qn.qn_network_analysis import QnNetworkAnalysis
from qn.vasp_structure import VaspStructure

from x_logger import XLogger

# =============================================================================
# ユーザー設定
# =============================================================================

# 解析するVASP構造ファイル。
#
# 次の順番で存在を確認する。
#
#     1. POSCAR
#     2. POSCAR.vasp
#     3. aaa.vasp
#     4. aaa.cfg
#
# aaa.cfgだけが存在する場合は、RmcPot.cfg2poscar()を直接使用して
# aaa.vaspへ変換してから解析する。
CONTCAR_PATH = Path("CONTCAR")
POSCAR_PATH = Path("POSCAR")

FALLBACK_POSCAR_PATHS = [
    Path("POSCAR.vasp"),
    Path("aaa.vasp"),
]
CFG_PATH = Path("aaa.cfg")

# aaa.cfgをaaa.vaspへ変換するときに使用する元素順。
ELEMENT_INFO = [
    "Si",
    "O",
]

# RMC_POT の入力・出力ファイル。
DAT_PATH = Path("aaa.dat")
SNC_PATH = Path("aaa.snc")

# Qn解析に必要な設定だけをまとめる。
#
# DAT_PATH の [ SNC ] を使用せず、手動設定で解析する場合に使用する。
# main() 内の切替箇所でコメントアウト・コメントインして選択する。
#
# first_mode:
#     "cutoff"
#         first_min～first_max 内の第一近接原子をすべて使用する。
#         Q5以上を含めて数える場合はこちらを使用する。
#
#     "nearest"
#         first_min～first_max 内から近い順に first_nearest_n 個だけ使用する。
#         first_nearest_n=4 の場合、Q5以上は出ない。
#
# second_use_first_network:
#     False
#         第一近接と第二近接を、それぞれ独立した距離範囲で判定する。
#         RMC_POTのSNCと同じ二段階の距離判定に対応する。
#
#     True
#         第一近接networkの逆接続を第二近接判定へ再利用する。
MANUAL_QN_CONFIG = {
    "structure": {
        # POSCARに元素名行がない場合に使用する元素順。
        "atom_types": [
            "Si",
            "O",
        ],
    },
    "network": {
        # Qnを求める中心元素。
        "central_types": [
            "Si",
        ],
        # 中心元素と第二近接元素の間をつなぐ第一近接元素。
        "bridge_types": [
            "O",
        ],
        # bridgeを介して接続する第二近接元素。
        "second_types": [
            "Si",
        ],
        # 中心元素－bridge元素の距離範囲 [Å]。
        "first_min": 1.2,
        "first_max": 1.9,
        # Q5以上も数えるため、距離範囲内のbridgeをすべて使用する。
        "first_mode": "cutoff",
        # first_mode="nearest" の場合だけ使用する。
        "first_nearest_n": 4,
        # bridge元素－第二近接元素の距離範囲 [Å]。
        "second_min": 1.2,
        "second_max": 1.9,
        # RMC_POT SNCと同様に、第二近接を独立した距離範囲で判定する。
        "second_use_first_network": False,
    },
}


def load_qn_config_from_dat(dat_path: Path) -> dict:
    """自由形式 ``*.dat`` の SNC から Qn 解析設定を作る。

    ``RmcPotDatFree.get_qn_constraints()`` を使用し、DAT の再解析は行わない。
    Q3、Q4、Q5など複数の SNC が同じ network 定義を共有していることを
    確認し、その共通部分を QnNetworkAnalysis の設定へ変換する。

    Args:
        dat_path: 解析する自由形式 ``*.dat`` ファイル。

    Returns:
        QnNetworkAnalysis に渡す設定辞書。

    Raises:
        ValueError: SNC が無い場合、SNC 間で network 定義が異なる場合、
            または第二近接原子ごとの距離範囲が異なる場合。
    """
    dat = RmcPotDat(
        cfg_name=str(dat_path.with_suffix("")),
        auto_write=False,
    )
    constraints = dat.get_qn_constraints()
    if not constraints:
        raise ValueError(f"{dat_path} に [ SNC ] がありません。")

    chemical_symbols_value = dat.get(
        "GENERAL",
        "CHEMICAL-SYMBOLS",
        default=None,
    )
    if chemical_symbols_value is None:
        raise ValueError(f"{dat_path} に CHEMICAL-SYMBOLS がありません。")
    chemical_symbols = chemical_symbols_value.split()

    reference = constraints[0]
    reference_signature = (
        reference["central_type"],
        reference["first_neighbor_type"],
        reference["first_neighbor_range"],
        tuple(
            (
                second["atom_type"],
                second["minimum"],
                second["maximum"],
            )
            for second in reference["second_neighbors"]
        ),
    )

    for index, constraint in enumerate(constraints[1:], start=1):
        signature = (
            constraint["central_type"],
            constraint["first_neighbor_type"],
            constraint["first_neighbor_range"],
            tuple(
                (
                    second["atom_type"],
                    second["minimum"],
                    second["maximum"],
                )
                for second in constraint["second_neighbors"]
            ),
        )
        if signature != reference_signature:
            raise ValueError(
                "[ SNC ] ごとに Qn network 定義が異なります: " f"index=0, index={index}"
            )

    second_ranges = {
        (second["minimum"], second["maximum"])
        for second in reference["second_neighbors"]
    }
    if len(second_ranges) != 1:
        raise ValueError(
            "QnNetworkAnalysis は第二近接元素ごとに異なる距離範囲を" "受け取れません。"
        )

    central_type = reference["central_type"]
    first_neighbor_type = reference["first_neighbor_type"]
    second_neighbor_types = [
        second["atom_type"] for second in reference["second_neighbors"]
    ]

    used_types = [central_type, first_neighbor_type] + second_neighbor_types
    for atom_type in used_types:
        if atom_type < 1 or atom_type > len(chemical_symbols):
            raise ValueError(
                "SNC の原子タイプ番号が CHEMICAL-SYMBOLS の範囲外です: "
                f"atom_type={atom_type}"
            )

    second_minimum, second_maximum = next(iter(second_ranges))
    first_minimum, first_maximum = reference["first_neighbor_range"]

    return {
        "structure": {
            "atom_types": chemical_symbols,
        },
        "network": {
            "central_types": [chemical_symbols[central_type - 1]],
            "bridge_types": [chemical_symbols[first_neighbor_type - 1]],
            "second_types": [
                chemical_symbols[atom_type - 1] for atom_type in second_neighbor_types
            ],
            "first_min": first_minimum,
            "first_max": first_maximum,
            "first_mode": "cutoff",
            "first_nearest_n": 4,
            "second_min": second_minimum,
            "second_max": second_maximum,
            "second_use_first_network": False,
        },
    }


def convert_cfg_to_poscar() -> Path:
    """aaa.cfgをaaa.vaspへ変換する。

    ``conv_cfg2poscar.py aaa Si,O`` と同じ処理を、このスクリプト内で
    直接実行する。

    Returns:
        生成されたaaa.vaspのパス。

    Raises:
        RuntimeError:
            RmcPot.cfg2poscar()の実行後もaaa.vaspが生成されなかった場合。
    """
    cfg_name = CFG_PATH.stem

    logger = XLogger(
        log_level="debug",
        logger_name="analyze_sio2_qn",
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
        element_info=ELEMENT_INFO,
    )

    generated_poscar_path = Path("%s.vasp" % cfg_name)

    if not generated_poscar_path.is_file():
        raise RuntimeError(
            "%s の変換後に %s が生成されませんでした。"
            % (
                CFG_PATH,
                generated_poscar_path,
            )
        )

    return generated_poscar_path


def resolve_poscar_path() -> Path:
    """解析対象のVASP構造ファイルを決定する。

    次の順番で存在を確認する。

        1. POSCAR
        2. POSCAR.vasp
        3. aaa.vasp
        4. aaa.cfg

    aaa.cfgだけが存在する場合は、aaa.vaspへ変換してそのファイルを返す。

    Returns:
        解析対象となるVASP構造ファイルのパス。

    Raises:
        FileNotFoundError:
            解析可能な入力ファイルが存在しない場合。
    """
    if CONTCAR_PATH.is_file():
        return CONTCAR_PATH

    if POSCAR_PATH.is_file():
        return POSCAR_PATH

    for fallback_poscar_path in FALLBACK_POSCAR_PATHS:
        if fallback_poscar_path.is_file():
            return fallback_poscar_path

    if CFG_PATH.is_file():
        return convert_cfg_to_poscar()

    raise FileNotFoundError(
        "POSCAR, POSCAR.vasp, aaa.vasp, aaa.cfg のいずれも見つかりません。"
    )


def main() -> None:
    """VASP 構造を解析し、Qnごとの個数と比率を表示する。"""
    poscar_path = resolve_poscar_path()

    ###################################
    # DAT の [ SNC ] を使う場合。
    qn_config = load_qn_config_from_dat(DAT_PATH)
    # 手動設定を使う場合は、上の1行をコメントアウトし、次の1行を有効にする。
    # qn_config = MANUAL_QN_CONFIG
    ###################################

    atom_types = QnNetworkAnalysis.get_structure_atom_types(qn_config)
    structure = VaspStructure.read_poscar(
        str(poscar_path),
        atom_types,
    )
    analysis = QnNetworkAnalysis(
        structure=structure,
        config=qn_config,
    )

    qn_counts = analysis.get_qn_counts()
    total_count = sum(qn_counts.values())

    print("Qn distribution")
    print("VASP structure:", poscar_path)
    if qn_config is MANUAL_QN_CONFIG:
        print("Qn config: MANUAL_QN_CONFIG")
    else:
        print("Qn config:", DAT_PATH, "[ SNC ]")
    print("Total central atoms:", total_count)

    snc_qn_counts = None
    if SNC_PATH.is_file():
        snc = RmcPotSnc(str(SNC_PATH))
        snc_qn_counts = snc.get_common_qn_counts()
        print("RMC_POT SNC output:", SNC_PATH)

    if total_count == 0:
        print("Qn network was not found.")
        return

    max_qn = max(qn_counts.keys())

    if snc_qn_counts:
        max_qn = max(max_qn, max(snc_qn_counts.keys()))

    print()
    if snc_qn_counts is None:
        print("Qn    Count    Ratio")
    else:
        print("Qn    Analyzer    RMC_POT.snc    Difference    Ratio")

    for qn in range(max_qn + 1):
        count = qn_counts.get(qn, 0)
        ratio = count / total_count
        if snc_qn_counts is None:
            print("Q%-2d %8d %9.4f %%" % (qn, count, ratio * 100.0))
        else:
            snc_count = snc_qn_counts.get(qn, 0)
            difference = count - snc_count
            print(
                "Q%-2d %10d %14d %13d %9.4f %%"
                % (qn, count, snc_count, difference, ratio * 100.0)
            )


if __name__ == "__main__":
    main()
