#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

POSCAR または cfg 名(例: aaa) を与えて、
全原子ペア距離ヒストグラムを描く。
cfg の場合は内部で POSCAR に変換して使用する。
"""

from typing import List
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import (
    VaspPoscar,
    VaspPoscarAnalyzer,
    RmcPot,
    RmcPotLog,
)
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


def collect_all_pair_distances(
    analyzer: VaspPoscarAnalyzer,
    pbc: bool = True,
    r_max: float | None = None,
) -> np.ndarray:
    """全原子ペア距離を収集する。"""
    poscar = analyzer.poscar
    n_sites: int = poscar.get_num_atoms()
    distances: list[float] = []

    for i in range(n_sites):
        for j in range(i + 1, n_sites):
            d_ij = analyzer.get_interatomic_distance(i, j, pbc=pbc)
            if (r_max is None) or (d_ij <= r_max):
                distances.append(d_ij)

    return np.array(distances)


def load_poscar_from_input(input_name: str, logger: XLogger) -> str:
    """
    入力名が POSCAR ならそのまま使用。
    入力名が cfg 名(例: aaa) なら、aaa.cfg → POSCAR を生成して返す。
    """
    if input_name == "POSCAR":
        return "POSCAR"

    cfg_path = f"{input_name}.cfg"
    if not os.path.exists(cfg_path):
        logger.error(f"cfg ファイル {cfg_path} が存在しません。")
        sys.exit(1)

    # cfg → POSCAR
    rmc_log = RmcPotLog(cfg_name=input_name, logger=logger)
    rmc = RmcPot(rmc_log=rmc_log, cfg_name=input_name, logger=logger)
    rmc.cfg2poscar(cfg_name=input_name)

    return "POSCAR"


def main() -> None:
    logger = XLogger(log_level="info", logger_name="poscar_hist")

    if len(sys.argv) != 2:
        print("Usage: ./plot_dist.py POSCAR  または  ./plot_dist.py aaa")
        sys.exit(1)

    input_name: str = sys.argv[1]

    # POSCAR または cfg → POSCAR
    poscar_name = load_poscar_from_input(input_name, logger)

    # POSCAR 読み込み
    poscar = VaspPoscar(poscar_name)
    analyzer = VaspPoscarAnalyzer(poscar)

    # 距離収集
    distances = collect_all_pair_distances(analyzer, pbc=True, r_max=None)
    if distances.size == 0:
        print("距離データがありません。")
        sys.exit(0)

    # ヒストグラム描画
    plt.figure()
    plt.hist(distances, bins=100)
    plt.xlabel("Interatomic distance (Å)")
    plt.ylabel("Counts")
    plt.title(f"Histogram of interatomic distances ({input_name})")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
