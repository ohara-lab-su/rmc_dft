#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

rmc_dft 用の VASP 入力ファイル
"""

import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import subprocess

from rmc_dft import Config
from x_logger import XLogger

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspOutcar,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotHst,
    RmcPotPpcf,
)

# ---------------------------------------------------------
# rmc_vasp_init_N.py として使用した場合:
# True  : 次の VASP run でもこの init_N.py を再読込して使用する
# False : 次の VASP run では通常の rmc_vasp_init.py に戻る
CONTINUE_NUMBERED_INIT = False
# ---------------------------------------------------------


def run_vasp_init_safe(
    config: Config,
    *,
    vasp_incar: Optional[VaspIncar] = None,
    vasp_kpoints: Optional[VaspKpoints] = None,
    logger: Optional[Any] = None,
):
    """
    VASP の KPOINTS/INCAR/POTCAR のスクリプトによる生成
    収束の調整は自動ではちょいと難しいので INIT データ作成くらいしか使えんかも
    """
    if logger is None:
        logger = XLogger()

    # ------------------
    # make KPOINTS
    # 存在しないなら作る
    # ------------------
    if not os.path.exists("KPOINTS"):
        logger.info("== make KPOINTS")

        if vasp_kpoints is None:
            vasp_kpoints = VaspKpoints(config=config, logger=logger)

        vasp_kpoints.set_mode("Monkhorst-Pack")
        vasp_kpoints.set_grid(1, 1, 1)
        vasp_kpoints.set_shift(0, 0, 0)

    # ------------------
    # make POTCAR
    # 存在しないなら作る
    # ------------------
    if not os.path.exists("POTCAR"):
        logger.info("== make POTCAR")
        vasp_potcar = VaspPotcarBuilder("~/potpaw_PBE.64", logger=logger)
        # elements = ["Fe", "Si", "B"]
        elements = config.element_info

        if isinstance(elements, str):  # もし、label.txt とかの str ならば、
            with open(elements) as f:
                elements = f.readline().strip().split()

        vasp_potcar.build(elements, poscar_name="POTCAR")

        # 富岳対応 (キャッシュ対策)
        subprocess.run(["sleep", "10"], check=True)
        subprocess.run(["ls", "-la", "./"], check=True)

    # ------------------
    # make INCAR
    # ------------------
    if vasp_incar is None:
        vasp_incar = VaspIncar(config=config, logger=logger)

    logger.info("== make INCAR")
    vasp_incar.set_tag("EDIFF", 1e-04)
    # vasp_incar.set_tag("EDIFFG", 1e-03)
    vasp_incar.set_tag("EDIFFG", 1e-03)
    # vasp_incar.set_tag("EDIFF", 1e-06)
    # vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    #
    vasp_incar.set_tag("ISMEAR", 0)  # 0:Gaussian
    # vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("SIGMA", 0.05)
    vasp_incar.set_tag("NELM", 30)
    # vasp_incar.set_tag("NELM", 300)
    #
    # vasp_incar.set_tag("NSW", 10)
    vasp_incar.set_tag("NSW", 30)
    # vasp_incar.set_tag("NSW", 300)

    vasp_incar.set_tag("ISIF", 2)

    # vasp_incar.set_tag("IBRION", 2)  # CG
    vasp_incar.set_tag("IBRION", 1)  # RMM-DIIS
    # vasp_incar.set_tag("IBRION", 3)  # Dampd

    vasp_incar.set_tag("POTIM", 0.05)  # Dampd scaling

    vasp_incar.set_tag("ISYM", 0)

    vasp_incar.set_tag("LREAL", "auto")

    # extra
    vasp_incar.set_tag("ISPIN", 1)
    vasp_incar.set_tag("LORBIT", 11)
    vasp_incar.set_tag("NEDOS", 1500)

    vasp_incar.set_tag("ALGO", "Normal")

    # ==== 主に富岳向け(a64)並列パラメータ 1core = 4CMG = 48MPI rank
    vasp_incar.set_tag("KPAR", 1)  # K点並列
    vasp_incar.set_tag("NCORE", 12)  # MPI ランク
    vasp_incar.set_tag("NSIM", 4)  # バンド並列Gr

    # ==== mixing (大規模アモルファス用・保守的設定) ====
    # vasp_incar.set_tag("IMIX", 4)
    # vasp_incar.set_tag("INIMIX", 1)
    # vasp_incar.set_tag("AMIX", 0.02)
    # vasp_incar.set_tag("BMIX", 0.0001)
    # vasp_incar.set_tag("MAXMIX", 20)


if __name__ == "__main__":
    config_ = Config("config.yml")
    logger_ = XLogger(log_level="debug", logger_name="rmc_run")
    vasp_incar_ = VaspIncar(logger=logger_)

    run_vasp_init(
        config=config_,
        vasp_incar=vasp_incar_,
        logger=logger_,
    )
