#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

POSCAR の全原子ペアについて周期境界条件込みで距離を計算し、
短い順に上位10件を表示する。
"""

from typing import List, Tuple

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspOutcar,
    VaspKpoints,
    VaspOutcar,
    VaspLog,
    VaspPoscar,
    VaspPoscarAnalyzer,
    VaspPotcarBuilder,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


def get_all_distances(
        analyzer: VaspPoscarAnalyzer,
        use_pbc: bool = True,
) -> List[Tuple[float, int, int]]:
    """
    全原子ペアの距離一覧を返す。

    Returns:
        List[(距離, 原子iindex, 原子jindex)]
    """
    num_atoms: int = analyzer.poscar.get_num_atoms()
    dist_list: List[Tuple[float, int, int]] = []

    for i in range(1, num_atoms + 1):
        for j in range(i + 1, num_atoms + 1):
            d: float = float(analyzer.get_interatomic_distance(i, j, pbc=use_pbc))
            dist_list.append((d, i, j))

    return dist_list


def print_top10(
        analyzer: VaspPoscarAnalyzer,
        dist_list: List[Tuple[float, int, int]],
        top_n: int = 10,
) -> None:
    """
    距離の短い順に上位 N 個を表示する。
    """
    dist_list_sorted = sorted(dist_list, key=lambda x: x[0])

    print(f"=== Shortest {top_n} distances (PBC) ===")
    for rank, (d, i, j) in enumerate(dist_list_sorted[:top_n], start=1):
        elem_i = analyzer.poscar.get_element_by_global_index(i)
        elem_j = analyzer.poscar.get_element_by_global_index(j)
        print(
            f"{rank:2d}: {elem_i:>2s}({i:4d}) - " f"{elem_j:>2s}({j:4d}) : {d:8.4f} Å"
        )


def main() -> None:
    # POSCAR 読み込み
    poscar = VaspPoscar("POSCAR", verbose=False)
    analyzer = VaspPoscarAnalyzer(poscar)

    # 全ペア距離を取得
    dist_list = get_all_distances(analyzer, use_pbc=True)

    # 上位10件を表示
    print_top10(analyzer, dist_list, top_n=10)


if __name__ == "__main__":
    main()
