#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_multi_converge.py

RMC と DFT の収束状況を同一 Figure に並べて描画

- 上段: RMC_POT の <cfg_name>.hst の chi2
- 下段: VASP OUTCAR の flatten energy

前提:
- 新ログ構造では、RMC と DFT が別ディレクトリ:
    logX_rmc
    logX_dft

本スクリプトでは、make_log_dirname.find_log_pairs(base_dir) が返す
ペア情報を入力として扱う

- log_pairs
  - 手動: [{"index":"0","rmc":"log0_rmc","dft":"log0_dft"}, ...]
  - 自動: log_search.find_log_pairs(base_dir)
  のいずれかをコメントアウトで切り替え

"""
from typing import Dict, List, Optional, Tuple, Union
import os
import numpy as np
import matplotlib.pyplot as plt

from rmc_dft import RmcPotHst, VaspOutcar
from x_logger import XLogger

import make_log_dirname


def read_chi2_from_dir(
    dir_name: str,
    cfg_name: str,
) -> Union[Tuple[list, list], bool]:
    """指定ディレクトリ内の <cfg_name>.hst から (steps, chi2) を読み取り"""

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


def read_energy_from_dir(
    dir_name: str,
) -> Union[np.ndarray, bool]:
    """指定ディレクトリ内の OUTCAR から flatten energy 列を返す"""

    outcar_path: str = os.path.join(dir_name, "OUTCAR")

    try:
        out = VaspOutcar(outcar_path)
    except (RuntimeError, FileNotFoundError):
        return False

    energies: np.ndarray = out.get_energy_flat()
    return energies


def _hide_yticklabels_except_first(axes_row) -> None:
    for j, ax in enumerate(axes_row):
        if j != 0:
            ax.set_yticklabels([])


def plot_multi_converge(
    log_pairs: List[Dict[str, str]],
    cfg_name: str,
    base_dir: str,
    logger: Optional[XLogger] = None,
) -> None:
    """RMC(上段) と DFT(下段) を同一 Figure に並べて描画

    Args:
        log_pairs (List[Dict[str, str]]):
            log_search.find_log_pairs(base_dir) と同形式のリスト。
            各要素は {"index","rmc","dft"} を持つ。
        cfg_name (str):
            RMC_POT の cfg 名（拡張子なし）。
        base_dir (str):
            logX_* が存在する基準ディレクトリ。
        logger (Optional[XLogger]):
            ロガー。

    Returns:
        None
    """

    logger = logger or XLogger()

    hst_data: List[Tuple[str, list, list]] = []
    en_data: List[Tuple[str, np.ndarray]] = []

    hst_ymin: float = float("inf")
    hst_ymax: float = float("-inf")

    en_ymin: float = float("inf")
    en_ymax: float = float("-inf")

    for pair in log_pairs:
        idx_str: str = pair.get("index", "")
        rmc_dir_name: str = pair.get("rmc", "")
        dft_dir_name: str = pair.get("dft", "")

        rmc_dir_path: str = os.path.join(base_dir, rmc_dir_name)
        dft_dir_path: str = os.path.join(base_dir, dft_dir_name)

        title: str = f"log{idx_str}"

        h = read_chi2_from_dir(rmc_dir_path, cfg_name)
        if h is False:
            continue

        steps, chi2 = h
        hst_data.append((title, steps, chi2))

        if len(chi2) > 0:
            hst_ymin = min(hst_ymin, min(chi2))
            hst_ymax = max(hst_ymax, max(chi2))

        e = read_energy_from_dir(dft_dir_path)
        if e is False:
            continue

        energies = e
        en_data.append((title, energies))

        if energies.size > 0:
            en_ymin = min(en_ymin, float(np.min(energies)))
            en_ymax = max(en_ymax, float(np.max(energies)))

    if len(hst_data) == 0 or len(en_data) == 0:
        logger.error("有効なデータが見つかりませんでした。")
        return

    n: int = min(len(hst_data), len(en_data))
    hst_data = hst_data[:n]
    en_data = en_data[:n]

    fig, axes = plt.subplots(
        nrows=2,
        ncols=n,
        figsize=(2.7 * n, 8),
    )

    if n == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    for col, (title, steps, chi2) in enumerate(hst_data):
        ax = axes[0, col]
        ax.plot(steps, chi2)
        ax.set_title(title)
        if hst_ymin != float("inf"):
            ax.set_ylim(hst_ymin, hst_ymax)
        ax.set_xlabel("Step")
        ax.grid(True)

    axes[0, 0].set_ylabel("Chi^2")
    _hide_yticklabels_except_first(axes[0])

    for col, (title, energies) in enumerate(en_data):
        ax = axes[1, col]
        x = np.arange(energies.size, dtype=int)
        ax.plot(x, energies)
        ax.set_title(title)
        if en_ymin != float("inf"):
            ax.set_ylim(en_ymin, en_ymax)
        ax.set_xlabel("SCF step")
        ax.grid(True)

    axes[1, 0].set_ylabel("Energy [eV]")
    _hide_yticklabels_except_first(axes[1])

    fig.suptitle("RMC (top)  /  DFT (bottom)", fontsize=16, y=0.98)

    plt.tight_layout(
        rect=(0.05, 0.03, 1.0, 0.96),
    )

    plt.show()

    fig.savefig("plot_multi_converge.png", dpi=300)
    print("Saved: plot_multi_converge.png")


if __name__ == "__main__":

    logger_ = XLogger(log_level="debug", logger_name="rmc_run")

    # -------------------- 設定 --------------------
    cfg_name_: str = "aaa"
    base_dir_: str = "."

    # -------------------- log_pairs（手動） --------------------
    # log_pairs_: List[Dict[str, str]] = [
    #     {"index": "0", "rmc": "log0_rmc", "dft": "log0_dft"},
    #     {"index": "1", "rmc": "log1_rmc", "dft": "log1_dft"},
    # ]

    # -------------------- log_pairs（自動） --------------------
    log_pairs_ = make_log_dirname.find_log_pairs(base_dir_)

    plot_multi_converge(
        log_pairs_,
        cfg_name_,
        base_dir_,
        logger_,
    )
