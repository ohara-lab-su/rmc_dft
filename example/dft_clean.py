#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC の出力を消す
"""
import os
import sys
import argparse
import shutil

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog
from x_logger import XLogger


if __name__ == "__main__":

    logger = XLogger(log_level="debug", logger_name="dft")
    vasp_log = VaspLog(logger=logger)
    vasp_log.clean()
