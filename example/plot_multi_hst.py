#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst


def read_chi2_from_dir(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list], bool]:
    """
    指定フォルダ dir_name 内の <cfg_name>.hst から (steps, chi2) を読み取る
    """
    hst_name: str = os.path.join(dir_name, f"{cfg_name}.hst")
    # reader = RmcPotHst(hst_path)
    # steps, chi2 = reader.read_chi2()
    try:
        reader = RmcPotHst(hst_name=hst_name)
        result = reader.read_chi2()
    except (RuntimeError, FileNotFoundError):
        return False

    if not reader:
        # HST が無い / 読めない場合は False を返して呼び元で処理
        return False

    steps, chi2 = result
    return steps, chi2


def plot_multi_chi(
    dir_list: List[str],
    cfg_name: str,
) -> None:
    """
    dir_list に列挙されたフォルダごとに <cfg_name>.hst を読み込み、
    一枚の図の中に横一列で並べてプロットする。
    縦軸スケールは全サブプロットで共通とする。
    """

    all_data: List[Tuple[str, list, list]] = []
    ymin: float = float("inf")
    ymax: float = float("-inf")

    # まず全フォルダからデータを読み込んで、縦軸レンジを決める
    for d in dir_list:
        steps, chi2 = read_chi2_from_dir(d, cfg_name)
        all_data.append((d, steps, chi2))
        if len(chi2) == 0:
            continue
        ymin = min(ymin, min(chi2))
        ymax = max(ymax, max(chi2))

    if ymin == float("inf"):
        print("有効なデータがありません。")
        return

    n: int = len(all_data)
    # 横一列に並べる
    fig, axes = plt.subplots(
        nrows=1,
        ncols=n,
        figsize=(2.5 * n, 4),
        sharey=True,
    )

    # n=1 の場合の扱い
    if n == 1:
        axes = [axes]

    for ax, (d, steps, chi2) in zip(axes, all_data):
        ax.plot(steps, chi2)
        ax.set_title(d)
        ax.set_xlabel("Step")
        ax.set_ylim(ymin, ymax)
        ax.grid(True)

    # 縦軸ラベルは左端だけ
    axes[0].set_ylabel("Chi^2 (total/data_point)")

    plt.tight_layout()
    plt.show()

    fig.savefig("plot_multi_hst.png", dpi=300)
    print("Saved: plot_multi_hst.png")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage:")
        print("  plot_multi_chi.py <cfg_name_prefix>")
        print("例: plot_multi_chi.py aaa")
        sys.exit(1)

    cfg_name_: str = sys.argv[1]

    # ここでフォルダ名を手で並べる
    dir_list_: List[str] = [
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

    plot_multi_chi(dir_list_, cfg_name_)
