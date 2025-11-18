#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import matplotlib.pyplot as plt

from rmc_dft import RmcPotPpcf


def plot_ppcf(
    cfg_or_ppcf: str,
    target_dir: Optional[str] = None,
) -> None:

    # フォルダ指定がある場合は一時的に移動
    original_cwd: str = os.getcwd()
    try:
        if target_dir is not None:
            os.chdir(target_dir)

        indices = [0, 1, 2]
        labels = ["g11(r)", "g12(r)", "g13(r)"]

        reader = RmcPotPpcf(cfg_or_ppcf)
        reader.load()

        r = reader.get_r()

        for idx, lbl in zip(indices, labels):
            gij = reader.get_single(idx)
            plt.plot(r, gij, label=lbl)

        plt.xlabel("r (Å)")
        plt.ylabel("g_ij(r)")
        plt.legend()
        plt.tight_layout()
        plt.show()

    finally:
        # 元のディレクトリに戻す
        os.chdir(original_cwd)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # カレントフォルダで cfg_or_fit を指定
        cfg_or_ppcf_arg: str = sys.argv[1]
        plot_ppcf(cfg_or_ppcf_arg, target_dir=None)

    elif len(sys.argv) == 3:
        # 第1引数でフォルダ、第2引数で cfg_or_fit
        dir_arg: str = sys.argv[1]
        cfg_or_ppcf_arg: str = sys.argv[2]
        plot_ppcf(cfg_or_ppcf_arg, target_dir=dir_arg)

    else:
        print("Usage:")
        print("  python plot_ppcf.py <cfg_or_hst>")
        print("  python plot_ppcf.py <dir> <cfg_or_hst>")
        sys.exit(1)
