#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os

import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst, VaspOutcar


def read_chi2_from_dir(dir_name: str, cfg_name: str) -> Tuple[list, list]:
    hst_path: str = os.path.join(dir_name, f"{cfg_name}.hst")
    reader = RmcPotHst(hst_path)
    steps, chi2 = reader.read_chi2()
    return steps, chi2


def read_energy_from_dir(dir_name: str) -> np.ndarray:
    outcar_path: str = os.path.join(dir_name, "OUTCAR")
    out = VaspOutcar(outcar_path)
    energies: np.ndarray = out.get_energy_flat()
    return energies


def hide_yticklabels_except_first(axes_row):
    for j, ax in enumerate(axes_row):
        if j != 0:
            ax.set_yticklabels([])


def plot_multi_converge(dir_list: List[str], cfg_name: str) -> None:

    # -------------------- データ読み取り --------------------
    hst_data = []
    en_data = []

    hst_ymin = float("inf")
    hst_ymax = float("-inf")

    en_ymin = float("inf")
    en_ymax = float("-inf")

    for d in dir_list:
        # HST
        steps, chi2 = read_chi2_from_dir(d, cfg_name)
        hst_data.append((d, steps, chi2))
        if len(chi2) > 0:
            hst_ymin = min(hst_ymin, min(chi2))
            hst_ymax = max(hst_ymax, max(chi2))

        # Energy
        energies = read_energy_from_dir(d)
        en_data.append((d, energies))
        if energies.size > 0:
            en_ymin = min(en_ymin, float(np.min(energies)))
            en_ymax = max(en_ymax, float(np.max(energies)))

    n = len(dir_list)

    # -------------------- Figure 準備 --------------------
    fig, axes = plt.subplots(
        nrows=2,
        ncols=n,
        figsize=(2.7 * n, 8),  # 横幅をわずかに拡大
    )

    if n == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    # -------------------- 上段（RMC） --------------------
    for col, (d, steps, chi2) in enumerate(hst_data):
        ax = axes[0, col]
        ax.plot(steps, chi2)
        ax.set_title(d)
        if hst_ymin != float("inf"):
            ax.set_ylim(hst_ymin, hst_ymax)
        ax.set_xlabel("Step")
        ax.grid(True)

    axes[0, 0].set_ylabel("Chi^2")
    hide_yticklabels_except_first(axes[0])

    # -------------------- 下段（DFT Energy） --------------------
    for col, (d, energies) in enumerate(en_data):
        ax = axes[1, col]
        x = np.arange(energies.size, dtype=int)
        ax.plot(x, energies)
        if en_ymin != float("inf"):
            ax.set_ylim(en_ymin, en_ymax)
        ax.set_xlabel("SCF step")
        ax.grid(True)

    axes[1, 0].set_ylabel("Energy [eV]")
    hide_yticklabels_except_first(axes[1])

    # -------------------- 全体タイトル --------------------
    fig.suptitle("RMC (top)  /  DFT (bottom)", fontsize=16, y=0.98)

    # -------------------- 余白調整（左側を広げる） --------------------
    # left=0.11 で左側だけ大きな余白を固定し、tight_layout と両立
    # plt.tight_layout(rect=[0.11, 0.03, 1.0, 0.96],)
    plt.tight_layout(
        rect=[0.05, 0.03, 1.0, 0.96],
    )

    plt.show()

    # -------------------- PNG 保存 --------------------
    fig.savefig("plot_multi_converge.png", dpi=300)
    print("Saved: plot_multi_converge.png")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage:")
        print("  plot_multi_converge.py <cfg_name_prefix>")
        sys.exit(1)

    cfg_name_arg = sys.argv[1]

    _dir_list = [
        "log01",
        "log02",
        "log03",
        "log04",
        "log05",
        "log06",
        "log07",
        "log08",
        "log09",
        "log10",
        "log11",
        "log12",
        "log13",
        "log14",
        "log15",
        "log16",
        "log17",
        "log18",
        "log19",
    ]

    plot_multi_converge(_dir_list, cfg_name_arg)
