#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_multi_fit.py

RMC_POT の <cfg_name>.fit を複数ログ（logX_rmc）から読み取り、
S(Q) を多段サブプロットで描画

"""

from typing import List, Tuple, Union
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotFit

import make_log_dirname


def read_sq_from_fit(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list, list], bool]:
    """指定ディレクトリの <cfg_name>.fit から Q, S_calc, S_exp を読み取ります。

    Args:
        dir_name (str):
            <cfg_name>.fit を含むディレクトリ（パス）。
        cfg_name (str):
            cfg 名（拡張子なし）。

    Returns:
        Union[Tuple[list, list, list], bool]:
            読めた場合は (Q, S_calc, S_exp)、読めない場合は False。
    """

    original_cwd: str = os.getcwd()
    try:
        try:
            os.chdir(dir_name)
        except FileNotFoundError:
            return False

        fit = RmcPotFit(cfg_name=cfg_name)
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
    """複数ディレクトリの S(Q) を多段サブプロットで描画します。

    Args:
        dir_list (List[str]):
            <cfg_name>.fit を含むディレクトリ（パス）の列。
        cfg_name (str):
            cfg 名（拡張子なし）。
        ncols (int):
            サブプロットの列数。

    Returns:
        None
    """

    all_data: List[Tuple[str, list, list, list]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")
    xmin: float = float("inf")
    xmax: float = float("-inf")

    for d in dir_list:
        result = read_sq_from_fit(d, cfg_name)
        if result is False:
            continue

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

    n: int = len(all_data)
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
        ax.set_title(os.path.basename(d))
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.grid(True)
        ax.legend(fontsize=6)

    for ax in axes[len(all_data) :]:
        ax.axis("off")

    for ax in axes[-ncols:]:
        ax.set_xlabel("Q")

    axes[0].set_ylabel("S(Q)")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_fit.png", dpi=300)
    print("Saved: plot_multi_fit.png")


if __name__ == "__main__":

    # -------------------- 設定 --------------------
    cfg_name_: str = "aaa"
    base_dir_: str = "."
    ncols_: int = 4

    # -------------------- dir_list（手動） --------------------
    # dir_list_names_: List[str] = [
    #     "log0_rmc",
    #     "log1_rmc",
    #     "log2_rmc",
    # ]

    # -------------------- dir_list（自動） --------------------
    dir_list_names_: List[str] = make_log_dirname.find_rmc_dirs(base_dir_)

    dir_list_paths_: List[str] = []
    for name in dir_list_names_:
        dir_list_paths_.append(os.path.join(base_dir_, name))

    plot_multi_fit(dir_list_paths_, cfg_name_, ncols=ncols_)
