#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
import os
import shutil

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
)
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")

    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")

    # 初期CFG 作成 (POSCAR to CFG)
    poscar2cfg(cfg_name=config.cfg_name)

    # POSCAR to CFG (rmc用のCFG変換)
    # cfg_name = "aaa"
    # vasp_name = "aaa"
    cfg_name = config.cfg_name
    vasp_name = config.vasp_name
    run_mode = config.run_mode
    element_info = config.element_info
    max_rmc_dft_loop = config.max_rmc_dft_loop
    log_vasp_dir = config.dft_log_dir
    log_rmc_dir = config.rmc_log_dir

    # vasp_log = VaspLog(logger=logger)
    # vasp = Vasp(
    #     vasp_log=vasp_log,
    #     config=config,
    #     logger=logger,
    # )

    vasp = Vasp(config=config, logger=logger)

    # rmc_log = RmcPotLog(cfg_name=cfg_name, logger=logger)
    # rmc_log = RmcPotLog(config=config, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    rmc_dat = RmcPotDat(config=config, logger=logger)
    rmc_dat.set_comment("comment FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])

    rmc = RmcPot(rmc_dat=rmc_dat, config=config, logger=logger)

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)

    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    # max_rmc_dft_loop = 3

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)

    digits = len(str(max_rmc_dft_loop - 1))

    i = 0
    for i in range(0, max_rmc_dft_loop):

        _rmc_dir = f"{log_rmc_dir}{str(i).zfill(digits)}"
        _vasp_dir = f"{log_vasp_dir}{str(i).zfill(digits)}"

        if not os.path.exists(_rmc_dir):
            os.mkdir(_rmc_dir)
        if not os.path.exists(_vasp_dir):
            os.mkdir(_vasp_dir)

        logger.info(f"== rmc {i}")

        rmc.postprocess()
        # rmc.run(cfg_name=cfg_name)
        rmc.run()
        rmc.postprocess(log_dir=_rmc_dir)  # backup(loop番号つき), cfg --> xxx.vasp
        # rmc.postprocess(element_info="label.txt")
        # rmc.postprocess(
        #     log_dir=log_rmc_dir,  # 相対
        #     cfg_name=cfg_name,
        #     element_info="label.txt",
        # )

        shutil.copy(f"{cfg_name}.vasp", "POSCAR")

        logger.info(f"== vasp {i}")
        # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
        # vasp.run(mode="test")
        vasp.run(mode="mpi")
        # vasp.run(mode=run_mode)
        # vasp.postprocess(
        #     log_dir=log_vasp_dir,
        #     cfg_name=cfg_name,
        # )
        vasp.postprocess(
            log_dir=_vasp_dir
        )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
        logger.info("loop end " + str(i))
