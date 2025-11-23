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

    config = Config("../config.yml")
    # vasp = Vasp(config=config, _logger=_logger)

    # vasp.set_tag("NSW", 1)
    # vasp.set_tag("EDIFF", 1e-04)
    # vasp.get_tag("EDIFF")

    # INCAR が存在すれば勝手に追加・更新/無ければ勝手に新規

    vasp_incar = VaspIncar(logger=logger)
    vasp_incar.set_tag("NSW", 1)
    vasp_incar.set_tag("EDIFF", 1e-04)
    vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    vasp_incar.set_tag("ISMEAR", 0)
    vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("NSW", 2)
    vasp_incar.set_tag("NELM", 30)
    vasp_incar.set_tag("IBRION", 2)
    vasp_incar.set_tag("ISIF", 2)
    vasp_incar.set_tag("LREAL", "auto")
