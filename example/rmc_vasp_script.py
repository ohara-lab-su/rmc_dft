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
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")

    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")

    cfg_name = config.cfg_name
    vasp_name = config.vasp_name
    run_mode = config.run_mode
    element_info = config.element_info
    max_rmc_dft_loop = config.max_rmc_dft_loop
    log_vasp_dir = config.dft_log_dir
    log_rmc_dir = config.rmc_log_dir

    # rmc_log = RmcPotLog(config=config, logger=logger)
    rmc_log = RmcPotLog(cfg_name=cfg_name, logger=logger)
    rmc_dat = RmcPotDat(config=config, logger=logger)

    rmc_dat.set_comment("comment FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    rmc = RmcPot(
        rmc_dat=rmc_dat,
        rmc_log=rmc_log,
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
        vasp_potcar.build(elements, poscar_name="POTCAR")

    vasp_incar = VaspIncar(logger=logger)
    vasp_incar.set_tag("NSW", 10)
    vasp_incar.set_tag("EDIFF", 1e-04)
    vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    vasp_incar.set_tag("ISMEAR", 0)
    vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("NELM", 30)
    vasp_incar.set_tag("IBRION", 2)
    vasp_incar.set_tag("ISIF", 2)
    vasp_incar.set_tag("LREAL", "auto")

    vasp_log = VaspLog(logger=logger)

    vasp = Vasp(
        vasp_log=vasp_log,
        vasp_incar=vasp_incar,
        config=config,
        logger=logger,
    )

    # CFG の 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)

    digits = len(str(max_rmc_dft_loop - 1))

    i = 0
    for i in range(0, max_rmc_dft_loop):

        rmc_dir = f"{log_rmc_dir}{str(i).zfill(digits)}"
        vasp_dir = f"{log_vasp_dir}{str(i).zfill(digits)}"

        if not os.path.exists(rmc_dir):
            os.mkdir(rmc_dir)
        if not os.path.exists(vasp_dir):
            os.mkdir(vasp_dir)

        ## RMC ###########################################
        logger.info(f"== RMC {i}")
        rmc.postprocess()
        # rmc.run(cfg_name=cfg_name)
        rmc.run()
        rmc.postprocess(
            log_dir=rmc_dir,
            # cfg_name=cfg_name,
            # element_info="label.txt",
        )  # backup(loop番号つき), cfg --> xxx.vasp

        shutil.copy(f"{cfg_name}.vasp", "POSCAR")

        ## DFT ###########################################
        logger.info(f"== DFT(vasp) {i}")
        # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
        # vasp.run(mode="test")
        # vasp.run(mode=run_mode)
        vasp.run(mode="mpi")
        vasp.postprocess(
            log_dir=vasp_dir,
            # cfg_name=cfg_name,
        )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
        logger.info("loop end " + str(i))
