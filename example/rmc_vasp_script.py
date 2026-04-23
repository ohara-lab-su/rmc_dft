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
    logger.info(f"max_rmc_dft_loop: {max_rmc_dft_loop}")

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
        start_loop, start_mode = check_restart_rmc_vasp(logger=logger)

    else:
        # ---------------------------
        # 初期から始める、初期POSCAR 作成 (POSCAR0 からコピーして、全てを始める)1
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

    # 1. RMC 関連インスタンスは RMC-DFT loop で毎回作った方がハンドリングしやすいのでここでは作らん

    # 2. VASP 関係インスタンス
    vasp_log = VaspLog(logger=logger)
    vasp_incar = VaspIncar(logger=logger)
    vasp_kpoints = VaspKpoints(logger=logger)

    # 3. VASP の INPUT 作成
    run_vasp_init(
        config,
        vasp_incar=vasp_incar,
        vasp_kpoints=vasp_kpoints,
        logger=logger,
    )

    i = 0
    for i in range(start_loop, start_loop + max_rmc_dft_loop):
        # for i in range(start_loop, max_rmc_dft_loop):
        # ------------------- RMC ------------------------
        if start_mode == "RMC":
            # 保存フォルダ名はそれぞれの run_rmc 内部で決まる
            run_rmc(
                config=config,
                auto_converge=False,
                msg=f"{i}",
                logger=logger,
            )
            # 次回のDFTの初期構造ファイル
            shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

            # STOP mode が RMC のときに RMC で止める
            if (i == max_rmc_dft_loop - 1) and (stop_mode == "RMC"):
                break

            start_mode = "VASP"

        logger.info("")
        logger.info("=====================")
        logger.info("=====================")
        logger.info("")

        # ------------------- DFT ------------------------
        if start_mode == "VASP":
            # 保存フォルダ名はそれぞれの run_vasp 内部で決まる
            run_vasp(
                config=config,
                vasp_log=vasp_log,
                vasp_incar=vasp_incar,
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

            start_mode = "RMC"
