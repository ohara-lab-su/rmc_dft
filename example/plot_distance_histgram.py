#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

POSCAR から全原子ペアの距離分布（ヒストグラム）を描くスクリプト。

前提:
    - 同じディレクトリに poscar.py, poscar_analyzer.py がある
    - POSCAR ファイルがカレントディレクトリにある
"""

from typing import List

import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import VaspPoscar
from rmc_dft import VaspPoscarAnalyzer


def collect_all_pair_distances(
    analyzer: VaspPoscarAnalyzer,
    pbc: bool = True,
    r_max: float | None = None,
) -> np.ndarray:
    """
    全原子ペア (i < j) の距離を収集する（PBC 対応）。
    """
    poscar = analyzer.poscar
    n_sites: int = poscar.get_num_atoms()
    distances: list[float] = []

    # idx は 0 始まりで正しい（あなたの VaspPoscarAnalyzer がそうなっている）
    for i in range(n_sites):
        for j in range(i + 1, n_sites):
            d_ij = analyzer.get_interatomic_distance(i, j, pbc=pbc)

            if (r_max is None) or (d_ij <= r_max):
                distances.append(d_ij)

    return np.array(distances)


def main() -> None:
    # POSCAR 読み込み
    poscar = VaspPoscar("POSCAR")
    analyzer = VaspPoscarAnalyzer(poscar)

    # 距離を収集
    # r_max は適宜調整（例: 6 Å まで見たい場合など）
    distances = collect_all_pair_distances(analyzer, pbc=True, r_max=None)

    if distances.size == 0:
        print("距離データがありません。")
        return

    # ヒストグラムを描画
    # ビン数は必要に応じて変更
    n_bins = 100

    plt.figure()
    plt.hist(distances, bins=n_bins)
    plt.xlabel("Interatomic distance (Å)")
    plt.ylabel("Counts")
    plt.title("Histogram of interatomic distances (PBC, all pairs)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
