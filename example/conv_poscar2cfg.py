#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

poscar2cfg を呼び出すだけ
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import shutil

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspOutcar,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    config = None

    # ---------------------------------------------
    # 引数あり: cfg_name = vasp_name = argv[1]
    # ---------------------------------------------
    if len(sys.argv) >= 2:
        cfg_name: str = sys.argv[1]
        vasp_name: str = sys.argv[1]

        logger.info("command-line argument detected")
        logger.info(f"cfg_name  = {cfg_name}")
        logger.info(f"vasp_name = {vasp_name}")

    # ---------------------------------------------
    # 引数なし: POSCAR を使う（config は使わない）
    # ---------------------------------------------
    else:
        cfg_name: str = "POSCAR"
        vasp_name: str = "POSCAR"

        logger.info("no command-line argument; use POSCAR")
        logger.info(f"cfg_name  = {cfg_name}")
        logger.info(f"vasp_name = {vasp_name}")

    vasp = Vasp(config=None, logger=logger)
    # rmc = RmcPot(config=config, _logger=_logger)

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)
