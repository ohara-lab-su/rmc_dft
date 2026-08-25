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
        if stage != "rmc":
            if stage != "dft":
                continue

        records.append((index, stage, name))

    records.sort(key=lambda item: item[0])

    pairs: List[Dict[str, str]] = []

    for index, stage, name in records:
        if stage == "rmc":
            pairs.append(
                {
                    "index": str(index),
                    "rmc": name,
                    "dft": "",
                }
            )
            continue

        if stage == "dft":
            if len(pairs) > 0 and pairs[-1]["rmc"] and not pairs[-1]["dft"]:
                pairs[-1]["dft"] = name
            else:
                pairs.append(
                    {
                        "index": str(index),
                        "rmc": "",
                        "dft": name,
                    }
                )

    return pairs


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
            各要素は {"index","rmc","dft"} を持つ。
            RMC または DFT が存在しない列では空文字を持つ。
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

    plot_data: List[Dict[str, object]] = []

    hst_ymin: float = float("inf")
    hst_ymax: float = float("-inf")

    en_ymin: float = float("inf")
    en_ymax: float = float("-inf")

    for pair in log_pairs:
        rmc_dir_name: str = pair.get("rmc", "")
        dft_dir_name: str = pair.get("dft", "")

        rmc_data = False
        dft_data = False

        if rmc_dir_name:
            rmc_dir_path: str = os.path.join(base_dir, rmc_dir_name)
            rmc_data = read_chi2_from_dir(rmc_dir_path, cfg_name)

            if rmc_data is not False:
                steps, chi2 = rmc_data
                if len(chi2) > 0:
                    hst_ymin = min(hst_ymin, min(chi2))
                    hst_ymax = max(hst_ymax, max(chi2))

        if dft_dir_name:
            dft_dir_path: str = os.path.join(base_dir, dft_dir_name)
            dft_data = read_energy_from_dir(dft_dir_path)

            if dft_data is not False:
                energies = dft_data
                if energies.size > 0:
                    en_ymin = min(en_ymin, float(np.min(energies)))
                    en_ymax = max(en_ymax, float(np.max(energies)))

        plot_data.append(
            {
                "rmc": rmc_dir_name,
                "rmc_data": rmc_data,
                "dft": dft_dir_name,
                "dft_data": dft_data,
            }
        )

    if len(plot_data) == 0:
        logger.error("有効なデータが見つかりませんでした。")
        return

    if not any(
        item["rmc_data"] is not False or item["dft_data"] is not False
        for item in plot_data
    ):
        logger.error("有効なデータが見つかりませんでした。")
        return

    n: int = len(plot_data)

    fig, axes = plt.subplots(
        nrows=2,
        ncols=n,
        figsize=(2.7 * n, 8),
    )

    if n == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    first_rmc_col: Optional[int] = None
    first_dft_col: Optional[int] = None

    for col, item in enumerate(plot_data):
        ax = axes[0, col]
        h = item["rmc_data"]

        if h is False:
            ax.axis("off")
            continue

        if first_rmc_col is None:
            first_rmc_col = col

        steps, chi2 = h
        ax.plot(steps, chi2)
        ax.set_title(str(item["rmc"]).split("_", 1)[0])
        if hst_ymin != float("inf"):
            ax.set_ylim(hst_ymin, hst_ymax)
        ax.set_xlabel("Step")
        ax.grid(True)

    if first_rmc_col is not None:
        axes[0, first_rmc_col].set_ylabel("Chi^2")
        for col, item in enumerate(plot_data):
            if col != first_rmc_col and item["rmc_data"] is not False:
                axes[0, col].set_yticklabels([])

    for col, item in enumerate(plot_data):
        ax = axes[1, col]
        e = item["dft_data"]

        if e is False:
            ax.axis("off")
            continue

        if first_dft_col is None:
            first_dft_col = col

        energies = e
        x = np.arange(energies.size, dtype=int)
        ax.plot(x, energies)
        ax.set_title(str(item["dft"]).split("_", 1)[0])
        if en_ymin != float("inf"):
            ax.set_ylim(en_ymin, en_ymax)
        ax.set_xlabel("SCF step")
        ax.grid(True)

    if first_dft_col is not None:
        axes[1, first_dft_col].set_ylabel("Energy [eV]")
        for col, item in enumerate(plot_data):
            if col != first_dft_col and item["dft_data"] is not False:
                axes[1, col].set_yticklabels([])

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
    # 旧仕様
    # log_pairs_ = make_log_dirname.find_log_pairs(base_dir_)

    # 新仕様
    log_pairs_ = find_rmc_dft_pairs(base_dir_)

    plot_multi_converge(
        log_pairs_,
        cfg_name_,
        base_dir_,
        logger_,
    )
