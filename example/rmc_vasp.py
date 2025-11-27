#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

既存の入力ファイルを使って計算する
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
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
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


if __name__ == "__main__":
    """"""
    config = Config("config.yml")
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    vasp = Vasp(vasp_incar=vasp_incar, config=config, logger=logger)

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    # vasp.poscar2cfg(config.cfg_name)

    # make INCAR
    # vasp_incar = VaspIncar(logger=logger)
    # vasp_incar.set_tag("EDIFF", 1e-04)
    # vasp_incar.set_tag("EDIFFG", 1e-05)
    # vasp_incar.set_tag("ISTART", 0)
    # #
    # vasp_incar.set_tag("ISMEAR", 0)  # Gussian
    # vasp_incar.set_tag("SIGMA", 0.1)
    # vasp_incar.set_tag("NELM", 30)
    # #
    # vasp_incar.set_tag("NSW", 10)
    # vasp_incar.set_tag("ISIF", 2)
    # vasp_incar.set_tag("IBRION", 2)  # CG
    # # vasp_incar.set_tag("IBRION", 3)  # Dampd
    # # vasp_incar.set_tag("POTIM", 0.05)  # Dampd scaling
    # vasp_incar.set_tag("LREAL", "auto")
    # # extra
    # vasp_incar.set_tag("ISPIN", 1)
    # vasp_incar.set_tag("LORBIT", 11)
    # vasp_incar.set_tag("NEDOS", 1500)

    # ------------------- DFT ------------------------
    logger.info(f"== DFT(vasp)")
    # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
    # vasp.run(mode="test")
    # vasp.run(mode=config.run_mode)
    ret = vasp.run(mode="mpi")
    if not ret:
        logger.error("**Error**: vasp execution failed")
        sys.exit(-1)

    log_dir = "log25"
    # vasp.postprocess(
    #     log_dir=vasp_dir,
    #     cfg_name=config.cfg_name,
    # )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
    vasp.backup(log_dir=log_dir)
    logger.info(f"loop end")
