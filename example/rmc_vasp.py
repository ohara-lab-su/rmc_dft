#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

既存の入力ファイル(INCARなど)を使って計算する
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
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
from x_logger import XLogger

from rmc_vasp_init import run_dft_init


def run_dft(
    config: Config,
    *,
    vasp_log: VaspLog,
    vasp_incar: VaspIncar,
    mode: str = None,
    msg: str = None,
    logger: XLogger = None,
):
    if logger is None:
        logger = XLogger()

    if vasp_log is None:
        vasp_log = VaspLog(logger=logger)

    if vasp_incar is None:
        vasp_incar = VaspIncar(logger=logger)

    vasp = Vasp(
        vasp_log=vasp_log,  # instance
        vasp_incar=vasp_incar,  # instance
        config=config,  # instance
        logger=logger,  # instance
    )

    # -----------------------
    # このスクリプト自体をジョブで投げる。mpi だとジョブが システムの mpi run する
    # -----------------------
    if msg:
        logger.info(f"=============== DFT(vasp) {msg} ============")
    else:
        logger.info(f"=============== DFT(vasp) {msg} ============")

    # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
    # vasp.run(mode="test")
    # vasp.run(mode=config.run_mode)
    # ret = vasp.run(mode="mpi")
    ret = vasp.run(mode="local")
    if not ret:
        logger.error("**Error**: vasp execution failed")
        sys.exit(-1)

    vasp.postprocess(
        log_dir=vasp_dir,
        cfg_name=config.cfg_name,
    )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
    # vasp.backup(log_dir=log_dir)

    logger.info("END of DFT")
    logger.info("")


if __name__ == "__main__":
    """"""
    config_ = Config("config.yml")
    logger_ = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    vasp_log_ = VaspLog(logger=logger)
    vasp_incar_ = VaspIncar(logger=logger_)
    msg_ = None

    run_dft_init(
        config_,
        vasp_incar=vasp_incar_,
        logger=logger_,
    )
    run_dft(
        config_,
        vasp_log=vasp_log_,
        vasp_incar=vasp_incar_,
        msg=None,
        logger=logger_,
    )
