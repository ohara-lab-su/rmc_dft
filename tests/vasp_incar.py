#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
import os
import shutil

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"
    vasp_name = "aaa"

    vasp_log = VaspLog(logger=logger)
    vasp = Vasp(
        vasp_log=vasp_log,
        vasp_name=vasp_name,
        logger=logger,
    )

    print(vasp.NSW)
    print(vasp.EDIFF)
    print(vasp.EDIFFG)
    print(vasp.get_EDIFFG())
    # print(vasp.to_incar())
