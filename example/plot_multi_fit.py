#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotFit


def read_sq_from_fit(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list, list], bool]:
    """
    dir_name に一時的に移動し、cfg_name.fit から
    Q, S_calc, S_exp を読み取る。
    単体版 plot_sq.py と同じロジック。
    """
    original_cwd: str = os.getcwd()
    try:
        try:
            os.chdir(dir_name)
        except FileNotFoundError:
            return False
        fit = RmcPotFit(cfg_name)
        ret = fit.read_fit()
        if not ret:
            return False

        Q = fit.Q
        S_calc = fit.get_S_calc()
        S_exp = fit.get_S_exp()
        return Q, S_calc, S_exp
    finally:
        os.chdir(original_cwd)


def plot_multi_fit(
    dir_list: List[str],
    cfg_name: str,
    ncols: int = 4,
) -> None:
    """
    dir_list に列挙されたフォルダごとに <cfg_name>.fit を読み込み、
    S(Q) を多段サブプロットで表示する。
    """

    all_data: List[Tuple[str, list, list, list]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")
    xmin: float = float("inf")
    xmax: float = float("-inf")

    # 全データを読み込み、軸レンジを決める
    for d in dir_list:
        result = read_sq_from_fit(d, cfg_name)
        if result is False:
            break

        Q, S_calc, S_exp = result
        all_data.append((d, Q, S_calc, S_exp))

        if len(Q) > 0:
            xmin = min(xmin, min(Q))
            xmax = max(xmax, max(Q))
        if len(S_calc) > 0:
            ymin = min(ymin, min(S_calc))
            ymax = max(ymax, max(S_calc))
        if len(S_exp) > 0:
            ymin = min(ymin, min(S_exp), ymin)
            ymax = max(ymax, max(S_exp), ymax)

    if xmin == float("inf"):
        print("有効な FIT データがありません。")
        return

    n: int = len(dir_list)
    nrows: int = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(4 * ncols, 3 * nrows),
        sharex=True,
        sharey=True,
    )

    axes = axes.flatten()

    for ax, (d, Q, S_calc, S_exp) in zip(axes, all_data):
        ax.plot(Q, S_calc, label="S_calc")
        ax.plot(Q, S_exp, label="S_exp")
        ax.set_title(d)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.grid(True)
        ax.legend(fontsize=6)

    # 余った subplot を消す
    for ax in axes[len(all_data) :]:
        ax.axis("off")

    # 軸ラベル
    for ax in axes[-ncols:]:
        ax.set_xlabel("Q")
    axes[0].set_ylabel("S(Q)")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_fit.png", dpi=300)
    print("Saved: plot_multi_fit.png")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage:  plot_multi_fit.py <cfg_name>")
        print("例:     plot_multi_fit.py aaa")
        sys.exit(1)

    cfg_name_: str = sys.argv[1]

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

    plot_multi_fit(dir_list_, cfg_name_, ncols=4)
