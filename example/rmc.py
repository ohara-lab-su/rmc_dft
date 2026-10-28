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
)
from rmc_util import (
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotHst,
    RmcPotPpcf,
)
from rmc_util.util import poscar2cfg

# from rmc_dft.util import poscar2cfg

from rmc_dft.util import next_log_dir_name as next_log_dir_name
from x_logger import XLogger


def run_rmc(
    config: Config,
    *,
    rmc_log: Optional[RmcPotLog] = None,
    rmc_dat: Optional[RmcPotDat] = None,
    rmc_pot: Optional[RmcPot] = None,
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
        rmc_log = RmcPotLog(
            cfg_name=config.cfg_name,
            logger=logger,
        )

    # if rmc_dat is None:
    #     rmc_dat = RmcPotDat(config=config, logger=logger)
    if rmc_dat is None:
        logger.error("**Error**: rmc_dat is None")
        return False

    ######################################

    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, config=config, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    if rmc_pot is None:
        rmc = RmcPot(
            rmc_dat=rmc_dat,  # instance
            rmc_log=rmc_log,  # instance
            config=config,
            logger=logger,
        )
    else:
        rmc = rmc_pot

    # ---------------------------
    # 以下
    # aaa.cfg がすでにある前提
    # ---------------------------

    if msg:
        logger.info(f"[rmc] =============== RMC(RMC_POT) {msg} ============")
    else:
        logger.info(f"[rmc] =============== RMC(RMC_POT) ============")

    # auto converge-loop
    # (デフォルト auto_converge = False)
    while True:
        ##################
        # rmc_dir = f"log01_rmc"
        rmc_dir = next_log_dir_name("rmc")
        ##################

        # logger.info("")
        logger.info(f"[rmc] rmc_dir = {rmc_dir}")

        if not rmc.preprocess():
            logger.error("**Error**: RMC_POT input validation failed.")
            return False

        # cutoff と FNC の矛盾チェック
        if not rmc.check_fnc_cutoff_consistency(
            cfg_name=config.cfg_name,
        ):
            logger.error("**Error**: FNC and cutoff are inconsistent.")
            return False

        # RMC_POT の終了方法に関係なく後処理を行う。
        # Ctrl+C の場合も rmc.run() から KeyboardInterrupt が抜ける前に
        # 途中まで出力された *.cfg などを rmc_dir に退避する。
        try:
            run_ok = rmc.run()
        finally:
            if postprocess:
                rmc.postprocess(
                    log_dir=rmc_dir,
                    cfg_name=config.cfg_name,
                    element_info=config.element_info,
                )

        if not run_ok:
            logger.error("**Error**: RMC_POT execution failed.")
            return False

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

        logger.info("[rmc] end")

        # auto_converge True: なんか失敗した
        if loop == -1:
            logger.error("**Error**: Insufficient HST records for convergence check.")
            # break
            return False

        # auto_converge True: 収束してないので繰り返す
        elif loop is None:
            logger.info("")
            logger.info("[rmc] RMC is NOT converged.")
            logger.info("[rmc] Continue RMC loop.")
            logger.info("")
            logger.info("[rmc] =====================")
            logger.info("[rmc] =====================")
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

    logger.info(f"[rmc] ====================")
    logger.info(f"[rmc] RMC is converged.")
    logger.info(f"[rmc]   loop index           = {loop}")
    logger.info(f"[rmc]   generated            = {generated}")
    logger.info(f"[rmc]   chi2_tot             = {chi2_tot:.6e}")
    logger.info(f"[rmc]   chi2/F(Q)_set#1      = {chi2_set1:.6e}")
    logger.info(f"[rmc]   accepted/tried       = {acc:.6e}")

    logger.info(f"[rmc] END of RMC")
    logger.info(f"")
    return True


if __name__ == "__main__":
    from rmc_init import run_rmc_init

    logger_ = XLogger(
        log_level="debug",
        logger_name="rmc.py",
    )
    config_ = Config("config.yml")
    msg_ = None

    # ---------------------------
    # 初期POSCAR 作成
    # shutil.copy(f"POSCAR0", "POSCAR")
    # 初期CFG 作成 (POSCAR to CFG)
    # poscar2cfg(cfg_name=config.cfg_name)#
    # ---------------------------

    rmc_log_ = RmcPotLog(
        cfg_name=config_.cfg_name,
        logger=logger_,
    )

    # 実行バイナリが _ADVANCED_GEOM_CONST を有効に置く必要がある
    # make AGC=0
    # が必要となる
    rmc_dat_ = RmcPotDat(
        config=config_,
        logger=logger_,
    )

    # ini パラメーターでをここで作り、config や *.dat を上書きする
    run_rmc_init(
        config=config_,
        rmc_dat=rmc_dat_,
        logger=logger_,
    )

    try:
        run_rmc(
            config=config_,
            rmc_log=rmc_log_,
            rmc_dat=rmc_dat_,
            auto_converge=False,
            msg=msg_,
            logger=logger_,
        )
    except KeyboardInterrupt:
        logger_.warning("[rmc] Exit by Ctrl+C.")
        sys.exit(130)
