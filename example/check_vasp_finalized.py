#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
OUTCAR が正常終了しているかどうかを判定するスクリプト
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import shutil
import sys

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspOutcar,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


def main() -> bool:
    """
    Returns:
        bool: True(VASPが正常に終了)
    """
    # 引数が 0 個 → デフォルト OUTCAR
    # 引数が 1 個 → 指定されたファイル
    if len(sys.argv) == 1:
        filename = "OUTCAR"
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        print("Usage: vasp_check_finalized.py [OUTCAR_file]")
        sys.exit(1)

    try:
        outcar = VaspOutcar(filename)
        if outcar.is_finalized():
            print(f"[OK] VASP finished successfully: {filename}")
            return True
        else:
            print(f"[NG] OUTCAR is not finalized: {filename}")
            return False

    except RuntimeError:
        print(f"[NG] OUTCAR is not finalized: {filename}")
        return False

    except Exception as e:
        print(f"[ERROR] Failed to read OUTCAR: {e}")
        sys.exit(4)


if __name__ == "__main__":
    ret = main()
