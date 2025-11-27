#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst


def plot_chi(
    cfg_name: str,
    target_dir: Optional[str] = None,
) -> None:
    hst_file = f"{cfg_name}.hst"

    # フォルダ指定がある場合は一時的に移動
    original_cwd: str = os.getcwd()
    try:
        if target_dir is not None:
            os.chdir(target_dir)

        reader = RmcPotHst(hst_file)
        steps, chi2 = reader.read_chi2()

        plt.figure(figsize=(8, 5))
        plt.plot(steps, chi2)
        plt.xlabel("Step")
        plt.ylabel("Chi^2 (total/data_point)")
        plt.title("RMC-POT Fitting Progress")
        plt.grid(True)

        # 表示のみ（保存はしない）
        plt.show()
    finally:
        # 元のディレクトリに戻す
        os.chdir(original_cwd)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # カレントフォルダで cfg_name を指定
        cfg_name_: str = sys.argv[1]
        plot_chi(cfg_name_, target_dir=None)

    elif len(sys.argv) == 3:
        # 第1引数でフォルダ、第2引数で cfg_name
        dir_arg: str = sys.argv[1]
        cfg_name_: str = sys.argv[2]
        plot_chi(cfg_name_, target_dir=dir_arg)

    else:
        print("Usage:")
        print("  python plot_hst.py <cfg_name>")
        print("  python plot_hst.py <dir> <cfg_name>")
        sys.exit(1)
