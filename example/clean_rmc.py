#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
import os
import sys
import argparse
import shutil

# from rmc_dft import Config, Vasp, VaspLog, RmcPot, RmcPotLog
from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
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

    logger = XLogger(log_level="debug", logger_name="rmc_clear")

    args = parser.parse_args()
    if args.cfg_name is None:  # 引数が指定されていない場合は説明を出して終了
        logger.error("エラー: cfg_name が指定されていません。")
        logger.error("使用方法: ./rmc_clear.py <cfg_name>")
        logger.info("cfg_name = aaa を名前ととして使います")
        cfg_name = "aaa"
    else:
        cfg_name = args.cfg_name

    rmc = RmcPotLog(cfg_name=cfg_name, logger=logger)
    rmc.clear(cfg_name=cfg_name)
