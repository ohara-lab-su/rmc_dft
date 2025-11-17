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
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger

from rmc_dft.vasp import VaspIncar

if __name__ == "__main__":
    """"""
    logger = XLogger(log_level="debug", logger_name="dft")
    config = Config("config.yml")

    elements = ["Fe", "Si", "B"]

    if os.path.exists("POTCAR"):
        logger.error("POTCAR is already exists.")
        sys.exit(-1)

    potcar = VaspPotcarBuilder("~/potpaw_PBE.64", logger=logger)
    potcar.build(elements, poscar_name="POTCAR")
