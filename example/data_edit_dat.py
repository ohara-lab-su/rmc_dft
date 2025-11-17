#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import argparse
import shutil

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


if __name__ == "__main__":
    """"""
    logger = XLogger(log_level="debug", logger_name="dft")

    config = Config("config.yml")
    rmc_dat = RmcPotDat(config=config, logger=logger)

    rmc_dat.set_comment("FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])
