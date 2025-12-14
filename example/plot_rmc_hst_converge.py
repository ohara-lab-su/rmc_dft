#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RmcPotHst 全ループ出力試験スクリプト
"""

from rmc_dft import Config
from rmc_dft.rmc_pot_hst import RmcPotHst
from x_logger import XLogger


def main() -> None:
    logger = XLogger(logger_name="hst_test", log_level="info")

    # # Config から hst ファイルパスを取得
    # config = Config("config.yml")
    # hst_path = config.cfg_name  # あなたの設計に従う

    hst = RmcPotHst(hst_path=hst_path, config=config, logger=logger)

    num_loops = hst.get_num_loops()
    print(f"Total loops: {num_loops}")

    # ループごとの全値を一覧表示
    for loop in range(num_loops):
        print("-" * 70)
        print(f"Loop {loop}")
        print(f"  generated      = {hst.get_generated(loop)}")
        print(f"  tried          = {hst.get_tried(loop)}")
        print(f"  accepted       = {hst.get_accepted(loop)}")
        print(f"  time           = {hst.get_time(loop)}")
        print(f"  tried/gen      = {hst.get_tried_per_gen(loop)}")
        print(f"  acc/tried      = {hst.get_acc_per_tried(loop)}")
        print(f"  chi2_tot       = {hst.get_chi2_tot(loop)}")
        print(f"  chi2_set1      = {hst.get_chi2_set1(loop)}")
    print("-" * 70)


if __name__ == "__main__":
    main()
