#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RMC_POT のログ(標準出力)ファイルを解析して、
- 最後の RMC パートが正常終了しているか
- RMC パートがいくつあったか（開始ブロック数）

を表示する簡単なツール。

使い方:
    python rmc_log_check.py job.log
    python rmc_log_check.py aaa.log

引数を省略した場合は "aaa.log" を見る。
aaa は cfg_name で、config.yml で設定されている
"""
import os
import sys

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog
from x_logger import XLogger


def main() -> bool:
    logger: XLogger = XLogger()
    config: Config = Config("config.yml")

    # ログファイル名を決定
    if len(sys.argv) >= 2:
        # ログファイル名を直接指定
        log_filename: str = sys.argv[1]
    else:
        log_filename = f"{config.cfg_name}.log"

    logger.info(f"Log file: {log_filename}")

    # --- ファイル存在チェック ---
    if not os.path.exists(log_filename):
        logger.error("========================================")
        logger.error(f"Log file       : {log_filename}")
        logger.error("========================================")
        logger.error("Error: 指定されたログファイルが存在しません。")
        logger.error(
            "       RMC_POT の実行が行われていないか、ログが生成されていません。"
        )
        sys.exit(1)

    # cfg_name は特に使わないので None のまま、log_filename を明示指定する
    rmc_log: RmcPotLog = RmcPotLog(
        config=config,
        logger=logger,
        cfg_name=None,
        log_filename=log_filename,
    )

    # 念のため再読込したい場合はこれを呼んでもよい
    # rmc_log.reload_log()

    # RMC パートの個数
    block_count: int = rmc_log.get_num_rmc_block()

    # 最後の RMC パートが閉じているかどうか
    finished: bool = rmc_log.is_finished()

    # 結果を表示
    logger.info("========================================")
    logger.info(f"Log file       : {log_filename}")
    logger.info("========================================")
    logger.info(f"RMC block count: {block_count}")
    logger.info(f"Last RMC block finished: {finished}")

    if block_count == 0:
        logger.error(
            "Note: このログには RMC_POT++ program のブロックが見つかりませんでした。"
        )
        return False
    else:
        if finished:
            logger.info("Last RMC block status: 正常に終了したと判定しました。")
            return True
        else:
            logger.error(
                "Last RMC block status: 途中でログが途切れている可能性があります。"
            )
            return False


if __name__ == "__main__":
    ret = main()
