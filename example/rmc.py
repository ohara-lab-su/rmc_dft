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

    if rmc_dat is None:
        rmc_dat = RmcPotDat(config=config, logger=logger)

    ######################################
    # パラメーター調整
    # rmc_dat.set_exp_filename("ascast.xsq")
    # rmc_dat.set_exp_filename("HB1M_250_251224.xsq")
    rmc_dat.set_exp_filename("as_cast_0305.xsq")

    # 1 行目のコメント（系名）を設定する
    rmc_dat.set_comment("comment FeSiB")
    # 2 行目：number density（数密度）を設定する
    # rmc_dat.set_density(0.0915)
    # rmc_dat.set_density(0.09119)
    rmc_dat.set_density(0.0912)

    # 3 行目：cut offs（各原子種ペアのカットオフ距離）を設定する
    # rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    # FeSiB
    # 11(Fe-Fe) 2.45-2.55
    # 12(Fe-Si) 2.35-2.45
    # 13(Fe-B)  2.05-2.15
    # 22(Si-Si) 2.35-2.50
    # 23(Si-B)  2.0-2.1
    # 33(B-B)   1.7-1.9
    # rmc_dat.set_cutoffs([2.2, 1.9, 1.75, 1.8, 1.75, 1.5])
    # rmc_dat.set_cutoffs([2.1, 1.9, 1.75, 1.8, 1.75, 1.5])
    # rmc_dat.set_cutoffs([2.2, 2.2, 1.95, 1.8, 1.8, 2.8]) # 2026.02.16
    # rmc_dat.set_cutoffs([2.4, 2.3, 2.1, 2.0, 2.4, 1.7])
    rmc_dat.set_cutoffs([2.2, 2.1, 1.75, 2.3, 1.6, 1.6])

    # 4 行目：maximum moves（1 回の移動での最大変位量）を設定する
    # rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximu_moves([0.05, 0.01, 0.01])
    # rmc_dat.set_maximu_moves([0.05, 0.01, 0.01])  # 2026.02.16
    rmc_dat.set_maximu_moves([0.01, 0.01, 0.01])  # 2026.02.16

    # 5 行目：r spacing を設定する
    # rのステップ(Δr)
    rmc_dat.set_r_spacing(0.025)

    # 6行目: moveout を認めるかどうか？
    # カットオフ以下の位置での原子の存在を排除するか？認めるか？
    rmc_dat.set_moveout_option(True)
    # rmc_dat.set_moveout_option(False)

    # 9行目
    # 計算時間と構造をsaveするステップ間隔
    # rmc_dat.set_time_and_save(0.5, 0.5)
    # rmc_dat.set_time_and_save(5, 1)
    # rmc_dat.set_time_and_save(30, 1)
    rmc_dat.set_time_and_save(60, 1)
    # rmc_dat.set_time_and_save(120, 1)
    # rmc_dat.set_time_and_save(360, 1)
    # rmc_dat.set_time_and_save(480, 1)
    # rmc_dat.set_time_and_save(720, 1)

    # 10 行目：データ種の使用フラグ（g(r), neutron, x-ray, EXAFS）を設定する
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # 実験データファイル名（11 行目）を設定する
    rmc_dat.set_exp_filename(config.rmc_exp_filename)

    # 12 (データ範囲)
    # rmc_dat.set_exp_range(1, 1091, auto_write=True)
    # rmc_dat.set_exp_range(50, 1091)  # 2026.02.16
    rmc_dat.set_exp_range(85, 1091)  # 2026.02.16

    # 14 (温度因子)
    # σ（実験データの許容誤差の標準偏差）
    #    小さいほど「ズレ」を許さず、結果的により厳しくフィットさせようとする。
    # rmc_dat.set_sigma_factor(5e-4)
    # rmc_dat.set_sigma_factor(1e-5)
    # rmc_dat.set_sigma_factor(1e-2)  # 2026.02.16
    # rmc_dat.set_sigma_factor(1e-7)
    rmc_dat.set_sigma_factor(0.05)

    # 26 行目：1 回の move で動かす原子数（通常 1）を設定する
    rmc_dat.set_num_atoms_per_move(1)

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
