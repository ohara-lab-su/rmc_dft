#!/usr/bin/env python3
import os


def logs_exist(prefix: str) -> bool:
    """
    prefixNN 形式のディレクトリが 1 個でも存在するかを判定する。

    例:
        prefix="log" のとき:
            log0, log9, log01, log10, log123 などがあれば True
    """
    try:
        entries = os.listdir(".")
    except FileNotFoundError:
        return False

    for name in entries:
        if not name.startswith(prefix):
            continue

        suffix = name[len(prefix) :]
        if len(suffix) == 0:
            continue

        if suffix.isdigit():
            return True

    return False
