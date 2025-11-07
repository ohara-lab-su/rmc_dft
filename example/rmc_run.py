#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC を動かすだけ
"""
import os
import sys
import argparse

from rmc_dft import Config, Vasp, VaspLog, RmcPot, RmcPotLog
from rmc_dft.util import poscar2cfg
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_run")

    config = Config()
    config.load_yaml("config.yml")

    cfg_name = config.cfg_name

    # POSCAR to CFG
    poscar2cfg(cfg_name=cfg_name)

    # rmc_log = RmcPotLog(cfg_name=cfg_name, logger=logger)
    # rmc = RmcPot(rmc_log=rmc_log, cfg_name=cfg_name, config=config, logger=logger)
    rmc_log = RmcPotLog(config=config, logger=logger)
    rmc = RmcPot(rmc_log=rmc_log, config=config, logger=logger)

    # ret = rmc.get_tag("density")
    # print(ret)
    # rmc.set_tag("density", 0.1)
    # ret = rmc.get_tag("density")
    # print(ret)

    rmc.run(cfg_name=cfg_name)
    rmc.postprocess()
