#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_multi_energy.py
K.NAKADA, kengo.nakada@gmail.com

VASP OUTCAR を複数ログ（logX_dft）から読み取り、
SCF の flatten energy 列を横一列のサブプロットとして描画

"""
from typing import List, Tuple
import os
import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import VaspOutcar

import make_log_dirname


def read_energy_from_dir(
    dir_name: str,
) -> np.ndarray:
    """指定ディレクトリ内の OUTCAR から flatten energy 列を返します。

    Args:
        dir_name (str):
            OUTCAR を含むディレクトリ（パス）。

    Returns:
        np.ndarray:
            shape=(N,) のエネルギー列。
    """

    outcar_path: str = os.path.join(dir_name, "OUTCAR")
    out = VaspOutcar(outcar_path)
    energies: np.ndarray = out.get_energy_flat()
    return energies


def plot_multi_energy(
    dir_list: List[str],
) -> None:
    """複数ディレクトリの flatten energy を横一列で描画します。

    Args:
        dir_list (List[str]):
            OUTCAR を含むディレクトリ（パス）の列。

    Returns:
        None
    """

    all_data: List[Tuple[str, np.ndarray]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")

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

    if n == 1:
        axes = [axes]

    for ax, (d, energies) in zip(axes, all_data):
        x = np.arange(energies.size)
        ax.plot(x, energies)
        ax.set_title(os.path.basename(d))
        ax.set_xlabel("SCF step")
        ax.set_ylim(ymin, ymax)
        ax.grid(True)

    axes[0].set_ylabel("Energy (without entropy) [eV]")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_energy.png", dpi=300)
    print("Saved: plot_multi_energy.png")


if __name__ == "__main__":

    # -------------------- 設定 --------------------
    base_dir_: str = "."

    # -------------------- dir_list（手動） --------------------
    # dir_list_names_: List[str] = [
    #     "log0_dft",
    #     "log1_dft",
    #     "log2_dft",
    # ]

    # -------------------- dir_list（自動） --------------------
    dir_list_names_: List[str] = make_log_dirname.find_dft_dirs(base_dir_)

    dir_list_paths_: List[str] = []
    for name in dir_list_names_:
        dir_list_paths_.append(os.path.join(base_dir_, name))

    plot_multi_energy(dir_list_paths_)
