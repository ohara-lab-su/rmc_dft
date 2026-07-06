#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GROMACS 用 top/gro から RMC_POT 用 top を作る実行スクリプト。

ライブラリ本体:
    rmc_dft.rmc_pot.util.gromacs_top_to_rmc_top

使用例:
    python convert_gromacs_top_to_rmc_top.py \
        --top sio2_em3.top \
        --gro SiO2_3000_s1_1.gro \
        --out aaa.top

RMC_POT が force field 名を認識できない場合は、必要に応じて次のように置換する。
ただし、どの include 名が正しいかは RMC_POT 側の設定・dat 側の potential 指定に合わせる。

    python convert_gromacs_top_to_rmc_top.py \
        --top sio2_em3.top \
        --gro SiO2_3000_s1_1.gro \
        --out aaa.top \
        --force-field-include ffoplsaa.itp
"""

import os
import sys


def _add_src_to_path() -> None:
    """source tree から直接実行する場合の import path を補助する。"""
    here = os.path.abspath(os.path.dirname(__file__))
    candidates = [
        os.path.abspath(os.path.join(here, "..", "..", "src")),
        os.path.abspath(os.path.join(here, "..", "..", "..", "src")),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)


_add_src_to_path()

from rmc_dft.rmc_pot.util.gromacs_top_to_rmc_top import main


if __name__ == "__main__":
    sys.exit(main())
