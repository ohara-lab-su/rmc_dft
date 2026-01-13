#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

rmc_dft 用の VASP 入力ファイル
"""
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
    RmcPotPpcf,
)


def run_dft_init(
    config: Config,
    *,
    logger: XLogger = None,
):
    """
    VASP の KPOINTS/INCAR/POTCAR のスクリプトによる生成
    収束の調整は自動ではちょいと難しいので INIT データ作成くらいしか使えんかも
    """
    if logger is None:
        logger = XLogger()

    # ------------------
    # make KPOINTS
    # ------------------
    if not os.path.exists("KPOINTS"):
        logger.info("== make KPOINTS")
        vasp_kpoints = VaspKpoints(logger=logger)
        vasp_kpoints.set_mode("Monkhorst-Pack")
        vasp_kpoints.set_grid(1, 1, 1)
        vasp_kpoints.set_shift(0, 0, 0)

    # ------------------
    # make POTCAR
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

    # ------------------
    # make INCAR
    # ------------------
    logger.info("== make INCAR")
    vasp_incar = VaspIncar(logger=logger)
    vasp_incar.set_tag("EDIFF", 1e-04)
    vasp_incar.set_tag("EDIFFG", 1e-05)
    vasp_incar.set_tag("ISTART", 0)
    #
    vasp_incar.set_tag("ISMEAR", 0)  # Gussian
    vasp_incar.set_tag("SIGMA", 0.1)
    vasp_incar.set_tag("NELM", 30)
    #
    vasp_incar.set_tag("NSW", 10)
    vasp_incar.set_tag("ISIF", 2)
    vasp_incar.set_tag("IBRION", 2)  # CG
    # vasp_incar.set_tag("IBRION", 3)  # Dampd
    # vasp_incar.set_tag("POTIM", 0.05)  # Dampd scaling
    vasp_incar.set_tag("LREAL", "auto")
    # extra
    vasp_incar.set_tag("ISPIN", 1)
    vasp_incar.set_tag("LORBIT", 11)
    vasp_incar.set_tag("NEDOS", 1500)
    #
    # ==== mixing (大規模アモルファス用・保守的設定) ====
    vasp_incar.set_tag("IMIX", 4)
    vasp_incar.set_tag("INIMIX", 1)
    vasp_incar.set_tag("AMIX", 0.02)
    vasp_incar.set_tag("BMIX", 0.0001)
    vasp_incar.set_tag("MAXMIX", 20)
