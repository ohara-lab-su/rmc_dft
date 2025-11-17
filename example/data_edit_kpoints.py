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

# from rmc_dft.vasp import VaspIncar
from x_logger import XLogger


if __name__ == "__main__":
    """"""
    logger = XLogger(log_level="debug", logger_name="dft")

    config = Config("config.yml")

    if os.path.exists("KPOINTS"):
        logger.error("KPOINTS is already exists.")
        sys.exit(-1)

    # KPOINTS が存在すればそれを使う
    vasp_kpoints = VaspKpoints(logger=logger)
    vasp_kpoints.set_mode("Monkhorst-Pack")
    vasp_kpoints.set_grid(1, 1, 1)
    vasp_kpoints.set_shift(0, 0, 0)
