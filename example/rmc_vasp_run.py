#!/usr/bin/env python
import os

from rmc_vasp import Vasp, VaspLog, RmcPot, RmcLog
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    vasp_log = VaspLog(logger=logger)
    vasp = Vasp(vasp_log, logger=logger)

    rmc_log = RmcLog(logger=logger)
    rmc = RmcPot(rmc_log, logger=logger)

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)

    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    max = 10

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)

    i = 0
    for i in range(0, max):

        log_dir = "log" + str(i)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        logger.info("== rmc" + str(i))
        rmc.run(cfg_name)

        logger.info("== vasp" + str(i))
        vasp.run()

        logger.info("loop end " + str(i))
