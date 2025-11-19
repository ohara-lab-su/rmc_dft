#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

初期
RMC -> DFT の流れではなく

DFT -> RMC の流れ

"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
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
    RmcPotFit,
    RmcPotPpcf,
)
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")
    max_rmc_dft_loop = config.max_rmc_dft_loop

    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")

    # rmc_log = RmcPotLog(config=config, logger=logger)
    rmc_log = RmcPotLog(cfg_name=config.cfg_name, logger=logger)
    rmc_dat = RmcPotDat(config=config, logger=logger)

    ######################################
    # rmc_dat.set_exp_filename("ascast.xsq")
    rmc_dat.set_exp_filename(config.rmc_exp_filename)
    rmc_dat.set_comment("comment FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])
    ######################################

    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=config.cfg_name, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    rmc = RmcPot(
        rmc_dat=rmc_dat,  # instance
        rmc_log=rmc_log,  # instance
        config=config,
        logger=logger,
    )

    if not os.path.exists("KPOINTS"):
        vasp_kpoints = VaspKpoints(logger=logger)
        vasp_kpoints.set_mode("Monkhorst-Pack")
        vasp_kpoints.set_grid(1, 1, 1)
        vasp_kpoints.set_shift(0, 0, 0)

    if not os.path.exists("POTCAR"):
        vasp_potcar = VaspPotcarBuilder("~/potpaw_PBE.64", logger=logger)
        elements = ["Fe", "Si", "B"]
        # elements = config.element_info
        vasp_potcar.build(elements, poscar_name="POTCAR")

    vasp_incar = VaspIncar(logger=logger)
    vasp_incar.set_tag("NSW", 10)
    vasp_incar.set_tag("EDIFF", 1e-04)
    vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    vasp_incar.set_tag("ISMEAR", 0)  # Gussian
    vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("NELM", 30)
    vasp_incar.set_tag("IBRION", 2)  # CG
    # vasp_incar.set_tag("IBRION", 3)  # Dampd
    # vasp_incar.set_tag("POTIM", 0.05)  # Dampd scaling
    vasp_incar.set_tag("ISIF", 2)
    vasp_incar.set_tag("LREAL", "auto")

    vasp_log = VaspLog(logger=logger)

    vasp = Vasp(
        vasp_log=vasp_log,  # instance
        vasp_incar=vasp_incar,  # instance
        config=config,  # instance
        logger=logger,  # instance
    )

    # CFG の 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(config.cfg_name)

    digits = len(str(max_rmc_dft_loop - 1))

    i = 0
    for i in range(0, max_rmc_dft_loop):

        rmc_dir = f"{config.rmc_log_dir}{str(i).zfill(digits)}"
        vasp_dir = f"{config.dft_log_dir}{str(i).zfill(digits)}"

        if not os.path.exists(rmc_dir):
            os.mkdir(rmc_dir)
        if not os.path.exists(vasp_dir):
            os.mkdir(vasp_dir)

        # ------------------- DFT ------------------------
        logger.info(f"== DFT(vasp) {i}")
        # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
        # vasp.run(mode="test")
        # vasp.run(mode=config.run_mode)
        ret = vasp.run(mode="mpi")
        if not ret:
            logger.error("**Error**: vasp execution failed")
            sys.exit(-1)

        vasp.postprocess(
            log_dir=vasp_dir,
            cfg_name=config.cfg_name,
        )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
        # CFG ファイルが用意された
        exit()
        # ------------------- RMC ------------------------
        logger.info(f"== RMC {i}")
        logger.info(f"element_info = {config.element_info}")

        rmc.preprocess()
        # rmc.run(cfg_name=config.cfg_name)
        rmc.run()
        rmc.postprocess(
            log_dir=rmc_dir,
            cfg_name=config.cfg_name,
            element_info=config.element_info,
        )  # backup(loop番号つき), cfg --> xxx.vasp

        # POSCAR を用意する
        shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

        logger.info("loop end " + str(i))
