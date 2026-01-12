#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
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
    # 引数あり: config を使わず、cfg_name = vasp_name = argv[1]
    # ---------------------------------------------
    if len(sys.argv) >= 2:
        cfg_name: str = sys.argv[1]
        vasp_name: str = sys.argv[1]

        logger.info("command-line argument detected")
        logger.info(f"cfg_name  = {cfg_name}")
        logger.info(f"vasp_name = {vasp_name}")

    # ---------------------------------------------
    # 引数なし: 従来通り config.yml を使用
    # ---------------------------------------------
    else:
        config = Config("config.yml")

        # POSCAR to CFG (rmc用のCFG変換)
        cfg_name = config.cfg_name
        vasp_name = config.vasp_name

        logger.info("no command-line argument; use config.yml")
        logger.info(f"cfg_name  = {cfg_name}")
        logger.info(f"vasp_name = {vasp_name}")

    vasp = Vasp(config=config, logger=logger)
    # rmc = RmcPot(config=config, _logger=_logger)

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)
