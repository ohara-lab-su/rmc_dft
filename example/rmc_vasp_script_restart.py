#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RMC–VASP restart system
途中再開＋ログ継続管理用。
"""

import os
import sys
import shutil
from typing import Tuple  # find_next_log_index の型注釈用

from rmc_dft import (
    Config,
    Vasp,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
)
from rmc_dft.util import check_rmc_and_vasp
from rmc_dft.util import find_next_log_index
from rmc_dft.util import logs_exist
from x_logger import XLogger


def check_restart(
    *,
    config: Config,
    rmc_log_filename: Optional[str],
    max_loop: int,
    logger: XLogger,
) -> Tuple[int, str]:
    """
    どのモードで、どこからスタートするか調べる

    Args:
        config:
        logger:
        rmc_log_filename:
        max_loop:

    Returns:

    """
    # ----------------------------------------------------------
    # RMC/VASP の終了判定
    # ----------------------------------------------------------
    rmc_finished, vasp_finished = check_rmc_and_vasp(
        config=config,
        logger=logger,
        log_filename=rmc_log_filename,
    )
    logger.info(f"[STATUS] RMC finished={rmc_finished}, VASP finished={vasp_finished}")

    # ----------------------------------------------------------
    # 既存 logN / dftN から次インデックス・桁数を決定
    # ----------------------------------------------------------
    next_rmc_idx, rmc_digits = find_next_log_index(config.rmc_log_dir, max_loop)
    next_vasp_idx, vasp_digits = find_next_log_index(config.dft_log_dir, max_loop)

    # 「最後に使われた index」は next - 1（存在しない場合は -1）
    last_rmc_idx = next_rmc_idx - 1
    last_vasp_idx = next_vasp_idx - 1

    logger.info(
        f"[LOG-INDEX] last_rmc={last_rmc_idx}, next_rmc={next_rmc_idx}, "
        f"digits_rmc={rmc_digits}"
    )
    logger.info(
        f"[LOG-INDEX] last_vasp={last_vasp_idx}, next_vasp={next_vasp_idx}, "
        f"digits_vasp={vasp_digits}"
    )

    # ----------------------------------------------------------
    # どこから再開するかを決定
    #
    # ルール：
    #   1) RMC 未完・VASP 完了   → RMC から再開（新しい log 番号）
    #   2) RMC 完了・VASP 未完   → VASP から再開（同じ log 番号）
    #   3) RMC 完了・VASP 完了   → 次ループの RMC から開始（新しい log 番号）
    #   4) RMC 未完・VASP 未完   →
    #        - 既存ログが一切無ければ「新規スタート扱い」で loop=0, RMC から
    #        - 既存ログがあるなら危険なので何もしないで終了
    # ----------------------------------------------------------
    if (not rmc_finished) and vasp_finished:
        # ケース1: RMC 未完・VASP 完了 →「次の」ループとして RMC から再開
        #################
        start_loop = next_rmc_idx
        start_mode = "RMC"
        #################
        logger.info(
            "[DECISION] RMC not finished, VASP finished → "
            f"restart from {start_mode} loop {start_loop}"
        )

    elif rmc_finished and (not vasp_finished):
        # ケース2: RMC 完了・VASP 未完 → 最後のループ番号で VASP から再開
        if last_rmc_idx < 0:
            logger.error(
                "[ERROR] RMC finished flag is True but no RMC log directory is found."
            )
            sys.exit(1)
        #################
        start_loop = last_rmc_idx
        start_mode = "VASP"
        #################
        logger.info(
            "[DECISION] RMC finished, VASP not finished → "
            f"restart from {start_mode} loop {start_loop}"
        )

    elif rmc_finished and vasp_finished:
        # ケース3: 両方完了 → 次のループで新規 RMC から
        #################
        start_loop = next_rmc_idx
        start_mode = "RMC"
        #################
        logger.info(
            f"[DECISION] RMC & VASP finished → start new {start_mode} loop "
            f"{start_loop}"
        )

    else:
        # ケース4: RMC 未完・VASP 未完
        #   既存ログが無ければ「新規スタート扱い」
        #   （log0, dft0 などが一つも無い状態 → 初回起動とみなす）
        if (last_rmc_idx < 0) and (last_vasp_idx < 0):
            # 既存ログディレクトリの有無
            rmc_logs_exist = logs_exist(config.rmc_log_dir)
            vasp_logs_exist = logs_exist(config.dft_log_dir)

            #################
            start_loop = 0
            start_mode = "RMC"
            #################
            logger.warning(
                "[DECISION] RMC/VASP both not finished, but no existing log "
                "directories are found.\n"
                "           Treat this as a fresh start: start from loop 0 (RMC)."
            )
        else:
            logger.error(
                "[FATAL] RMC and VASP are both NOT finished, and some log directories exist.\n"
                "        This state is treated as invalid for restart.\n"
                "        Please fix the situation manually (or run the non-restart script)."
            )
            sys.exit(1)

    logger.info(f"[RESTART] loop = {start_loop}, mode = {start_mode}")
    return start_loop, start_mode


if __name__ == "__main__":
    logger_ = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    # ----------------------------------------------------------
    # 設定読込
    # ----------------------------------------------------------
    config_ = Config("config.yml")
    cfg = config_.cfg_name
    max_loop_ = config_.max_rmc_dft_loop

    # ----------------------------------------------------------
    # コマンドライン引数：RMC ログファイル（ジョブファイル等）指定
    #   rmc_vasp_script_restart.py [rmc_log_file]
    # ----------------------------------------------------------
    if len(sys.argv) >= 2:
        rmc_log_filename_ = sys.argv[1]
        logger.info(f"[ARG] RMC log file specified: {rmc_log_filename}")
    else:
        rmc_log_filename_ = None

    ret = check_restart(
        config=config_,
        rmc_log_filename=rmc_log_filename_,
        max_loop=max_loop_,
        logger=logger_,
    )
    start_loop_ = ret[0]
    start_mode_ = ret[1]

    # ----------------------------------------------------------
    # RMC/VASP インスタンス構築（入力ファイルは既存前提）
    # ----------------------------------------------------------
    rmc_log = RmcPotLog(cfg_name=cfg, logger=logger_)
    rmc_dat = RmcPotDat(config=config_, logger=logger_)

    rmc = RmcPot(
        rmc_dat=rmc_dat,
        rmc_log=rmc_log,
        config=config_,
        logger=logger_,
    )

    vasp_log = VaspLog(logger=logger_)
    vasp = Vasp(
        vasp_log=vasp_log,
        config=config_,
        logger=logger_,
    )

    # ----------------------------------------------------------
    # メインループ：決定した start_loop から max_loop まで
    # ----------------------------------------------------------
    mode = start_mode_
    logger_.info(f"start_mode = {mode}")

    for i in range(start_loop_, max_loop_):

        rmc_dir = f"{config_.rmc_log_dir}{str(i).zfill(rmc_digits)}"
        vasp_dir = f"{config_.dft_log_dir}{str(i).zfill(vasp_digits)}"

        if not os.path.exists(rmc_dir):
            os.mkdir(rmc_dir)
        if not os.path.exists(vasp_dir):
            os.mkdir(vasp_dir)

        # ---------------- RMC パート ----------------
        if mode == "RMC":
            logger_.info("")
            logger_.info(f"======================== RMC loop {i}")
            logger_.info("")

            rmc.preprocess()
            rmc.run()
            rmc.postprocess(
                log_dir=rmc_dir,
                cfg_name=cfg,
                element_info=config_.element_info,
            )  # backup(loop番号つき), cfg --> xxx.vasp

            # RMC の結果から POSCAR 更新
            shutil.copy(f"{cfg}.vasp", "POSCAR")

            # 次は VASP へ
            mode = "VASP"

        # ---------------- VASP パート ----------------
        if mode == "VASP":
            logger_.info("")
            logger_.info(f"======================== VASP loop {i}")
            logger_.info("")

            ret = vasp.run(mode="mpi")
            if not ret:
                logger_.error("**Error**: vasp execution failed")
                sys.exit(-1)

            vasp.postprocess(
                log_dir=vasp_dir,
                cfg_name=cfg,
            )  # BACKUP(loop番号つき), CONTCAR --> POSCAR, aaa.cfg

            # 次ループは再び RMC から
            mode = "RMC"

        logger_.info(f"---- LOOP {i} END ----")

    logger_.info("==== ALL LOOP FINISHED ====")
