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
    vasp_log: Optional[VaspLog] = None,
    vasp_incar: Optional[VaspIncar] = None,
    log_dir_vasp: Optional[str] = None,  # backup_dir
    mode: Optional[str] = None,
    msg: Optional[str] = None,
    logger: Optional[Any] = None,
):
    if logger is None:
        logger = XLogger()

    if vasp_log is None:
        vasp_log = VaspLog(logger=logger)

    if vasp_incar is None:
        vasp_incar = VaspIncar(logger=logger)

    vasp = Vasp(
        config=config,  # instance
        vasp_log=vasp_log,  # instance
        vasp_incar=vasp_incar,  # instance
        logger=logger,  # instance
    )

    # -----------------------
    # このスクリプト自体をジョブで投げる。mpi だとジョブが システムの mpi run する
    # -----------------------
    if msg:
        logger.info(
            f"=============== DFT(vasp) vasp_dir={log_dir_vasp}, {msg} ============"
        )
    else:
        logger.info(
            f"=============== DFT(vasp) vasp_dir={log_dir_vasp}, {msg} ============"
        )

    # vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
    # vasp.run(mode="test")
    # vasp.run(mode=config.run_mode)
    # ret = vasp.run(mode="mpi")
    ret = vasp.run(mode="local")
    if not ret:
        logger.error("**Error**: vasp execution failed")
        sys.exit(-1)

    # log_dir にバックアップする
    vasp.postprocess(
        log_dir=log_dir_vasp,
        cfg_name=config.cfg_name,
    )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg
    # vasp.backup(log_dir=log_dir)

    logger.info("END of DFT")
    logger.info("")


if __name__ == "__main__":
    """"""
    config_ = Config("config.yml")
    logger_ = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    vasp_log_ = VaspLog(logger=logger_)
    vasp_incar_ = VaspIncar(logger=logger_)
    vasp_dir = config_.dft_log_dir
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
        log_dir_vasp=vasp_dir,
        msg=None,
        logger=logger_,
    )
