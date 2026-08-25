#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""plot_multi_converge.py
K.NAKADA, kengo.nakada@gmail.com

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

# 旧仕様
# import make_log_dirname


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


def find_rmc_dft_pairs(
    base_dir: str,
) -> List[Dict[str, str]]:
    """logX_rmc / logX_dft を描画列単位に整理する。

    連続した RMC または DFT はそれぞれ独立した列に配置する。
    RMC の直後が DFT の場合だけ、同じ列の上段・下段として揃える。
    """

    records: List[Tuple[int, str, str]] = []

    for name in os.listdir(base_dir):
        path_name = os.path.join(base_dir, name)

        if not os.path.isdir(path_name):
            continue

        parts = name.split("_")

        if len(parts) != 2:
            continue

        if not parts[0].startswith("log"):
            continue

        try:
            index = int(parts[0].replace("log", ""))
        except ValueError:
            continue

        stage = parts[1]
        if stage not in ("rmc", "dft"):
            continue

        records.append((index, stage, name))

    records.sort(key=lambda item: item[0])

    columns: List[Dict[str, str]] = []
    previous_stage: Optional[str] = None

    for index, stage, name in records:
        if stage == "rmc":
            columns.append(
                {
                    "index": str(index),
                    "rmc": name,
                    "dft": "",
                }
            )
        else:
            if previous_stage == "rmc" and columns[-1]["dft"] == "":
                columns[-1]["dft"] = name
            else:
                columns.append(
                    {
                        "index": str(index),
                        "rmc": "",
                        "dft": name,
                    }
                )

        previous_stage = stage

    return columns

def plot_multi_converge(
    log_pairs: List[Dict[str, str]],
    cfg_name: str,
    base_dir: str,
    logger: Optional[XLogger] = None,
) -> None:
    """RMC(上段) と DFT(下段) を同一 Figure に並べて描画

    Args:
        log_pairs (List[Dict[str, str]]):
            find_rmc_dft_pairs(base_dir) と同形式のリスト。
            各要素は {"index", "rmc", "dft"} を持ち、
            rmc または dft は空文字の場合がある。
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

    plot_columns: List[Dict[str, object]] = []

    hst_ymin: float = float("inf")
    hst_ymax: float = float("-inf")

    en_ymin: float = float("inf")
    en_ymax: float = float("-inf")

    for pair in log_pairs:
        rmc_dir_name: str = pair.get("rmc", "")
        dft_dir_name: str = pair.get("dft", "")

        column: Dict[str, object] = {
            "rmc_title": "",
            "rmc_data": None,
            "dft_title": "",
            "dft_data": None,
        }

        if rmc_dir_name:
            rmc_dir_path = os.path.join(base_dir, rmc_dir_name)
            h = read_chi2_from_dir(rmc_dir_path, cfg_name)

            if h is not False:
                steps, chi2 = h
                column["rmc_title"] = rmc_dir_name.split("_", 1)[0]
                column["rmc_data"] = (steps, chi2)

                if len(chi2) > 0:
                    hst_ymin = min(hst_ymin, min(chi2))
                    hst_ymax = max(hst_ymax, max(chi2))

        if dft_dir_name:
            dft_dir_path = os.path.join(base_dir, dft_dir_name)
            e = read_energy_from_dir(dft_dir_path)

            if e is not False:
                energies = e
                column["dft_title"] = dft_dir_name.split("_", 1)[0]
                column["dft_data"] = energies

                if energies.size > 0:
                    en_ymin = min(en_ymin, float(np.min(energies)))
                    en_ymax = max(en_ymax, float(np.max(energies)))

        plot_columns.append(column)

    if not plot_columns:
        logger.error("有効なログディレクトリが見つかりませんでした。")
        return

    if all(
        column["rmc_data"] is None and column["dft_data"] is None
        for column in plot_columns
    ):
        logger.error("有効なデータが見つかりませんでした。")
        return

    n: int = len(plot_columns)

    fig, axes = plt.subplots(
        nrows=2,
        ncols=n,
        figsize=(2.7 * n, 8),
    )

    if n == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    for col, column in enumerate(plot_columns):
        ax = axes[0, col]
        rmc_data = column["rmc_data"]

        if rmc_data is None:
            ax.axis("off")
        else:
            steps, chi2 = rmc_data
            ax.plot(steps, chi2)
            ax.set_title(str(column["rmc_title"]))
            if hst_ymin != float("inf"):
                ax.set_ylim(hst_ymin, hst_ymax)
            ax.set_xlabel("Step")
            ax.grid(True)

    visible_rmc_axes = [
        axes[0, col]
        for col, column in enumerate(plot_columns)
        if column["rmc_data"] is not None
    ]
    if visible_rmc_axes:
        visible_rmc_axes[0].set_ylabel("Chi^2")
        _hide_yticklabels_except_first(visible_rmc_axes)

    for col, column in enumerate(plot_columns):
        ax = axes[1, col]
        dft_data = column["dft_data"]

        if dft_data is None:
            ax.axis("off")
        else:
            energies = dft_data
            x = np.arange(energies.size, dtype=int)
            ax.plot(x, energies)
            ax.set_title(str(column["dft_title"]))
            if en_ymin != float("inf"):
                ax.set_ylim(en_ymin, en_ymax)
            ax.set_xlabel("SCF step")
            ax.grid(True)

    visible_dft_axes = [
        axes[1, col]
        for col, column in enumerate(plot_columns)
        if column["dft_data"] is not None
    ]
    if visible_dft_axes:
        visible_dft_axes[0].set_ylabel("Energy [eV]")
        _hide_yticklabels_except_first(visible_dft_axes)

    fig.suptitle("RMC (top)  /  DFT (bottom)", fontsize=16, y=0.98)

    plt.tight_layout(
        rect=(0.05, 0.03, 1.0, 0.96),
    )

    plt.show()

    fig.savefig("plot_multi_converge.png", dpi=300)
    print("Saved: plot_multi_converge.png")
