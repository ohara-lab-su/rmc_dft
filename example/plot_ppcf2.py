#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""

import math
import os
from typing import Optional, List
import matplotlib.pyplot as plt

from rmc_dft import RmcPotPpcf


def plot_ppcf(
    cfg_name: str,
    target_dir: Optional[str] = None,
) -> None:
    original_cwd: str = os.getcwd()
    try:
        if target_dir is not None:
            os.chdir(target_dir)

        reader = RmcPotPpcf(cfg_name=cfg_name)
        reader.load()

        r = reader.get_r()
        labels: List[str] = reader.get_labels()

        n_plots = len(labels)
        ncols = 2
        nrows = math.ceil(n_plots / ncols)

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(8, 3.3 * nrows),
            squeeze=False,
        )
        axes = axes.flatten()

        for idx, lbl in enumerate(labels):
            gij = reader.get_single(idx)
            axes[idx].plot(r, gij)
            axes[idx].set_title(lbl)
            axes[idx].set_xlabel("r (Å)")
            axes[idx].set_ylabel("g(r)")

        for idx in range(n_plots, len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        plt.show()

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        # 引数省略時は "aaa" を指定した場合と同じ動作
        cfg_name_: str = "aaa"
        plot_ppcf(cfg_name_, target_dir=None)

    elif len(sys.argv) == 2:
        cfg_name_: str = sys.argv[1]
        plot_ppcf(cfg_name_, target_dir=None)

    elif len(sys.argv) == 3:
        dir_arg: str = sys.argv[1]
        cfg_name_: str = sys.argv[2]
        plot_ppcf(cfg_name_, target_dir=dir_arg)

    else:
        print("Usage:")
        print("  python plot_ppcf.py <cfg_name>")
        print("  python plot_ppcf.py <dir> <cfg_name>")
        sys.exit(1)
