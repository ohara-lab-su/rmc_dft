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

    config = Config()
    config.load_yaml("config.yml")

    # POSCAR to CFG (rmc用のCFG変換)
    # cfg_name = "aaa"
    # vasp_name = "aaa"
    cfg_name = config.cfg_name
    vasp_name = config.vasp_name

    vasp_log = VaspLog(logger=logger)
    vasp = Vasp(
        vasp_log=vasp_log,
        config=config,
        logger=logger,
    )

    # rmc_log = RmcPotLog(cfg_name=cfg_name, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, logger=logger)
    rmc_log = RmcPotLog(config=config, logger=logger)
    rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)

    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    max_loop = 3

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)

    run_mode = "local"
    digits = len(str(max_loop - 1))

    i = 0
    for i in range(0, max_loop):

        log_rmc_dir = f"log{str(i).zfill(digits)}"
        log_vasp_dir = f"log{str(i).zfill(digits)}"

        if not os.path.exists(log_rmc_dir):
            os.mkdir(log_rmc_dir)

        logger.info("== rmc" + str(i))
        rmc.run(cfg_name=cfg_name)
        rmc.postprocess(
            log_dir=log_rmc_dir,
            cfg_name=cfg_name,
            element_info="label.txt",
        )

        logger.info("== vasp" + str(i))
        vasp.run(mode=run_mode)
        # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
        # vasp.run(mode="test")
        vasp.postprocess(
            log_dir=log_vasp_dir,
            cfg_name=cfg_name,
        )
        logger.info("loop end " + str(i))
