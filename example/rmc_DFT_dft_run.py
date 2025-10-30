#!/usr/bin/env python
"""
RMD-DFT を動かす
"""
import os

# local の config
from config import Config

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog, RmcDft
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    config = Config()

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"

    rmc_dft = RmcDft(
        rmc_code="RmcPot",
        dft_code="Vasp",
        cfg_name="aaa",
        max_loop=3,
        config=config,
        logger=logger,
    )

    # RMCの初期構造をPOSCAR から作る
    # rmc_dft.poscar2cfg(cfg_name)
    rmc_dft.init(cfg_name=cfg_name)
    rmc_dft.run(cfg_name=cfg_name)
