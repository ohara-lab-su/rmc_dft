#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

rmc_vasp_script.py はそのまま RMC-DFT で止めてしまうので、
DFT でおわる。
そこから一回RMCをかけるプログラム
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import argparse
import sys
import shutil
import re

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
from rmc_dft.util import poscar2cfg
from rmc_dft.util import next_log_dir_name as next_log_dir_name
from x_logger import XLogger


def run_rmc(
    config: Config,
    *,
    rmc_log: Optional[RmcPotLog] = None,
    rmc_dat: Optional[RmcPotDat] = None,
    auto_converge: Optional[bool] = False,
    postprocess: Optional[bool] = True,
    msg: Optional[str] = None,
    logger: Optional[Any] = None,
) -> bool:
    """
    RMC
    """
    if logger is None:
        logger = XLogger()

    if rmc_log is None:
        rmc_log = RmcPotLog(cfg_name=config.cfg_name, logger=logger)

    # if rmc_dat is None:
    #     rmc_dat = RmcPotDat(config=config, logger=logger)
    if rmc_dat is None:
        logger.error("**Error**: rmc_dat is None")
        return False

    ######################################

    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, config=config, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    rmc = RmcPot(
        rmc_dat=rmc_dat,  # instance
        rmc_log=rmc_log,  # instance
        config=config,
        logger=logger,
    )

    # ---------------------------
    # 以下
    # aaa.cfg がすでにある前提
    # ---------------------------

    if msg:
        logger.info(f"=============== RMC(RMC_POT) {msg} ============")
    else:
        logger.info(f"=============== RMC(RMC_POT) ============")

    # auto converge-loop
    # (デフォルト autoconve = False)
    while True:
        ##################
        # rmc_dir = f"log01_rmc"
        rmc_dir = next_log_dir_name("rmc")
        ##################

        logger.info("")
        logger.info(f"rmc_dir = {rmc_dir}")

        rmc.preprocess()  # check inputfile
        # rmc.run(cfg_name=config.cfg_name)
        rmc.run()

        # インスタンス生成時にログ読み込みする
        hst = RmcPotHst(cfg_name=f"{config.cfg_name}")  # sample.cfg → sample.hst

        ###################################################
        # RMC 収束判定
        if auto_converge:
            loop: Optional[int] = hst.detect_convergence(
                rel_tol=1.0e-2,
                acc_tol=1.0e-3,
                min_consecutive=2,
            )
        else:
            # auto_converge しない
            loop = 0  # とりあえず None 以外の数字
        ###################################################

        # ---------------------------
        # backup folder がすでにある前提
        # ---------------------------
        # rmc.postprocess()  ## backup and output xxx.vasp

        if postprocess:
            # カレントフォルダで回すだけだと必要ない
            rmc.postprocess(
                log_dir=rmc_dir,
                cfg_name=config.cfg_name,
                element_info=config.element_info,
            )  # backup(loop番号つき), cfg --> xxx.vasp
        logger.info("end")

        # auto_converge True: なんか失敗した
        if loop == -1:
            logger.error("**Error**: Insufficient HST records for convergence check.")
            # break
            return False

        # auto_converge True: 収束してないので繰り返す
        elif loop is None:
            logger.info("")
            logger.info("RMC is NOT converged.")
            logger.info("Continue RMC loop.")
            logger.info("")
            logger.info("=====================")
            logger.info("=====================")
            logger.info("")
            continue

        # auto_converge しないとき
        else:
            break

    # 収束点の情報を取得 (auto_converge = False のときは loop = 0)
    generated = hst.get_generated(loop)
    chi2_tot = hst.get_chi2_tot(loop)
    chi2_set1 = hst.get_chi2_set1(loop)
    acc = hst.get_accepted_per_tried(loop)

    logger.info("====================")
    logger.info("RMC is converged.")
    logger.info(f"  loop index           = {loop}")
    logger.info(f"  generated            = {generated}")
    logger.info(f"  chi2_tot             = {chi2_tot:.6e}")
    logger.info(f"  chi2/F(Q)_set#1      = {chi2_set1:.6e}")
    logger.info(f"  accepted/tried       = {acc:.6e}")

    logger.info("END of RMC")
    logger.info("")
    return True


if __name__ == "__main__":
    logger_ = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    config_ = Config("config.yml")
    msg_ = None

    # ---------------------------
    # 初期POSCAR 作成
    # shutil.copy(f"POSCAR0", "POSCAR")
    # 初期CFG 作成 (POSCAR to CFG)
    # poscar2cfg(cfg_name=config.cfg_name)#
    # ---------------------------

    rmc_log_ = RmcPotLog(cfg_name=config_.cfg_name, logger=logger_)
    rmc_dat_ = RmcPotDat(config=config_, logger=logger_)
    run_rmc(
        config=config_,
        rmc_log=rmc_log_,
        rmc_dat=rmc_dat_,
        auto_converge=False,
        msg=msg_,
        logger=logger_,
    )
