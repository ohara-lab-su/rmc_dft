#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotFit


def plot_sq(
    cfg_or_fit: str,
    target_dir: Optional[str] = None,
) -> None:
    """
    RmcPotFit を用いて S(Q) をプロットする。

    Args:
        cfg_or_fit (str): RmcPotFit に渡す文字列
        target_dir (str): フォルダ名（None の場合はカレントディレクトリ）
    """

    # フォルダ指定がある場合は一時的に移動
    original_cwd: str = os.getcwd()
    try:
        if target_dir is not None:
            os.chdir(target_dir)

        fit = RmcPotFit(cfg_or_fit)

        Q = fit.Q
        S_calc = fit.get_S_calc()
        S_exp = fit.get_S_exp()

        plt.figure()
        plt.plot(Q, S_calc, label="S_calc")
        plt.plot(Q, S_exp, label="S_exp")
        plt.xlabel("Q")
        plt.ylabel("S(Q)")
        plt.legend()
        plt.tight_layout()
        plt.show()
    finally:
        # 元のディレクトリに戻す
        os.chdir(original_cwd)


if __name__ == "__main__":
    import sys

    # 使い方:
    #   1) カレントフォルダで cfg 指定
    #        python plot_fit.py aaa
    #
    #   2) フォルダを指定して、そのフォルダ内で cfg 指定
    #        python plot_fit.py /path/to/dir aaa
    #
    #      上記どちらでも RmcPotFit への引数（cfg_or_fit）は同じ意味で渡される。

    #    if len(sys.argv) != 2:
    #        print("Usage: python plot_sq.py <cfg_name>")
    #        sys.exit(1)
    #
    #    _fitfile = sys.argv[1]
    #    plot_sq(_fitfile)

    if len(sys.argv) == 2:
        # カレントフォルダで cfg_or_fit を指定
        cfg_or_fit_arg: str = sys.argv[1]
        plot_sq(cfg_or_fit_arg, target_dir=None)

    elif len(sys.argv) == 3:
        # 第1引数でフォルダ、第2引数で cfg_or_fit
        dir_arg: str = sys.argv[1]
        cfg_or_fit_arg: str = sys.argv[2]
        plot_sq(cfg_or_fit_arg, target_dir=dir_arg)

    else:
        print("Usage:")
        print("  python plot_fit.py <cfg_or_fit>")
        print("  python plot_fit.py <dir> <cfg_or_fit>")
        sys.exit(1)
