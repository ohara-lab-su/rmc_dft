#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
import os
import shutil

from rmc_dft import Config, Vasp, VaspLog, RmcPot, RmcPotLog, RmcPotDat
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_run")

    config = Config("config.yml")

    # 既存の data ファイルがあれば、RmcPotDat() は勝手に読むが
    # ファイルがなかった読まない。
    rmc_dat = RmcPotDat(config=config, logger=logger)
    rmc_dat.set_comment("comment FeSiB")
    rmc_dat.set_density(0.0915)
    rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    rmc_dat.set_maximu_moves([0.1, 0.1, 0.1])
    rmc_dat.set_r_spacing(0.025)
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # rmc = RmcPot(rmc_dat=rmc_dat, config=config, logger=logger)

    # rmc.run(cfg_name=cfg_name)
    # rmc.preprocess()
    # rmc.run()
    # rmc.postprocess()
