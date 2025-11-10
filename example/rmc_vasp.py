#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
import os
import shutil

from rmc_dft import Config, Vasp, VaspLog, RmcPot, RmcPotLog
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config()
    config.load_yaml("config.yml")

    # POSCAR to CFG (rmc用のCFG変換)
    # cfg_name = "aaa"
    # vasp_name = "aaa"
    cfg_name = config.cfg_name
    vasp_name = config.vasp_name
    log_vasp_dir = config.vasp_log_dir

    # vasp_log = VaspLog(logger=logger)
    # vasp = Vasp(
    #     vasp_log=vasp_log,
    #     config=config,
    #     logger=logger,
    # )
    vasp = Vasp(config=config, logger=logger)

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    vasp.poscar2cfg(cfg_name)

    # run_mode = "local"

    if not os.path.exists(log_vasp_dir):
        os.mkdir(log_vasp_dir)

    vasp.run()
    # vasp.run(mode=run_mode)
    # vasp.postprocess(
    #     log_dir=log_vasp_dir,
    #     cfg_name=cfg_name,
    # )
    vasp.postprocess()
