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
    # 1 行目のコメント（系名）を設定する
    rmc_dat.set_comment("comment FeSiB")
    # 2 行目：number density（数密度）を設定する
    rmc_dat.set_density(0.0915)

    # 3 行目：cut offs（各原子種ペアのカットオフ距離）を設定する
    # rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_cutoffs([2.1, 1.9, 1.75, 1.8, 1.75, 1.5])

    # 4 行目：maximum moves（1 回の移動での最大変位量）を設定する
    # rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_maximu_moves([0.05, 0.05, 0.05])

    # 5 行目：r spacing（g(r) のビン幅）を設定する
    rmc_dat.set_r_spacing(0.025)

    # 6行目: moveout を認めるかどうか？
    # rmc_dat.set_moveout_option(True)
    rmc_dat.set_moveout_option(False)

    # 9行目
    # 計算時間と構造をsaveするステップ間隔
    rmc_dat.set_time_and_save(60, 1)

    # 10 行目：データ種の使用フラグ（g(r), neutron, x-ray, EXAFS）を設定する
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # 実験データファイル名（11 行目）を設定する
    rmc_dat.set_exp_filename(config.rmc_exp_filename)
    # 26 行目：1 回の move で動かす原子数（通常 1）を設定する
    rmc_dat.set_num_atoms_per_move(1)

    # σ（実験データの許容誤差の標準偏差）
    #    小さいほど「ズレ」を許さず、結果的により厳しくフィットさせようとする。
    # rmc_dat.set_sigma_factor(5e-4)
    rmc_dat.set_sigma_factor(1e-5)

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
    # 入力の構造を用意する
    # ---------------------------

    # ---------------------------
    # aaa.cfg がすでにある前提
    # ---------------------------

    rmc.preprocess()  # check inputfile
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
