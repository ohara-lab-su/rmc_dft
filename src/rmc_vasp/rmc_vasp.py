#!/usr/bin/env python
import os

from vasp import Vasp, VaspLog
from rmc import RmcPot, RmcLog
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="kobayashi")
    vasp = Vasp(logger=logger)
    vasp_log = VaspLog(logger=logger)

    rmc = Rmc(logger=logger)
    rmc_log = RmcLog(logger=logger)

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)

    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    max = 10

    print("print ", _vasp)
    print("print ", _rmc)
    print("print ", _vasp.run)
    print("print ", _rmc.run)

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"
    vasp.poscar2cfg(cfg_name)

    i = 0
    for i in range(0, max):

        log_dir = "log" + str(i)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        print("rmc" + str(i))
        rmc.run("aaa")
        rmc_log.rmc_log()
        rmc_log.rmc_copy(log_dir)

        print("cfg2vasp" + str(i))
        rmc.cfg2vasp("aaa")
        vasp.add_element_name("aaa.vasp")
        vasp.add_element_name("POSCAR")

        print("vasp" + str(i))
        vasp.run()
        vasp_log.vasp_log()
        vasp_log.vasp_copy(log_dir)
        vasp.add_element_name("aaa.vasp")
        vasp.add_element_name("XDATCAR")

        print("vasp2cfg" + str(i))
        vasp.xdatcar2poscar("aaa")
        vasp.poscar2cfg("aaa")
        print("loop end " + str(i))
