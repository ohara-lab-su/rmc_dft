#!/usr/bin/env thon
"""
最新の logNN_ をそのまま見て、次を決める
"""
import os


def check_restart_rmc_vasp(
    config=None,
    rmc_log_filename=None,
    max_loop=None,
    logger=None,
):
    """logger 以外は使わないので None が前提.互換性維持のため"""

    # ----------------------------------------------------------
    # logNN_rmc / logNN_dft から状態を判定
    # ----------------------------------------------------------

    # 見つかった中で最大の番号
    latest_index = -1

    # その番号の種類
    latest_stage = None

    for name in os.listdir("."):
        if not name.startswith("log"):
            continue

        parts = name.split("_")
        if len(parts) != 2:
            continue

        try:
            n = int(parts[0].replace("log", ""))
        except Exception:
            continue

        stage = parts[1]

        if n > latest_index:
            latest_index = n
            latest_stage = stage

    logger.info(f"[LOG] latest_index = {latest_index}")
    logger.info(f"[LOG] latest_stage = {latest_stage}")

    # ----------------------------------------------------------
    # 判定
    # ----------------------------------------------------------

    if latest_index < 0:
        start_loop = 0
        start_mode = "RMC"

    elif latest_stage == "rmc":
        start_loop = latest_index
        start_mode = "VASP"

    else:
        start_loop = latest_index + 1
        start_mode = "RMC"

    logger.info(f"[RESTART] start_loop={start_loop} start_mode={start_mode}")

    return start_loop, start_mode
