#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
import os
import sys
import argparse
import shutil

from rmc_dft import Config, Vasp, VaspLog, RmcPot, RmcPotLog
from x_logger import XLogger


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="指定した cfg_name に対応する RMCファイル群を削除します。"
    )
    parser.add_argument(
        "cfg_name",
        type=str,
        nargs="?",
        help="対象とするCFGファイル名（拡張子なし）",
    )

    logger = XLogger(
        log_level="debug",
        logger_name="rmc_clear",
    )

    args = parser.parse_args()

    # 引数が指定されていない場合は説明を出して終了
    if args.cfg_name is None:
        logger.error("エラー: cfg_name が指定されていません。")
        logger.error("使用方法: ./rmc_clear.py <cfg_name>")
        sys.exit(1)

    cfg_name = args.cfg_name

    rmc = RmcPotLog(cfg_name=cfg_name, logger=logger)
    rmc.clear(cfg_name=cfg_name)
