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
import re

# ----- QnNetworkBuilder
# from rmc_dft.rmc_pot.qn import QnNetworkBuilder
# from qn.qn_network_builder import QnNetworkBuilder

# ----------------------

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
from rmc_util.util import poscar2cfg, contcar2cfg

# from rmc_dft.util import poscar2cfg, contcar2cfg

from rmc_dft.util import next_log_dir_name as next_log_dir_name
from rmc_dft.util import check_restart_rmc_vasp as check_restart_rmc_vasp

from x_logger import XLogger

# for local
from rmc import run_rmc
from rmc_vasp import run_vasp

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

    # 現行 rmc_vasp_script.py と同じ init 選択状態。
    # init ファイル自体は各 run 直前に runpy.run_path() で毎回再読込する。
    rmc_init_file = "rmc_init.py"
    rmc_vasp_init_file = "rmc_vasp_init.py"

    #####################################################
    # 手動シーケンス設定
    #
    # 普段編集するのは rmc_vasp_sequence.py のみ。
    #####################################################
    sequence_namespace = runpy.run_path("rmc_vasp_script_sequence_dat.py")
    manual_sequence = sequence_namespace["manual_sequence"]
    continue_rmc_dft = sequence_namespace.get("continue_rmc_dft", False)

    for init_file in manual_sequence:
        rmc_match = re.fullmatch(r"rmc_init_(\d+)\.py", init_file)
        vasp_match = re.fullmatch(r"rmc_vasp_init_(\d+)\.py", init_file)

        if rmc_match:
            expected_msg = int(rmc_match.group(1))

            # 現行 RMC と同じ採番規則を使う
            log_dir_rmc = next_log_dir_name("rmc")
            msg_rmc = int(log_dir_rmc.split("_")[0].replace("log", ""))

            if msg_rmc != expected_msg:
                raise RuntimeError(
                    f"{init_file} と次のログ番号が一致しません: " f"{log_dir_rmc}"
                )

            if not os.path.isfile(init_file):
                raise FileNotFoundError(init_file)

            rmc_init_namespace = runpy.run_path(init_file)
            rmc_init_namespace["run_rmc_init"](
                config=config,
                rmc_dat=rmc_dat,
                logger=logger,
            )

            # continue_rmc_dft=True で通常ループへ移る場合に備え、
            # 現行 script と同じ CONTINUE_NUMBERED_INIT の状態を引き継ぐ。
            if rmc_init_namespace.get("CONTINUE_NUMBERED_INIT", False):
                rmc_init_file = init_file
            else:
                rmc_init_file = "rmc_init.py"

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # run_rmc() 側の既存のログ自動採番をそのまま使う
            run_rmc(
                config=config,
                rmc_dat=rmc_dat,
                auto_converge=False,
                msg=f"{msg_rmc}",
                logger=logger,
            )

            # 次回の DFT の初期構造ファイル
            shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

        elif vasp_match:
            expected_msg = int(vasp_match.group(1))

            # 現行 VASP と同じ採番規則を使う
            log_dir_vasp = next_log_dir_name("dft")
            msg_vasp = int(log_dir_vasp.split("_")[0].replace("log", ""))

            if msg_vasp != expected_msg:
                raise RuntimeError(
                    f"{init_file} と次のログ番号が一致しません: " f"{log_dir_vasp}"
                )

            if not os.path.isfile(init_file):
                raise FileNotFoundError(init_file)

            rmc_vasp_init_namespace = runpy.run_path(init_file)
            rmc_vasp_init_namespace["run_vasp_init"](
                config,
                vasp_incar=vasp_incar,
                vasp_kpoints=vasp_kpoints,
                logger=logger,
            )

            # continue_rmc_dft=True で通常ループへ移る場合に備え、
            # 現行 script と同じ CONTINUE_NUMBERED_INIT の状態を引き継ぐ。
            if rmc_vasp_init_namespace.get("CONTINUE_NUMBERED_INIT", False):
                rmc_vasp_init_file = init_file
            else:
                rmc_vasp_init_file = "rmc_vasp_init.py"

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # run_vasp() 側の既存のログ自動採番をそのまま使う
            run_vasp(
                config=config,
                vasp_log=vasp_log,
                vasp_incar=vasp_incar,
                postprocess_mode=True,
                msg=f"{msg_vasp}",
                logger=logger,
            )

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

        else:
            raise ValueError(
                "manual_sequence には "
                "rmc_init_N.py または rmc_vasp_init_N.py "
                f"を指定してください: {init_file}"
            )

    # 手動シーケンスだけで終了する場合
    if not continue_rmc_dft:
        logger.info("[SEQUENCE] manual sequence finished")
        logger.info("[SEQUENCE] continue_rmc_dft = False: stop")
        sys.exit(0)

    # continue_rmc_dft = True の場合のみ、
    # 手動シーケンス終了後に通常の RMC-DFT を RMC から再開する
    logger.info("[SEQUENCE] continue_rmc_dft = True: continue normal RMC-DFT")
    start_mode = "RMC"

    i = 0
    for i in range(start_loop, start_loop + max_rmc_dft_loop):
        # for i in range(start_loop, max_rmc_dft_loop):
        # ------------------- RMC ------------------------
        if start_mode == "RMC":

            # msg の連番番号を作る
            log_dir_rmc = next_log_dir_name("rmc")
            msg_rmc = int(log_dir_rmc.split("_")[0].replace("log", ""))

            # ----------------------------------------------------------------
            # RMC のパラメーターを作る
            # 現在 run の番号付き init があれば使用する。
            # 無ければ、現在選択中の init を毎回ファイルから再読込する。
            numbered_rmc_init_file = f"rmc_init_{msg_rmc}.py"
            if os.path.isfile(numbered_rmc_init_file):
                rmc_init_file = numbered_rmc_init_file

            if os.path.isfile(rmc_init_file):
                rmc_init_namespace = runpy.run_path(rmc_init_file)
                rmc_init_namespace["run_rmc_init"](
                    config=config,
                    rmc_dat=rmc_dat,
                    logger=logger,
                )

                if rmc_init_file != "rmc_init.py":
                    if not rmc_init_namespace.get("CONTINUE_NUMBERED_INIT", False):
                        rmc_init_file = "rmc_init.py"
            # ----------------------------------------------------------------

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

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # msg の連番番号を作る
            log_dir_vasp = next_log_dir_name("dft")
            msg_vasp = int(log_dir_vasp.split("_")[0].replace("log", ""))

            # ----------------------------------------------------------------
            # VASP のパラメーターを作る
            # 現在 run の番号付き init があれば使用する。
            # 無ければ、現在選択中の init を毎回ファイルから再読込する。
            numbered_vasp_init_file = f"rmc_vasp_init_{msg_vasp}.py"
            if os.path.isfile(numbered_vasp_init_file):
                rmc_vasp_init_file = numbered_vasp_init_file

            if os.path.isfile(rmc_vasp_init_file):
                rmc_vasp_init_namespace = runpy.run_path(rmc_vasp_init_file)
                rmc_vasp_init_namespace["run_vasp_init"](
                    config,
                    vasp_incar=vasp_incar,
                    vasp_kpoints=vasp_kpoints,
                    logger=logger,
                )

                if rmc_vasp_init_file != "rmc_vasp_init.py":
                    if not rmc_vasp_init_namespace.get(
                        "CONTINUE_NUMBERED_INIT",
                        False,
                    ):
                        rmc_vasp_init_file = "rmc_vasp_init.py"
            # ----------------------------------------------------------------

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
