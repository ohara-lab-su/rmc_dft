#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

既存の入力ファイル(INCARなど)を使って計算する
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import shutil
import subprocess

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

from rmc_vasp_init import run_vasp_init
from rmc_dft.util import next_log_dir_name as next_log_dir_name


def run_vasp(
    config: Config,
    *,
    vasp_log: Optional[VaspLog] = None,
    vasp_incar: Optional[VaspIncar] = None,
    log_dir_vasp: Optional[str] = None,  # backup_dir
    run_mode: Optional[str] = None,
    postprocess_mode: bool = True,
    msg: Optional[str] = None,
    logger: Optional[Any] = None,
):
    if logger is None:
        logger = XLogger()

    if vasp_log is None:
        vasp_log = VaspLog(logger=logger)

    if vasp_incar is None:
        vasp_incar = VaspIncar(config=config, logger=logger)

    # VASP を動かす度に既存のRMC/DFTのフォルダを調査して countup する
    if log_dir_vasp is None:
        log_dir_vasp = next_log_dir_name("dft")

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

    ###################
    # ret = vasp.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
    # ret = vasp.run(mode="test")
    # ret = vasp.run(mode="mpi")
    # ret = vasp.run(mode="local")
    # ret = vasp.run(mode=config.run_mode)
    if run_mode is None:
        run_mode = config.run_mode
    ret = vasp.run(mode=run_mode)
    ###################
    if not ret:
        logger.error("**Error**: vasp execution failed")
        sys.exit(-1)

    # log_dir にバックアップする
    if postprocess_mode:
        ret = vasp.postprocess(
            log_dir=log_dir_vasp,
            cfg_name=config.cfg_name,
        )  # BACKUP(loop番号き), CONTCAR --> POSCAR, aaa.cfg, aaa.vasp
        if not ret:
            logger.error("**Error**: vasp postprocess failed")
            sys.exit(-1)
        # vasp.backup(log_dir=log_dir)

    logger.info("END of DFT")
    logger.info("")


if __name__ == "__main__":
    """"""
    # RUN-mode (MPI, mpi-command, local などは config.yml で定義)
    config_ = Config("config.yml")

    logger_ = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    vasp_log_ = VaspLog(logger=logger_)
    vasp_incar_ = VaspIncar(config=config_, logger=logger_)
    vasp_dir = config_.dft_log_dir
    msg_ = None

    #
    # POSCAR (構造) は事前に用意しておく
    #

    # VASP の INPUT を毎回作る/KPOINTS/POTCARは一回だけ作る)
    run_vasp_init(
        config_,
        vasp_incar=vasp_incar_,
        # vasp_kpoints=vasp_kpoints_,
        logger=logger_,
    )
    # 富岳対応 (cache対策)
    subprocess.run(["sleep", "5"], check=True)
    subprocess.run(["ls", "-la", "./"], check=True)

    # 保存フォルダ名はそれぞれの run_vasp 内部で決まる
    # 動作モード(mpiなど)各種は config から設定を読み取る
    run_vasp(
        config=config_,
        vasp_log=vasp_log_,
        # log_dir_vasp=vasp_dir,
        # run_mode=None,
        vasp_incar=vasp_incar_,
        msg=None,
        logger=logger_,
    )
