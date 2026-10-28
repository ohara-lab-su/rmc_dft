#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

cfg2poscar を動かすだけ。

Usage:
    conv_cfg2poscar.py aaa Si,O
    conv_cfg2poscar.py config.yml
"""

import sys

# from rmc_dft.config import Config
# from rmc_dft import RmcPot, RmcPotLog
from rmc_util.config import Config
from rmc_util import RmcPot, RmcPotLog
from x_logger import XLogger


def main() -> None:
    """CFG を POSCAR へ変換する。"""
    if len(sys.argv) == 3:
        # 引数が２つのとき
        cfg_name = sys.argv[1]
        element_info = sys.argv[2].split(",")

    elif len(sys.argv) == 2:
        # 引数が1つのとき
        config = Config(sys.argv[1])
        cfg_name = config.cfg_name
        element_info = config.element_info
    else:
        raise ValueError(
            "Usage: conv_cfg2poscar.py aaa Si,O  または  conv_cfg2poscar.py config.yml"
        )

    logger = XLogger(
        log_level="debug",
        logger_name="conv_cfg2poscar",
    )
    rmc_log = RmcPotLog(
        cfg_name=cfg_name,
        logger=logger,
    )
    rmc = RmcPot(
        rmc_log=rmc_log,
        cfg_name=cfg_name,
        logger=logger,
    )
    rmc.cfg2poscar(
        cfg_name=cfg_name,
        element_info=element_info,
    )


if __name__ == "__main__":
    main()
