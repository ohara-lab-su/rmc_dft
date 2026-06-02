#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

特定の用途用のカスタム RMC-DFT
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import shutil

from rmc_dft import Config, VaspIncar, VaspLog
from rmc_dft.util import poscar2cfg, contcar2cfg

from rmc import run_rmc
from rmc_vasp import run_vasp

from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")

    #  VASP 関係インスタンス
    vasp_log = VaspLog(logger=logger)
    vasp_incar = VaspIncar(logger=logger)

    # ---------------------------------------
    # RMC 計算を 一回するする
    i = "11_RMC"
    run_rmc(
        config=config,
        auto_converge=False,
        msg=f"{i}",
        logger=logger,
    )
    # 次回のDFTの初期構造ファイルを作成する
    shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

    # ---------------------------------------
    # DFT 計算を一回する
    i = "12_DFT"
    run_vasp(
        config=config,
        vasp_log=vasp_log,
        vasp_incar=vasp_incar,
        msg=f"{i}",
        logger=logger,
    )
    # 次回のRMCの初期構造ファイルを作成する
    contcar2cfg(cfg_name=config.cfg_name)
    shutil.copy(
        f"{config.cfg_name}.cfg",
        f"{config.cfg_name}0.cfg",
    )
