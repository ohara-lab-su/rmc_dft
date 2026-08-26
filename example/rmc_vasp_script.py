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


def _numbered_init_continue(init_prefix: str, current_run: int) -> bool:
    """
    current_run より前で最後に存在する番号付き init の
    CONTINUE_NUMBERED_INIT を返す。

    番号付き init が無い場合、またはフラグ未定義の場合は False。
    """
    for run_no in range(current_run - 1, -1, -1):
        init_file = f"{init_prefix}_{run_no}.py"
        if not os.path.isfile(init_file):
            continue

        namespace = runpy.run_path(init_file)
        return bool(namespace.get("CONTINUE_NUMBERED_INIT", False))

    return False


def _select_init_file(
    *,
    base_init_file: str,
    numbered_prefix: str,
    current_run: int,
) -> Optional[str]:
    """
    現在 run で実行する init ファイルを決める。

    1. 現在 run の番号付き init があれば、それを実行する。
    2. 無ければ、直前の番号付き init が継続モードなら何も実行しない。
    3. それ以外は基本 init を実行する。
    """
    numbered_init_file = f"{numbered_prefix}_{current_run}.py"

    if os.path.isfile(numbered_init_file):
        return numbered_init_file

    if _numbered_init_continue(numbered_prefix, current_run):
        return None

    return base_init_file


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
    for i in range(start_loop, start_loop + max_rmc_dft_loop):
        # for i in range(start_loop, max_rmc_dft_loop):
        # ------------------- RMC ------------------------
        if start_mode == "RMC":

            # msg の連番番号を作る
            log_dir_rmc = next_log_dir_name("rmc")
            msg_rmc = int(log_dir_rmc.split("_")[0].replace("log", ""))

            # RMC init
            #
            # - 現在 run の rmc_init_N.py があれば、それを使用する。
            # - 番号付き init の CONTINUE_NUMBERED_INIT=True が継続中なら、
            #   現在の *.dat をそのまま使用し、基本 init は実行しない。
            # - それ以外は rmc_init.py を実行する。
            #
            # restart でも同じ規則を使用する。
            rmc_init_file = _select_init_file(
                base_init_file="rmc_init.py",
                numbered_prefix="rmc_init",
                current_run=msg_rmc,
            )

            if rmc_init_file is not None and os.path.isfile(rmc_init_file):
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

            # 富岳対応 (キャッシュ対策)
            subprocess.run(["sleep", "5"], check=True)
            subprocess.run(["ls", "-la", "./"], check=True)

            # msg の連番番号を作る
            log_dir_vasp = next_log_dir_name("dft")
            msg_vasp = int(log_dir_vasp.split("_")[0].replace("log", ""))

            # VASP init
            #
            # - 現在 run の rmc_vasp_init_N.py があれば、それを使用する。
            # - 番号付き init の CONTINUE_NUMBERED_INIT=True が継続中なら、
            #   現在の INCAR をそのまま使用し、基本 init は実行しない。
            # - それ以外は rmc_vasp_init.py を実行する。
            #
            # restart でも同じ規則を使用する。
            rmc_vasp_init_file = _select_init_file(
                base_init_file="rmc_vasp_init.py",
                numbered_prefix="rmc_vasp_init",
                current_run=msg_vasp,
            )

            if (
                rmc_vasp_init_file is not None
                and os.path.isfile(rmc_vasp_init_file)
            ):
                rmc_vasp_init_namespace = runpy.run_path(rmc_vasp_init_file)
                rmc_vasp_init_namespace["run_vasp_init"](
                    config,
                    vasp_incar=vasp_incar,
                    vasp_kpoints=vasp_kpoints,
                    logger=logger,
                )

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
