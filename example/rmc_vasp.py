#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import shutil

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotPpcf,
)
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")

    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")

    if not os.path.exists("KPOINTS"):
        vasp_kpoints = VaspKpoints(logger=logger)
        vasp_kpoints.set_mode("Monkhorst-Pack")
        vasp_kpoints.set_grid(1, 1, 1)
        vasp_kpoints.set_shift(0, 0, 0)

    if not os.path.exists("POTCAR"):
        vasp_potcar = VaspPotcarBuilder("~/potpaw_PBE.64", logger=logger)
        elements = ["Fe", "Si", "B"]
        vasp_potcar.build(elements, poscar_name="POTCAR")

    vasp_incar = VaspIncar(logger=logger)
    vasp_incar.set_tag("NSW", 1)
    vasp_incar.set_tag("EDIFF", 1e-04)
    vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    vasp_incar.set_tag("ISMEAR", 0)
    vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("NSW", 2)
    vasp_incar.set_tag("NELM", 30)
    vasp_incar.set_tag("IBRION", 2)
    vasp_incar.set_tag("ISIF", 2)
    vasp_incar.set_tag("LREAL", "auto")

    vasp = Vasp(vasp_incar=vasp_incar, config=config, logger=logger)

    # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
    # vasp.poscar2cfg(config.cfg_name)

    # run_mode = "local"

    if not os.path.exists(config.log_vasp_dir):
        os.mkdir(config.log_vasp_dir)

    vasp.run(mode="mpi")
    # vasp.run(mode=run_mode)
    # vasp.postprocess(
    #     log_dir=config.log_vasp_dir,
    #     cfg_name=config.cfg_name,
    # )
    vasp.postprocess()  ## backup, contcar to poscar, poscar2cfg(xxx,cfg)
