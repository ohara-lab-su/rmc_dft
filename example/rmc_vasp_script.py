#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する 実用 sample script
"""

from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import sys
import shutil
import subprocess
import runpy

# ----- QnNetworkBuilder
# from rmc_dft.rmc_pot.qn import QnNetworkBuilder
from qn.qn_network_builder import QnNetworkBuilder

# ----------------------

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
from rmc_vasp import run_vasp
from rmc_vasp_init import run_vasp_init
from rmc_vasp_init_safe import run_vasp_init_safe

if __name__ == "__main__":
    logger = XLogger(
        log_level="debug",
        logger_name="rmc_vasp_script",
    )

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

    # 実行バイナリが _ADVANCED_GEOM_CONST を有効に置く必要がある
    # make AGC=0
    # が必要となる
    rmc_dat = RmcPotDat(
        config=config,
        logger=logger,
    )

    # 2. VASP 関係インスタンス
    vasp_log = VaspLog(logger=logger)
    vasp_incar = VaspIncar(config=config, logger=logger)
    vasp_kpoints = VaspKpoints(config=config, logger=logger)

    i = 0
    vasp_step = 0
    for i in range(start_loop, start_loop + max_rmc_dft_loop):
        # for i in range(start_loop, max_rmc_dft_loop):
        # ------------------- RMC ------------------------
        if start_mode == "RMC":

            # msg の連番番号を作る
            log_dir_rmc = next_log_dir_name("rmc")
            msg_rmc = int(log_dir_rmc.split("_")[0].replace("log", ""))

            # RMC のパラメーターを作る
            # log0_rmc は rmc_init.py、それ以降は rmc_init_N.py を
            # 各 RMC 実行直前にファイルから読み込む。
            # ファイルが存在しなければ実行しない。
            if msg_rmc == 0:
                rmc_init_file = "rmc_init.py"
            else:
                rmc_init_file = f"rmc_init_{msg_rmc}.py"

            if os.path.isfile(rmc_init_file):
                rmc_init_namespace = runpy.run_path(rmc_init_file)
                rmc_init_namespace["run_rmc_init"](
                    config=config,
                    rmc_dat=rmc_dat,
                    logger=logger,
                )

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # 保存フォルダ名はそれぞれの run_rmc 内部で決まる
            run_rmc(
                config=config,
                rmc_dat=rmc_dat,
                auto_converge=False,
                msg=f"{msg_rmc}",
                logger=logger,
            )
            # 次回のDFTの初期構造ファイル
            shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

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

            vasp_step += 1

            if vasp_step == 1:
                # VASP の INPUT を毎回作る/KPOINTS/POTCARは一回だけ作る)
                run_vasp_init_safe(
                    config,
                    vasp_incar=vasp_incar,
                    vasp_kpoints=vasp_kpoints,
                    logger=logger,
                )

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # msg の連番番号を作る
            log_dir_vasp = next_log_dir_name("dft")
            msg_vasp = int(log_dir_vasp.split("_")[0].replace("log", ""))

            # 保存フォルダ名はそれぞれの run_vasp 内部で決まる
            run_vasp(
                config=config,
                vasp_log=vasp_log,
                vasp_incar=vasp_incar,
                postprocess_mode=True,
                msg=f"{msg_vasp}",
                logger=logger,
            )

            # ----- make aaa.top -----------------
            # builder = QnNetworkBuilder.from_poscar(
            #     poscar_name=f"{config.cfg_name}.vasp",
            #     # config_name=f"{config.cfg_name}.json",
            #     config_name=f"qn_config.json",
            # )
            # builder.write_all(f"{config.cfg_name}")
            # shutil.copyfile(f"{config.cfg_name}_rmc_fnc3.fnc", f"{config.cfg_name}.fnc")
            # shutil.copyfile(f"{config.cfg_name}_rmc_unit.top", f"{config.cfg_name}.top")
            # ------------------------------------

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # STOP mode が VASP のときに VASP で止める
            if (i == max_rmc_dft_loop - 1) and (stop_mode == "VASP"):
                break

            start_mode = "RMC"
