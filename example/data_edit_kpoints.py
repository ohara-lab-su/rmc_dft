#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
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
)
from x_logger import XLogger

from rmc_dft.vasp import VaspIncar

if __name__ == "__main__":
    """"""
    logger = XLogger(log_level="debug", logger_name="dft")

    config = Config("config.yml")

    vasp_kpoints = VaspKpoints(logger=logger)
    # vasp_incar.set_tag("NSW", 1)
    # vasp_incar.set_tag("EDIFF", 1e-04)
