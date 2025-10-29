#!/usr/bin/env python
import os

# local の config
from config import Config

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog, RmcDft
from x_logger import XLogger


if __name__ == "__main__":
    _logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    _config = Config()

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"

    rmc_dft = RmcDft(
        rmc_code="RmcPot",
        dft_code="Vasp",
        cfg_name="aaa",
        max_loop=5,
        config=_config,
        logger=_logger,
    )

    # RMCの初期構造をPOSCAR から作る
    rmc_dft.poscar2cfg(cfg_name)
    rmc_dft.run()
