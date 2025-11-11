#!/usr/bin/env python

# 2025.08.13
# Pick up the final configuration in XDATCAR and write to VASP format.
# Based on the original Rvasp2cfg_nonLIB2025.py, having the following release history:
###############################################################################
# K.NAKADA, kengo.nakada@gmail.com
#
# convert from VASP POSCAR file to RMC_POT cfg file
# python3 ./Rvasp2cfg_nonLIB2025.py input_file_name_without_extention
################################################################################
# 2025.06.19
# vasp -> cfg
#
# 2018.08.17
#  Python2/3 両対応
#
# 2014.10.08
#    Rvasp2cfg.py に仕様を合わせる
#    --> オプション関係を追加
#
# 2014.10.01
#    1st version
#
################################################################################
from __future__ import print_function

################################################################################
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

import sys
import os

from x_logger import XLogger


def xdatcar2poscar(
    vasp_name: str,
    logger: Optional[XLogger] = XLogger(),
):
    """
    VASP の XDATCAR ファイルを POSCAR 形式にする

    Args:
        vasp_name (str): Base name for output files.
        logger (Xlogger):
    """
    logger.info("INPUT file name : XDATCAR")
    logger.info(f"OUTPUT file name: {vasp_name}.vasp")

    if not os.path.exists("XDATCAR"):
        # sys.exit("XDATCAR file not found")
        return False

    # Conversion logic goes here
    # Copy the header and last configuration.

    ###############################################
    ## Open vasp file
    ##
    tmp = open("XDATCAR")
    datfile = tmp.read()
    tmp.close()
    datlines = datfile.split("\n")

    ###############################################
    ## Read Header
    ##
    num_header = 7  # Number of header lines in XDATCAR.

    natom = sum(list(map(int, datlines[6].split())))
    header = datlines[:num_header]  # First 6 lines are the header
    NSW = (len(datlines) - num_header) // (1 + natom)  # NSW >= 1.
    skip_lines = num_header + (NSW - 1) * (1 + natom)
    configuration = datlines[skip_lines : (skip_lines + (1 + natom))]

    # Write to VASP format
    with open(vasp_name + ".vasp", "w") as f:
        if NSW > 1:
            for line in header:
                f.write(line + "\n")
            for line in configuration:
                f.write(line + "\n")
        else:
            # NSW == 1
            for line in datlines:
                f.write(line + "\n")
    f.close()

    logger.info(f"{vasp_name}.vasp created from XDATCAR.")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("Usage: python xdatcar2poscar.py <base_name>")
        sys.exit(1)

    base_name = sys.argv[1]
    xdatcar2poscar(base_name)
