#!/usr/bin/env python
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
import optparse
import logging

# from numpy import *
import numpy as np

try:
    from x_logger import XLogger
except Exception as e:
    log_level = "INFO"
    logging.basicConfig(level=log_level.upper())
    logger = logging.getLogger(__name__)


def contcar2cfg(
    cfg_name: str,
    logger: Optional[Any] = None,
):
    """
    2025.10.29 update CONTCAR タイプ対応
    コア部分を分離

    Args:
        cfg_name (str):  CFG 保存用の名前
        logger (str):

    Returns:

    """
    if logger is None:
        # logger = XLogger(logger_name="contcar2cfg")
        logger = logging.getLogger("contcar2cfg")

    logger.info(f"INPUT file name : CONTCAR")
    logger.info(f"OUTPUT file name: {cfg_name}.cfg")

    return convert_to_cfg("CONTCAR", cfg_name)


def poscar2cfg(
    cfg_name: str,
    poscar_name: Optional[str] = None,
    logger: Optional[Any] = None,
) -> bool:
    """
    2025.10.29 update CONTCAR タイプ対応
    コア部分を分離

    Args:
        cfg_name (str): CFG 保存用の名前
        poscar_name (str):
        logger (Any):

    Returns:

    """
    if logger is None:
        # logger = XLogger(logger_name="contcar2cfg")
        logger = logging.getLogger("contcar2cfg")

    if poscar_name is None:
        poscar_name = "POSCAR"

    logger.info(f"== poscar2cfg(poscar_name={poscar_name}, cfg_name={cfg_name})")
    logger.info(f"INPUT file name : {poscar_name}")
    logger.info(f"OUTPUT file name: {cfg_name}.cfg")

    return convert_to_cfg(f"{poscar_name}", cfg_name)


def vasp2cfg(
    vasp_name: str,
    cfg_name: str = None,
    logger: Optional[Any] = None,
):
    """
    2025.10.29 update CONTCAR タイプ対応

    *) poscar2cfg ではなく vasp2cfg にしているのは
       poscar --> xxx.cfg ではなく
       xxx.vasp --> xxx.cfg を意図しているから

    Args:
        cfg_name (str): cfg_name.vasp ファイルを読み込む(POSCAR相当)
                        もし、cfg_name.vasp ファイルが存在しなければ
                        CONTCAR を読み込む
        vasp_name (str):
        logger:

    Returns:

    """
    if logger is None:
        # logger = XLogger(logger_name="contcar2cfg")
        logger = logging.getLogger("contcar2cfg")

    if cfg_name is None:
        cfg_name = vasp_name

    logger.info(f"INPUT file name : {vasp_name}.vasp")
    logger.info(f"OUTPUT file name: {cfg_name}.cfg")
    poscar_name = vasp_name + ".vasp"

    return convert_to_cfg(
        poscar_name=poscar_name,
        cfg_name=cfg_name,
    )


def convert_to_cfg(
    poscar_name: str = "POSCAR",
    cfg_name: str = "aaa",
    logger: Optional[Any] = None,
) -> bool:
    """
    name ファイルを中身 POSCAR/CONTCAR とみなして、そのファイルを cfg 形式にする

    Args:
        poscar_name (str): この名前のファイルをそのまま読み込む
        cfg_name (str): cfg_name.cfg として書き出す
        logger (XLogger):

    Returns:

    """
    if logger is None:
        # logger = XLogger(logger_name="contcar2cfg")
        logger = logging.getLogger("contcar2cfg")

    if not os.path.exists(poscar_name):
        logger.error(f"{poscar_name} file not found")
        return False

    # def readcfg():
    ###############################################
    # comment
    # ntype
    # type_
    # natom
    # t1_x,t1_y,t1_z
    # t2_x,t2_y,t2_z
    # t3_x,t3_y,t3_z
    # position

    ###############################################
    ## Open vasp file
    ##
    # tmp = open(cfg_name + ".vasp")
    try:
        with open(poscar_name, "r") as tmp:
            datfile = tmp.read()
            datlines = datfile.split("\n")

    except Exception:
        logger.error(f"Error: {poscar_name} file open failed")
        return False

    ###############################################
    ## Read Header
    ##

    # t = datlines[7].split()
    # natom = t[0]
    natom = sum(list(map(int, datlines[6].split())))

    # t = datlines[8].split()
    # ntype = t[0]
    ntype = len(list(map(int, datlines[6].split())))

    ## We don't construct fixed molecule.
    # nmoles = datlines[9]
    # angles = datlines[10]

    ###############################################
    ## Read Lattice Vector
    ##
    v = datlines[2].split()
    t1_x = float(v[0])  # lattice constant/2
    t1_y = float(v[1])
    t1_z = float(v[2])

    v = datlines[3].split()
    t2_x = float(v[0])
    t2_y = float(v[1])
    t2_z = float(v[2])

    v = datlines[4].split()
    t3_x = float(v[0])
    t3_y = float(v[1])
    t3_z = float(v[2])

    ###############################################
    ## Read Atoms
    ##
    # _lines = 17
    # type_ = np.zeros((int(ntype) + 1))
    # for i in range(int(ntype)):
    #    _lines += 1
    #    n = datlines[_lines].split()
    #    type_[i] = n[0]
    #    _lines += 1
    #    tmp = datlines[_lines]
    #    _lines += 1
    #    tmp = datlines[_lines]
    #    _lines += 1
    #    tmp = datlines[_lines]
    type_ = list(
        map(int, datlines[6].split())
    )  # length is different from original deffinition
    ###############################################
    ## Read Internal Coordinate
    ##
    position = np.zeros((int(natom) + 1, 3))  # final row is dummy
    lines = 7
    for i in range(int(natom)):
        lines += 1
        xyz = datlines[lines].split()
        position[i, 0] = xyz[0]
        position[i, 1] = xyz[1]
        position[i, 2] = xyz[2]
    # print position[i,0], position[i,1], position[i,2]

    ###############################################
    ## DATA convert
    ##
    t1_x = t1_x * 0.5
    t1_y = t1_y * 0.5
    t1_z = t1_z * 0.5

    t2_x = t2_x * 0.5
    t2_y = t2_y * 0.5
    t2_z = t2_z * 0.5

    t3_x = t3_x * 0.5
    t3_y = t3_y * 0.5
    t3_z = t3_z * 0.5

    for i in range(int(natom)):
        position[i, 0] = position[i, 0] * 2 - 1
        position[i, 1] = position[i, 1] * 2 - 1
        position[i, 2] = position[i, 2] * 2 - 1

    ###############################################
    ## OUTPUT for cfg
    cfg = open(cfg_name + ".cfg", "w")

    print(
        " (Version 3 format configuration file) !file created by SimpleCfg::save !",
        file=cfg,
    )
    print("comment", file=cfg)
    print("", file=cfg)
    print("", file=cfg)
    print(
        "                0               0               0 moves generated, tried, accepted",
        file=cfg,
    )
    print("          0              configurations saved", file=cfg)
    print("", file=cfg)
    print("      %d molecules of all types" % natom, file=cfg)
    print("          %d types of molecules " % ntype, file=cfg)
    print("          1 is the largest number of atoms in a molecule ", file=cfg)
    print("          0 Euler angles are provided ", file=cfg)
    print(" ", file=cfg)
    print("          F (box is cubic)	", file=cfg)
    print("            Defining vectors are: ", file=cfg)
    print("             %13.9f %13.9f %13.9f" % (t1_x, t1_y, t1_z), file=cfg)
    print("             %13.9f %13.9f %13.9f" % (t2_x, t2_y, t2_z), file=cfg)
    print("             %13.9f %13.9f %13.9f" % (t3_x, t3_y, t3_z), file=cfg)
    print("", file=cfg)

    for i in range(ntype):
        print("       %d molecules of type  %d" % (type_[i], (i + 1)), file=cfg)
        print("          1 atomic sites ", file=cfg)
        print("              0.000000   0.000000   0.000000", file=cfg)
        print("", file=cfg)

    for i in range(int(natom)):
        print(
            " %13.9f %13.9f %13.9f" % (position[i, 0], position[i, 1], position[i, 2]),
            file=cfg,
        )

    cfg.close()
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger_ = logging.getLogger("cfg2poscar")
    # logger_ = XLogger(log_level="info", logger_name="vasp2cfg")

    if len(sys.argv) < 2:
        logger_.error("Usage: python Rvasp2cfg_nonLIB2025.py vasp_name [cfg_name]")
        sys.exit(1)

    vasp_name_: str = sys.argv[1]

    if len(sys.argv) >= 3:
        cfg_name_: str = sys.argv[2]
    else:
        cfg_name_: str = vasp_name_

    logger_.info(f"vasp_name = {vasp_name_}")
    logger_.info(f"cfg_name  = {cfg_name_}")

    ret = vasp2cfg(
        vasp_name=vasp_name_,
        cfg_name=cfg_name_,
        logger=logger_,
    )

    if not ret:
        logger_.error("vasp2cfg failed")
        sys.exit(1)
