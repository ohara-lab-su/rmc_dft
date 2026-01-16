#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
未完:
読み込んだファイルが全て正しければ、きちんと動作するが
エラーや計算途中のファイルがあるとちょっとまだ意図しない動作をする

"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os

import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst, VaspOutcar
from x_logger import XLogger


def read_chi2_from_dir(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list], bool]:
    """あるディレクトリのあるファイルの chi を読んで返す"""
    hst_name: str = os.path.join(dir_name, f"{cfg_name}.hst")

    try:
        reader = RmcPotHst(hst_name=hst_name)
        result = reader.read_chi2()
    except (RuntimeError, FileNotFoundError):
        return False

    if not reader:
        # HST が無い / 読めない場合は False を返して呼び元で処理
        return False

    if not result:
        return False

    steps, chi2 = result
    return steps, chi2


def read_energy_from_dir(
    dir_name: str,
) -> Union[np.ndarray, bool]:
    """あるディレクトリのあるファイルの energy を読んで返す"""
    outcar_path: str = os.path.join(dir_name, "OUTCAR")
    try:
        out = VaspOutcar(outcar_path)
    except (RuntimeError, FileNotFoundError):
        return False
    energies: np.ndarray = out.get_energy_flat()
    return energies


def hide_yticklabels_except_first(axes_row):
    for j, ax in enumerate(axes_row):
        if j != 0:
            ax.set_yticklabels([])


def plot_multi_converge(
    dir_list: List[str],
    cfg_name: str,
    logger: Optional[XLogger] = None,
) -> None:
    logger = logger or XLogger()

    # -------------------- データ読み取り --------------------
    hst_data = []
    en_data = []

    hst_ymin = float("inf")
    hst_ymax = float("-inf")

    en_ymin = float("inf")
    en_ymax = float("-inf")

    for d in dir_list:
        # HST
        h = read_chi2_from_dir(d, cfg_name)
        if h is False:
            # continue
            # ここで以降のディレクトリも存在しない前提で止める
            break

        steps, chi2 = h
        hst_data.append((d, steps, chi2))
        if len(chi2) > 0:
            hst_ymin = min(hst_ymin, min(chi2))
            hst_ymax = max(hst_ymax, max(chi2))

        # Energy
        e = read_energy_from_dir(d)
        if e is False:
            # continue
            # エネルギーも読めなくなったら打ち切り
            break

        energies = e
        en_data.append((d, energies))

        if energies.size > 0:
            en_ymin = min(en_ymin, float(np.min(energies)))
            en_ymax = max(en_ymax, float(np.max(energies)))

    # 1つもデータが無ければ何もしない
    if len(hst_data) == 0 or len(en_data) == 0:
        logger.error("有効なデータが見つかりませんでした。")
        return

    # 両方揃っている列数だけを使う
    n = min(len(hst_data), len(en_data))
    hst_data = hst_data[:n]
    en_data = en_data[:n]
    # n = len(dir_list)

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
        rect=(0.05, 0.03, 1.0, 0.96),
    )

    plt.show()

    # -------------------- PNG 保存 --------------------
    fig.savefig("plot_multi_converge.png", dpi=300)
    print("Saved: plot_multi_converge.png")


if __name__ == "__main__":
    import sys

    logger_ = XLogger(log_level="debug", logger_name="rmc_run")

    if len(sys.argv) != 2:
        print("Usage:")
        print("  plot_multi_converge.py <cfg_name_prefix>")
        sys.exit(1)

    cfg_name_ = sys.argv[1]

    dir_list_ = [
        "log00",
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

    plot_multi_converge(dir_list_, cfg_name_, logger_)
