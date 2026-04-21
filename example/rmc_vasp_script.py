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
from rmc_dft.util import check_restart_rmc_vasp as check_restart_rmc_vasp

from x_logger import XLogger

# for local
from rmc import run_rmc
from rmc_vasp_init import run_vasp_init
from rmc_vasp import run_vasp


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")
    max_rmc_dft_loop = config.max_rmc_dft_loop

    #####################################################
    # 起動モード
    #   引数なし        → 通常開始
    #   restart 指定    → restart
    #                     rmc_vasp_script.py restart
    #####################################################
    # どちらかを選ぶ

    if len(sys.argv) >= 2 and sys.argv[1] == "restart":
        # ---------------------------
        # Restart する場合
        #   (RMC からスタートするときは aaa.cfg がある前提)
        #
        logger.info("[MODE] restart")

        start_loop, start_mode = check_restart_rmc_vasp(
            config=config,
            rmc_log_filename=None,
            max_loop=max_rmc_dft_loop,
            logger=logger,
        )

    else:
        # ---------------------------
        # 初期から始める、初期POSCAR 作成
        #
        logger.info("[MODE] normal start")

        shutil.copy(f"POSCAR0", "POSCAR")
        # 初期CFG 作成 (POSCAR to CFG)
        poscar2cfg(cfg_name=config.cfg_name)
        start_loop = 0
        start_mode = "RMC"

    #####################################################
    # sys.exit()  # コメントアウトしないとプログラムを止める

    # RMC で止めるか、VASP で止めるか？
    stop_mode = "VASP"

    # RMC 関連インスタンスは RMC-DFT loop で毎回作った方がハンドリングしやすいのでここでは作らん
    # rmc_log = RmcPotLog(config=config, _logger=_logger)
    # rmc_log = RmcPotLog(cfg_name=config.cfg_name, logger=logger)
    # rmc_dat = RmcPotDat(config=config, logger=logger)

    vasp_log = VaspLog(logger=logger)
    vasp_incar = VaspIncar(logger=logger)
    vasp_kpoints = VaspKpoints(logger=logger)

    run_vasp_init(
        config,
        vasp_incar=vasp_incar,
        vasp_kpoints=vasp_kpoints,
        logger=logger,
    )

    # True: その周回では RMC と VASP のどちらか一方だけ実行
    #       start_mode で決まる(ログフォルダ名称から決まる)
    first = True

    i = 0
    for i in range(start_loop, max_rmc_dft_loop):

        rmc_dir = next_log_dir_name("rmc")
        vasp_dir = next_log_dir_name("dft")

        # ------------------- RMC ------------------------
        # log_dir_rmc は RMC-内部loop ごとに取得するのでここでは直接書かない
        if (not first) or (start_mode == "RMC"):
            run_rmc(
                config=config,
                # auto_converge=True,
                auto_converge=False,
                msg=f"{i}",
                logger=logger,
            )
            # 次回のDFTの初期構造ファイル
            shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

            # STOP mode が RMC のときに RMC で止める
            if (i == max_rmc_dft_loop - 1) and (stop_mode == "RMC"):
                break

        logger.info("")
        logger.info("=====================")
        logger.info("=====================")
        logger.info("")

        # ------------------- DFT ------------------------
        if (not first) or (start_mode == "VASP"):
            run_vasp(
                config=config,
                vasp_log=vasp_log,
                vasp_incar=vasp_incar,
                log_dir_vasp=vasp_dir,
                msg=f"{i}",
                logger=logger,
            )
            # 次回のRMCの初期構造ファイル
            contcar2cfg(cfg_name=config.cfg_name)
            shutil.copy(
                f"{config.cfg_name}.cfg",
                f"{config.cfg_name}0.cfg",
            )

            # STOP mode が VASP のときに VASP で止める
            if (i == max_rmc_dft_loop - 1) and (stop_mode == "VASP"):
                break

        # RMC->VASP の順番に計算を戻す
        first = False
