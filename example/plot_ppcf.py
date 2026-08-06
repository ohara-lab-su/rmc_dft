#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import matplotlib.pyplot as plt

from rmc_dft import RmcPotPpcf


def plot_ppcf(
        cfg_name: str,
        target_dir: Optional[str] = None,
) -> None:
    # フォルダ指定がある場合は一時的に移動
    original_cwd: str = os.getcwd()
    try:
        if target_dir is not None:
            os.chdir(target_dir)

        reader = RmcPotPpcf(cfg_name=cfg_name)
        reader.load()

        r = reader.get_r()
        labels = reader.get_labels()

        for idx, lbl in enumerate(labels):
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
        # カレントフォルダで cfg_name を指定
        cfg_name_: str = sys.argv[1]
        plot_ppcf(cfg_name_, target_dir=None)

    elif len(sys.argv) == 3:
        # 第1引数でフォルダ、第2引数で cfg_name
        dir_arg: str = sys.argv[1]
        cfg_name_: str = sys.argv[2]
        plot_ppcf(cfg_name_, target_dir=dir_arg)

    else:
        print("Usage:")
        print("  python plot_ppcf.py <cfg_name>")
        print("  python plot_ppcf.py <dir> <cfg_name>")
        sys.exit(1)
