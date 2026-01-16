#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
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

        indices: List[int] = [0, 1, 2, 3, 4, 5]
        labels: List[str] = ["g11(r)", "g12(r)", "g13(r)", "g22(r)", "g23(r)", "g33(r)"]

        reader = RmcPotPpcf(cfg_name=cfg_name)
        reader.load()

        r = reader.get_r()

        # 6 枚のサブプロット（縦 3 × 横 2）
        fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(8, 10))
        axes = axes.flatten()

        for ax, idx, lbl in zip(axes, indices, labels):
            gij = reader.get_single(idx)
            ax.plot(r, gij)
            ax.set_title(lbl)
            ax.set_xlabel("r (Å)")
            ax.set_ylabel("g(r)")

        plt.tight_layout()
        plt.show()

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
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
