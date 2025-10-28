#!/usr/bin/env python
import os

from rmc_vasp import Vasp, VaspLog, RmcPot, RmcLog
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    vasp = Vasp(logger=logger)
    vasp_log = VaspLog(logger=logger)

    rmc = RmcPot(logger=logger)
    rmc_log = RmcLog(logger=logger)

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)

    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    max = 10

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"
    vasp.poscar2cfg(cfg_name)

    i = 0
    for i in range(0, max):

        log_dir = "log" + str(i)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        logger.info("rmc" + str(i))
        rmc.run(cfg_name)
        rmc_log.rmc_log()
        rmc_log.rmc_copy(log_dir)

        logger.info("cfg2poscar" + str(i))
        rmc.cfg2poscar(cfg_name)
        vasp.add_element_name("aaa.vasp")
        vasp.add_element_name("POSCAR")

        logger.info("vasp" + str(i))
        vasp.run()
        vasp_log.vasp_log()
        vasp_log.vasp_copy(log_dir)
        vasp.add_element_name("aaa.vasp")
        vasp.add_element_name("XDATCAR")

        logger.info("vasp2cfg" + str(i))
        vasp.xdatcar2poscar(cfg_name)
        vasp.poscar2cfg(cfg_name)
        logger.info("loop end " + str(i))
