#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC-DFT のUIクラスを使わずに直接 rmc_pot, vasp 関係のクラスを起動して
RMC-VASP を構成する sample script
"""
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
)
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    config = Config("config.yml")

    # 初期POSCAR 作成
    shutil.copy(f"POSCAR0", "POSCAR")

    # POSCAR to CFG (rmc用のCFG変換)
    # cfg_name = "aaa"
    # vasp_name = "aaa"
    cfg_name = config.cfg_name
    vasp_name = config.vasp_name
    log_vasp_dir = config.dft_log_dir

    # vasp_log = VaspLog(logger=logger)
    # vasp = Vasp(
    #     vasp_log=vasp_log,
    #     config=config,
    #     logger=logger,
    # )

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
    # vasp.poscar2cfg(cfg_name)

    # run_mode = "local"

    if not os.path.exists(log_vasp_dir):
        os.mkdir(log_vasp_dir)

    vasp.run(mode="mpi")
    # vasp.run(mode=run_mode)
    # vasp.postprocess(
    #     log_dir=log_vasp_dir,
    #     cfg_name=cfg_name,
    # )
    vasp.postprocess()  ## backup, contcar to poscar, poscar2cfg(xxx,cfg)
