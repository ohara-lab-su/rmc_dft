#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
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
    VaspOutcar,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotHst,
    RmcPotPpcf,
)
from rmc_dft.util import poscar2cfg, contcar2cfg
from rmc_dft.util import next_log_dir_name as next_log_dir_name
from x_logger import XLogger

# for local
from rmc import run_rmc
from rmc_vasp_init import run_dft_init
from rmc_vasp import run_dft


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")
    max_rmc_dft_loop = config.max_rmc_dft_loop

    # ---------------------------
    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")
    # 初期CFG 作成 (POSCAR to CFG)
    poscar2cfg(cfg_name=config.cfg_name)  #
    # ---------------------------

    # rmc_log = RmcPotLog(config=config, _logger=_logger)
    # rmc_log = RmcPotLog(cfg_name=config.cfg_name, logger=logger)
    # rmc_dat = RmcPotDat(config=config, logger=logger)

    vasp_log = VaspLog(logger=logger)
    vasp_incar = VaspIncar(logger=logger)
    vasp_kpoints = VaspKpoints(logger=logger)

    run_dft_init(
        config,
        vasp_incar=vasp_incar,
        vasp_kpoints=vasp_kpoints,
        logger=logger,
    )

    digits = len(str(max_rmc_dft_loop - 1))

    i = 0
    for i in range(0, max_rmc_dft_loop):
        rmc_dir = next_log_dir_name("rmc")
        vasp_dir = next_log_dir_name("dft")

        # ------------------- RMC ------------------------
        run_rmc(config, msg=f"{i}", logger=logger)
        shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

        logger.info("")
        logger.info("=====================")
        logger.info("=====================")
        logger.info("")

        # ------------------- DFT ------------------------
        run_dft(
            config,
            vasp_log=vasp_log,
            vasp_incar=vasp_incar,
            msg=f"{i}",
            logger=logger,
        )
        contcar2cfg(cfg_name=config.cfg_name)
