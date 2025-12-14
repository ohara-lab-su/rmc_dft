#!/usr/bin/env python3
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence


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
