#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""

from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import re


def next_log_dir_name(
    stage: str,
    log_index_width: Optional[int] = None,
) -> str:
    """
    既存のログディレクトリ（log<整数>_(rmc|dft)）から「次に使う」ログ名を決める。

    本関数は、RMC と DFT の実行回数が一致しない（RMC を収束まで複数回回す）状況でも、
    ログディレクトリ名を単一の通し番号で一意に管理するための補助である。

    目的：
      - 既存の "log<整数>_(rmc|dft)" を走査し、最大の <整数> を見つける
      - 次番号として (最大値 + 1) を採用する
      - suffix として stage（"rmc" または "dft"）を付与する

    番号の扱い：
      - "log003_rmc" と "log3_rmc" は同じ整数 3 として扱う（ゼロ埋めは表示上の問題）
      - 最大が 999 の場合、次は 1000 とする（桁あふれは自然に桁拡張）

    ゼロ埋め幅（表示形式）の規則：
      - log_index_width が None の場合：
          既存ログに現れる数字部の最大桁数に追従する。
          ただし次番号がそれを超える場合（例：999→1000）は自然に桁拡張する。
      - log_index_width が int の場合：
          その値を「基本幅」としてゼロ埋めする。
          ただし次番号がその幅を超える場合は自然に桁拡張する。

    Args:
        stage (str):
            "rmc" または "dft" を想定する。戻り値の suffix にそのまま使う。
        log_index_width (Optional[int]):
            ゼロ埋め幅の基本値。
            None の場合は既存ログ幅に追従する。

    Returns:
        str:
            次に作成するログディレクトリ名。
            例： "log004_rmc", "log03_dft", "log1000_rmc"

    Notes:
        - 走査対象はカレントディレクトリ直下のディレクトリ名のみ。
        - 既存ログが存在しない場合、次番号は 1 とする。
        - stage 自体の妥当性チェック（"rmc"/"dft" 以外の拒否）はここでは行わない。
    """
    pattern = re.compile(r"^log(\d+)_((rmc)|(dft))$")

    max_index = -1
    max_width = 0

    for name in os.listdir("."):
        if not os.path.isdir(name):
            continue

        m = pattern.match(name)
        if m is None:
            continue

        index_str = m.group(1)
        index_val = int(index_str)

        if index_val > max_index:
            max_index = index_val

        if len(index_str) > max_width:
            max_width = len(index_str)

    next_index = max_index + 1
    next_index_str = str(next_index)

    if log_index_width is None:
        width = max_width
        if len(next_index_str) > width:
            width = len(next_index_str)
    else:
        width = log_index_width
        if len(next_index_str) > width:
            width = len(next_index_str)

    index_formatted = next_index_str.zfill(width)

    return f"log{index_formatted}_{stage}"


def find_next_log_index(
    prefix: str,
    max_loop: int,
) -> Tuple[int, int]:
    """
    RMC-DFT 用

    既存 prefixNN から
      - 次に使うインデックス(next_index)
      - 桁数(digits)
    を返す。

    例:
      log0, log1, ... log9 → 次 log10（桁は1→2へ自動昇格）
      log00, log01 → 次 log02
      log09 → 次 log10（桁は2を維持）
    """
    max_idx = -1
    max_existing_digits = 1

    try:
        entries = os.listdir(".")
    except FileNotFoundError:
        entries = []

    for name in entries:
        if not name.startswith(prefix):
            continue
        suf = name[len(prefix) :]
        if not suf.isdigit():
            continue
        idx = int(suf)
        digits = len(suf)
        if idx > max_idx:
            max_idx = idx
        if digits > max_existing_digits:
            max_existing_digits = digits

    # 次に使う index
    next_index = max_idx + 1 if max_idx >= 0 else 0

    # max_loop から必要桁数
    need_digits = len(str(max_loop - 1))
    digits = max(max_existing_digits, need_digits)

    return next_index, digits
