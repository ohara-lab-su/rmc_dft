#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMD-DFT を動かす
"""
import os
import shutil

# local の config
# from config import Config

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from rmc_dft.util import poscar2cfg

from x_logger import XLogger


if __name__ == "__main__":
    cfg_name = "aaa"
    max_rmc_dft_loop = 3

    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    config = Config("config.yml")

    config.cfg_name = cfg_name
    config.max_rmc_dft_loop = max_rmc_dft_loop

    # POSCAR to CFG (rmc用のCFG変換)

    rmc_dft = RmcDft(
        # rmc_code="RmcPot",
        # dft_code="Vasp",
        # max_rmc_dft_loop=3,
        config=config,
        logger=logger,
    )

    # RMCの初期構造をPOSCAR から作る
    shutil.copyfile("POSCAR0", "POSCAR")
    poscar2cfg(cfg_name=cfg_name)

    # rmc_dft.run(mode="local", cfg_name=cfg_name)
    # rmc_dft.run(mode="local")
    rmc_dft.run()
