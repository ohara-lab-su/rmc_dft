#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""VASP 構造から Qn 分布の個数と比率を表示する。

Qn network の判定条件は、このファイル前方の ``QN_CONFIG`` にまとめている。
外部 JSON 設定ファイルは使用しない。
CSV、TOP、FNC などのファイルは生成せず、解析結果だけを標準出力する。
"""

from pathlib import Path

from rmc_dft import RmcPot, RmcPotLog

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

# Qn解析に必要な設定だけをまとめる。
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
QN_CONFIG = {
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

    atom_types = QnNetworkAnalysis.get_structure_atom_types(QN_CONFIG)
    structure = VaspStructure.read_poscar(
        str(poscar_path),
        atom_types,
    )
    analysis = QnNetworkAnalysis(
        structure=structure,
        config=QN_CONFIG,
    )

    qn_counts = analysis.get_qn_counts()
    total_count = sum(qn_counts.values())

    print("Qn distribution")
    print("VASP structure:", poscar_path)
    print("Qn config: embedded QN_CONFIG")
    print("Total central atoms:", total_count)

    if total_count == 0:
        print("Qn network was not found.")
        return

    max_qn = max(qn_counts.keys())

    print()
    print("Qn    Count    Ratio")
    for qn in range(max_qn + 1):
        count = qn_counts.get(qn, 0)
        ratio = count / total_count
        print("Q%-2d %8d %9.4f %%" % (qn, count, ratio * 100.0))


if __name__ == "__main__":
    main()
