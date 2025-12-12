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
    RmcPotPpcf,
)
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")
    rmc_log = RmcPotLog(cfg_name=config.cfg_name, logger=logger)
    rmc_dat = RmcPotDat(config=config, logger=logger)

    ##################
    rmc_dir = "log20"
    ##################

    # 初期POSCAR 作成
    # shutil.copy(f"POSCAR0", "POSCAR")
    # 初期CFG 作成 (POSCAR to CFG)
    # poscar2cfg(cfg_name=config.cfg_name)

    # パラメーター調整
    ######################################
    # rmc_dat.set_exp_filename("ascast.xsq")
    rmc_dat.set_exp_filename(config.rmc_exp_filename)
    rmc_dat.set_comment("comment FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # σ（実験データの許容誤差の標準偏差）
    #    小さいほど「ズレ」を許さず、結果的により厳しくフィットさせようとする。
    rmc_dat.set_sigma_factor(5e-4)

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
    # aaa.cfg がすでにある前提
    # ---------------------------

    rmc.preprocess()  # check input file
    # rmc.run(cfg_name=config.cfg_name)
    rmc.run()

    # ---------------------------
    # backup folder がすでにある前提
    # ---------------------------
    # rmc.postprocess()  ## backup and output xxx.vasp

    ## カレントフォルダで回すだけだと必要ない
    ## rmc.postprocess(
    ##     log_dir=rmc_dir,
    ##     cfg_name=config.cfg_name,
    ##     element_info=config.element_info,
    ## )  # backup(loop番号つき), cfg --> xxx.vasp
    logger.info("end")
