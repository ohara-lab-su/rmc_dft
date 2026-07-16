#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VASP 構造から Qn 分布の個数と比率を表示する実行例。

Qn network の判定条件は ``qn_config.json`` から読み込む。
CSV、TOP、FNC などのファイルは生成せず、解析結果だけを標準出力する。
"""

from rmc_dft.rmc_pot.qn import QnNetworkBuilder


POSCAR_NAME = "aaa.vasp"
CONFIG_NAME = "qn_config.json"


def main() -> None:
    """VASP 構造を解析し、Qn ごとの個数と比率を表示する。"""
    builder = QnNetworkBuilder.from_poscar(
        poscar_name=POSCAR_NAME,
        config_name=CONFIG_NAME,
    )

    qn_counts = builder.get_qn_counts()
    total_count = sum(qn_counts.values())

    print("Qn distribution")
    print("VASP structure:", POSCAR_NAME)
    print("Qn config:", CONFIG_NAME)
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
