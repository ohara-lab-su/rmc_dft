#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import VaspOutcar


def read_energy_from_dir(dir_name: str) -> np.ndarray:
    """
    指定フォルダ dir_name 内の OUTCAR から
    flatten energy sequence（全 SCF のエネルギー列）を返す。
    """
    outcar_path: str = os.path.join(dir_name, "OUTCAR")
    out = VaspOutcar(outcar_path)
    energies: np.ndarray = out.get_energy_flat()  # shape = (N,)
    return energies


def plot_multi_energy(dir_list: List[str]) -> None:
    """
    dir_list に列挙されたフォルダごとに OUTCAR を読み込み、
    flatten energy を横一列のサブプロットにして表示する。
    縦軸は全てのサブプロットで共有。
    """
    all_data: List[Tuple[str, np.ndarray]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")

    # まず全データを読み込み、縦軸範囲を決定
    for d in dir_list:
        energies = read_energy_from_dir(d)
        all_data.append((d, energies))

        if energies.size == 0:
            continue

        ymin = min(ymin, float(np.min(energies)))
        ymax = max(ymax, float(np.max(energies)))

    if ymin == float("inf"):
        print("有効な OUTCAR エネルギーデータがありません。")
        return

    n: int = len(all_data)
    fig, axes = plt.subplots(
        nrows=1,
        ncols=n,
        figsize=(2.5 * n, 4),
        sharey=True,
    )

    # n=1 の特別処理
    if n == 1:
        axes = [axes]

    for ax, (d, energies) in zip(axes, all_data):
        x = np.arange(energies.size)
        ax.plot(x, energies)
        ax.set_title(d)
        ax.set_xlabel("SCF step")
        ax.set_ylim(ymin, ymax)
        ax.grid(True)

    axes[0].set_ylabel("Energy (without entropy) [eV]")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_energy.png", dpi=300)
    print("Saved: plot_multi_energy.png")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 1:
        print("Usage:")
        print("  plot_multi_energy.py")
        print("フォルダ名はスクリプトの下部で手動編集します。")
        sys.exit(1)

    # ここでフォルダ名を手で並べる（plot_multi_hst と同じ方式）
    dir_list: List[str] = [
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

    plot_multi_energy(dir_list)
