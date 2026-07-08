#!/usr/bin/env python
# K.NAKADA, kengo.nakada@gmail.com
#
# convert from RMC_POT cfg file to VASP POSCAR file
#
################################################################################
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

from typing import Optional, Union, Sequence, List


def parse_elements(
    element_info: Optional[Union[str, Sequence[str]]] = None,
) -> Optional[List[str]]:

    # ----------------------------
    # None の場合
    # ----------------------------
    if element_info is None:
        elements = None
        return elements

    # ----------------------------
    # str の場合
    #   - まずファイルとして open を試す
    #   - 失敗したら文字列として扱う
    # ----------------------------
    if isinstance(element_info, str):
        text = None

        try:
            with open(element_info, "r") as f:
                text = f.read()
        except OSError:
            # ファイルとして開けなければ、そのまま文字列として扱う
            text = element_info

        text = text.strip()
        elements = []

        for token in text.split(","):
            elements.append(token.strip())

        return elements

    # ----------------------------
    # Sequence[str] の場合
    # ----------------------------
    elements = []

    for elem in element_info:
        elements.append(elem)

    return elements


def make_vasp_elements_line(elements: List[str]) -> str:
    line = ""

    for elem in elements:
        line += elem
        line += " "

    line = line.rstrip()

    return line


def cfg2poscar(
    cfg_name: str,
    vasp_name: Optional[str] = None,
    element_info: Optional[Union[str, Sequence[str]]] = None,
    logger: Optional[Any] = None,
) -> bool:
    """
    RMCPOT cfg 形式を poscar 形式にする
    SAE を使わない独立版(noLIB)

    Args:
        cfg_name (str):
        vasp_name (str):
        element_info (str or Sequence[str]):
        logger (Any):
    Returns:
        bool:
    """
    if logger is None:
        logger = logging.getLogger("cfg2poscar")
        # logger = XLogger(logger_name="cfg2poscar")

    if not vasp_name:
        vasp_name = cfg_name

    logger.info(f"INPUT file name : {cfg_name}.cfg")
    logger.info(f"OUTPUT file name: {vasp_name}.vasp")

    if not os.path.exists(cfg_name + ".cfg"):
        sys.exit(cfg_name + ".cfg file not found")

    try:
        # def readcfg():
        ###############################################
        # comment
        # ntype
        # type
        # natom
        # t1_x,t1_y,t1_z
        # t2_x,t2_y,t2_z
        # t3_x,t3_y,t3_z
        # position

        ###############################################
        ## Open RMC_POT cfg file
        ##
        tmp = open(cfg_name + ".cfg")
        datfile = tmp.read()
        tmp.close()
        datlines = datfile.split("\n")

        ###############################################
        ## Read Header
        ##
        header = datlines[0]
        comment = datlines[1]
        tmp = datlines[2]
        tmp = datlines[3]

        moves = datlines[4]
        saved = datlines[5]
        tmp = datlines[6]

        t = datlines[7].split()
        natom = t[0]

        t = datlines[8].split()
        ntype = t[0]

        nmoles = datlines[9]
        angles = datlines[10]
        tmp = datlines[11]

        tmp = datlines[12]
        tmp = datlines[13]

        ###############################################
        ## Read Lattice Vector
        ##
        v = datlines[14].split()
        t1_x = float(v[0])  # lattice constant/2
        t1_y = float(v[1])
        t1_z = float(v[2])

        v = datlines[15].split()
        t2_x = float(v[0])
        t2_y = float(v[1])
        t2_z = float(v[2])

        v = datlines[16].split()
        t3_x = float(v[0])
        t3_y = float(v[1])
        t3_z = float(v[2])

        tmp = datlines[17]

        ###############################################
        ## Read Atoms
        ##
        lines = 17
        type = np.zeros((int(ntype) + 1))
        for i in range(int(ntype)):
            lines += 1
            n = datlines[lines].split()
            type[i] = n[0]
            lines += 1
            tmp = datlines[lines]
            lines += 1
            tmp = datlines[lines]
            lines += 1
            tmp = datlines[lines]

        ###############################################
        ## Read Internal Coordinate
        ##
        position = np.zeros((int(natom) + 1, 3))
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
        t1_x = t1_x * 2
        t1_y = t1_y * 2
        t1_z = t1_z * 2

        t2_x = t2_x * 2
        t2_y = t2_y * 2
        t2_z = t2_z * 2

        t3_x = t3_x * 2
        t3_y = t3_y * 2
        t3_z = t3_z * 2

        x_offset = 0.5
        y_offset = 0.5
        z_offset = 0.5
        for i in range(int(natom)):
            position[i, 0] = position[i, 0] / 2 + x_offset
            position[i, 1] = position[i, 1] / 2 + y_offset
            position[i, 2] = position[i, 2] / 2 + z_offset

        ###############################################
        ## OUTPUT for VASP
        vasp = open(vasp_name + ".vasp", "w")

        # --------------------------------------------------
        # [ADDED] VASP elements 情報を解釈
        #   element_info は cfg2poscar の引数
        # --------------------------------------------------
        elements = parse_elements(element_info)

        # ***.vasp へ出力
        print(comment, file=vasp)
        print("1.0", file=vasp)
        print("  %13.9f %13.9f %13.9f" % (t1_x, t1_y, t1_z), file=vasp)
        print("  %13.9f %13.9f %13.9f" % (t2_x, t2_y, t2_z), file=vasp)
        print("  %13.9f %13.9f %13.9f" % (t3_x, t3_y, t3_z), file=vasp)

        # ==================================================
        # [ADDED] VASP5 POSCAR elements 行
        #   lattice vectors の直後
        #   elements が None の場合は何も出力しない
        # ==================================================
        if elements is not None:
            print(make_vasp_elements_line(elements), file=vasp)

        ####
        # print >> vasp, " atoms"
        # print(" atoms", file=vasp)
        ####

        for i in range(int(ntype)):
            print(int(type[i]), file=vasp, end=" ")
        print("", file=vasp)
        print("Direct", file=vasp)

        for i in range(int(natom)):
            print(
                " %13.9f %13.9f %13.9f"
                % (position[i, 0], position[i, 1], position[i, 2]),
                file=vasp,
            )

        vasp.close()
    except Exception as e:
        logger.error(e)
        return False
        # sys.exit(1)

    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logger_ = logging.getLogger("cfg2poscar")
    # logger_ = XLogger(log_level="info", logger_name="cfg2poscar")

    if len(sys.argv) < 2:
        logger_.error("Usage: python cfg2poscar_nonLIB.py cfg_name [vasp_name]")
        sys.exit(1)

    cfg_name_: str = sys.argv[1]

    # vasp_name
    if len(sys.argv) >= 3:
        vasp_name_: str = sys.argv[2]
    else:
        vasp_name_: str = cfg_name_

    # element_info
    if len(sys.argv) >= 4:
        element_info_ = sys.argv[3]
    else:
        element_info_ = None

    if len(sys.argv) > 4:
        logger_.error("Too many arguments")
        sys.exit(1)

    logger_.info(f"cfg_name  = {cfg_name_}")
    logger_.info(f"vasp_name = {vasp_name_}")
    logger_.info(f"element_info = {element_info_}")

    # element_info = ["Li","P","S"]

    ret = cfg2poscar(
        cfg_name=cfg_name_,
        vasp_name=vasp_name_,
        element_info=element_info_,
        logger=logger_,
    )

    if not ret:
        logger_.error("cfg2poscar failed")
        sys.exit(1)
