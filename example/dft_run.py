#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
import os
import sys
import argparse
import shutil

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog
from x_logger import XLogger


if __name__ == "__main__":

    logger = XLogger(log_level="debug", logger_name="dft")
    vasp_log = VaspLog(logger=logger)
    vasp = Vasp(
        vasp_log,
        vasp_name="INCAR",
        mpi_cmd="mpirun",
        mpi_flag="-np",
        num_procs=1,
        vasp_bin="vasp_std",
        job_cmd=None,
        logger=logger,
    )

    vasp.set_tag("NSW", 1)
    vasp.set_tag("EDIFF", 1e-04)
    vasp.get_tag("EDIFF")
    ret = vasp.get_tag("EDIFFG")
    print(ret)
    # vasp.cat("INCAR")
