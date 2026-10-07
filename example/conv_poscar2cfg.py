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
from rmc_dft.vasp.util.poscar2cfg import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(
        log_level="debug",
        logger_name="conv_poscar2cfg",
    )
    config = None

    # ---------------------------------------------
    # 引数2つ: argv[1] を入力 POSCAR、argv[2] を出力 CFG 名として使う
    # ---------------------------------------------
    if len(sys.argv) >= 3:
        poscar_name: str = sys.argv[1]
        cfg_name: str = sys.argv[2]

        logger.info("command-line arguments detected")
        logger.info(f"poscar_name = {poscar_name}")
        logger.info(f"cfg_name    = {cfg_name}")

    # ---------------------------------------------
    # 引数1つ: POSCAR を入力、argv[1] を出力 CFG 名として使う
    # ---------------------------------------------
    elif len(sys.argv) >= 2:
        poscar_name: str = "POSCAR"
        cfg_name: str = sys.argv[1]

        logger.info("command-line argument detected")
        logger.info(f"poscar_name = {poscar_name}")
        logger.info(f"cfg_name    = {cfg_name}")

    # ---------------------------------------------
    # 引数なし: POSCAR を使う（config は使わない）
    # ---------------------------------------------
    else:
        poscar_name: str = "POSCAR"
        cfg_name: str = "POSCAR"

        logger.info("no command-line argument; use POSCAR")
        logger.info(f"poscar_name = {poscar_name}")
        logger.info(f"cfg_name    = {cfg_name}")

    # 初期構造をベースに CFG ファイルを作成する
    poscar2cfg(cfg_name=cfg_name, poscar_name=poscar_name, logger=logger)
