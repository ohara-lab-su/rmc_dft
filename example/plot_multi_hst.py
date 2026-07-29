#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_multi_hst.py
K.NAKADA, kengo.nakada@gmail.com

RMC_POT の .hst を複数ログ（logX_rmc）から読み取り、
chi2 の推移を横一列のサブプロットとして描画

"""

from typing import List, Tuple, Union
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst

import make_log_dirname


def read_chi2_from_dir(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list], bool]:
    """指定ディレクトリ内の <cfg_name>.hst から (steps, chi2) を読み取ります。

    Args:
        dir_name (str):
            .hst を含むディレクトリ（パス）。
        cfg_name (str):
            cfg 名（拡張子なし）。

    Returns:
        Union[Tuple[list, list], bool]:
            読めた場合は (steps, chi2)、読めない場合は False。
    """

    hst_name: str = os.path.join(dir_name, f"{cfg_name}.hst")

    try:
        reader = RmcPotHst(hst_name=hst_name)
        result = reader.read_chi2()
    except (RuntimeError, FileNotFoundError):
        return False

    if not reader:
        return False

    if not result:
        return False

    steps, chi2 = result
    return steps, chi2


def plot_multi_chi(
    dir_list: List[str],
    cfg_name: str,
) -> None:
    """複数ディレクトリの chi2 を横一列で描画します。

    Args:
        dir_list (List[str]):
            .hst を含むディレクトリ（パス）の列。
        cfg_name (str):
            cfg 名（拡張子なし）。

    Returns:
        None
    """

    all_data: List[Tuple[str, list, list]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")

    for d in dir_list:
        result = read_chi2_from_dir(d, cfg_name)
        if result is False:
            continue

        steps, chi2 = result
        all_data.append((d, steps, chi2))

        if len(chi2) == 0:
            continue

        ymin = min(ymin, min(chi2))
        ymax = max(ymax, max(chi2))

    if ymin == float("inf"):
        print("有効なデータがありません。")
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

    for ax, (d, steps, chi2) in zip(axes, all_data):
        ax.plot(steps, chi2)
        ax.set_title(os.path.basename(d))
        ax.set_xlabel("Step")
        ax.set_ylim(ymin, ymax)
        ax.grid(True)

    axes[0].set_ylabel("Chi^2 (total/data_point)")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_hst.png", dpi=300)
    print("Saved: plot_multi_hst.png")


if __name__ == "__main__":

    # -------------------- 設定 --------------------
    cfg_name_: str = "aaa"
    base_dir_: str = "."

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

    plot_multi_chi(dir_list_paths_, cfg_name_)
