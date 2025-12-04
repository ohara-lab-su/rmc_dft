#!/usr/bin/env python3

import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog
from rmc_dft.vasp.vasp_outcar import VaspOutcar
from x_logger import XLogger


def check_rmc_and_vasp(
    log_filename: Optional[str] = None,
    outcar_name: Optional[str] = None,
    cfg_name: Optional[str] = None,
    config: Optional[Config] = None,
    logger: Optional[XLogger] = None,
) -> Tuple[bool, bool]:
    """
    VASP と RMC のログを見て、それぞれ正常に終了したかを調べる
    RMCのログは log 単独のログファイル以外に、ジョブファイルに出力された
    ファイルを見ても判断できるようにしている

    Args:
        log_filename (str): aaa.log もしくは任意のログファイル
        outcar_name (str): OUTCAR
        cfg_name (str): aaa
        config (Config): cfg_name を定義しているのでそれを使う時に使う
        logger (XLogger):

    Returns:
        Tuple[bool, bool]: RMC, VASP
    """
    logger = logger or XLogger()
    config = config or Config("config.yaml")

    cfg_name = cfg_name or config.cfg_name
    log_filename = log_filename or f"{cfg_name}.log"
    outcar_name = outcar_name or "OUTCAR"

    # ----------------------------------------
    # RMC 判定
    # ----------------------------------------
    if os.path.exists(log_filename):
        rmc_log = RmcPotLog(
            config=config,
            logger=logger,
            cfg_name=cfg_name,
            log_filename=log_filename,
        )
        # True/False
        rmc_finished: bool = rmc_log.is_finished()
    else:
        logger.error(f"[RMC] log file not found: {log_filename}")
        raise RuntimeError(f"RMC log file not found: {log_filename}")
        # rmc_finished: bool = False

    # ----------------------------------------
    # VASP 判定
    # ----------------------------------------
    if os.path.exists(outcar_name):
        try:
            outcar = VaspOutcar(outcar_name, logger=logger)
            vasp_finished: bool = outcar.is_finalized()
        except Exception:
            vasp_finished = False
    else:
        logger.error(f"[VASP] OUTCAR not found: {outcar_name}")
        vasp_finished: bool = False

    return rmc_finished, vasp_finished
