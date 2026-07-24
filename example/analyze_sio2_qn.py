#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VASP 構造から Qn 分布の個数と比率を表示する。

Qn network の判定条件は、このファイル前方の ``QN_CONFIG`` にまとめている。
外部 JSON 設定ファイルは使用しない。
CSV、TOP、FNC などのファイルは生成せず、解析結果だけを標準出力する。
"""

from rmc_dft.rmc_pot.qn import QnNetworkBuilder
from rmc_dft.rmc_pot.qn.vasp_structure import VaspStructure


# =============================================================================
# ユーザー設定
# =============================================================================

# 解析するVASP構造ファイル。
POSCAR_NAME = "aaa.vasp"

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


def main() -> None:
    """VASP 構造を解析し、Qnごとの個数と比率を表示する。"""
    atom_types = QnNetworkBuilder.get_structure_atom_types(QN_CONFIG)
    structure = VaspStructure.read_poscar(
        POSCAR_NAME,
        atom_types,
    )
    builder = QnNetworkBuilder(
        structure=structure,
        config=QN_CONFIG,
    )

    qn_counts = builder.get_qn_counts()
    total_count = sum(qn_counts.values())

    print("Qn distribution")
    print("VASP structure:", POSCAR_NAME)
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
