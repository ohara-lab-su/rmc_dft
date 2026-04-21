#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

cfg2poscar を動かすだけ
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import argparse

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
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":

    logger = XLogger(log_level="debug", logger_name="rmc_run")

    cfg_name = "aaa"
    # element_info = "label.txt" # kobayashi-method
    element_info = ["Fe", "Si", "B"]  # normal-method

    rmc_log = RmcPotLog(
        cfg_name=cfg_name,
        logger=logger,
    )
    rmc = RmcPot(
        rmc_log=rmc_log,
        cfg_name=cfg_name,
        logger=logger,
    )

    # CFG to POSCAR
    # rmc.cfg2poscar(cfg_name=cfg_name)
    rmc.cfg2poscar(
        cfg_name=cfg_name,
        element_info=element_info,
    )
