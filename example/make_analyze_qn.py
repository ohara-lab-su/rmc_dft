#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

既存の VASP 構造から Qn 分布だけを解析して標準出力する実行例。

構造生成や RMC_POT 用ファイルの作成は行わない。
QnNetworkAnalysis を使って、Q0 から Q4 の個数と割合を画面に表示する。
"""

from typing import Dict

from rmc_dft.rmc_pot.qn.qn_network_analysis import QnNetworkAnalysis


def print_qn_counts(qn_counts: Dict[int, int]) -> None:
    """Q0 から Q4 の個数と割合を標準出力する。

    Args:
        qn_counts: Qn をキー、該当する中心原子数を値とする辞書。
    """
    total_count = sum(qn_counts.values())

    print("Qn analysis")
    print("-----------")
    print("central atom count: %d" % total_count)

    for qn in range(5):
        count = qn_counts.get(qn, 0)
        ratio = 0.0
        if total_count > 0:
            ratio = 100.0 * float(count) / float(total_count)

        print("Q%d: %d (%.2f%%)" % (qn, count, ratio))


def main() -> None:
    """VASP 構造を読み、Qn 分布だけを解析して画面表示する。"""
    poscar_name = "aaa.vasp"
    config_name = "qn_config.json"

    analysis = QnNetworkAnalysis.from_poscar(
        poscar_name=poscar_name,
        config_name=config_name,
    )

    qn_counts = analysis.get_qn_counts()
    print_qn_counts(qn_counts)


if __name__ == "__main__":
    main()
