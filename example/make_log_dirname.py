#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

log_dirname モジュール

RMC / DFT のログディレクトリ命名規則

    logX_rmc
    logX_dft

に基づき、ログディレクトリを収集するための共通関数群。

設計方針:
- RMC と DFT の命名規則差は本モジュール内に閉じ込める。
- マルチプロット側では分岐を書かない。
- 返り値は常に安定した並び順（index昇順）で返す。
"""

from typing import List, Dict
import os
import re


def find_log_pairs(
    base_dir: str,
) -> List[Dict[str, str]]:
    """
    RMC と DFT のログディレクトリをペアで収集する。

    対象:
        logX_rmc
        logX_dft

    同じ X を持つもののみを抽出し、
    index 昇順で返す。

    Args:
        base_dir (str):
            探索を行う基準ディレクトリ。

    Returns:
        List[Dict[str, str]]:
            [
                {
                    "index": "0",
                    "rmc": "log0_rmc",
                    "dft": "log0_dft",
                },
                ...
            ]
    """

    rmc_map: Dict[int, str] = {}
    dft_map: Dict[int, str] = {}

    names: List[str] = os.listdir(base_dir)

    for name in names:
        full_path: str = os.path.join(base_dir, name)

        if os.path.isdir(full_path) is False:
            continue

        m_rmc = re.fullmatch(r"log(\d+)_rmc", name)
        if m_rmc is not None:
            idx: int = int(m_rmc.group(1))
            rmc_map[idx] = name
            continue

        m_dft = re.fullmatch(r"log(\d+)_dft", name)
        if m_dft is not None:
            idx = int(m_dft.group(1))
            dft_map[idx] = name
            continue

    indices: List[int] = []

    for idx in rmc_map:
        if idx in dft_map:
            indices.append(idx)

    indices.sort()

    result: List[Dict[str, str]] = []

    for idx in indices:
        entry: Dict[str, str] = {}
        entry["index"] = str(idx)
        entry["rmc"] = rmc_map[idx]
        entry["dft"] = dft_map[idx]
        result.append(entry)

    return result


def find_rmc_dirs(
    base_dir: str,
) -> List[str]:
    """
    RMC ログディレクトリを収集する。

    対象:
        logX_rmc

    index 昇順で返す。

    Args:
        base_dir (str):
            探索を行う基準ディレクトリ。

    Returns:
        List[str]:
            ["log0_rmc", "log1_rmc", ...]
    """

    result: List[str] = []

    for name in os.listdir(base_dir):
        full_path: str = os.path.join(base_dir, name)

        if os.path.isdir(full_path) is False:
            continue

        m = re.fullmatch(r"log(\d+)_rmc", name)
        if m is None:
            continue

        result.append(name)

    result.sort(key=lambda x: int(x[3:-4]))
    return result


def find_dft_dirs(
    base_dir: str,
) -> List[str]:
    """
    DFT ログディレクトリを収集する。

    対象:
        logX_dft

    index 昇順で返す。

    Args:
        base_dir (str):
            探索を行う基準ディレクトリ。

    Returns:
        List[str]:
            ["log0_dft", "log1_dft", ...]
    """
    result: List[str] = []

    for name in os.listdir(base_dir):
        full_path: str = os.path.join(base_dir, name)

        if os.path.isdir(full_path) is False:
            continue

        m = re.fullmatch(r"log(\d+)_dft", name)
        if m is None:
            continue

        result.append(name)

    result.sort(key=lambda x: int(x[3:-4]))
    return result
