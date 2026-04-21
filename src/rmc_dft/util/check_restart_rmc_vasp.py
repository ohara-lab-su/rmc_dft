import os


def check_restart_rmc_vasp(
    *,
    config,
    rmc_log_filename,
    max_loop,
    logger,
):

    # ----------------------------------------------------------
    # logNN_rmc / logNN_dft から状態を判定
    # ----------------------------------------------------------

    def find_last_index(prefix):
        idx = -1
        for name in os.listdir("."):
            if name.startswith(prefix):
                try:
                    n = int(name.split("_")[0].replace("log", ""))
                    if n > idx:
                        idx = n
                except Exception:
                    pass
        return idx

    last_rmc = find_last_index("log")
    last_dft = -1

    for name in os.listdir("."):
        if name.endswith("_dft"):
            try:
                n = int(name.split("_")[0].replace("log", ""))
                if n > last_dft:
                    last_dft = n
            except Exception:
                pass

    logger.info(f"[LOG] last_rmc = {last_rmc}")
    logger.info(f"[LOG] last_dft = {last_dft}")

    # ----------------------------------------------------------
    # 判定
    # ----------------------------------------------------------

    if last_rmc < 0 and last_dft < 0:
        start_loop = 0
        start_mode = "RMC"

    elif last_rmc > last_dft:
        start_loop = last_rmc
        start_mode = "VASP"

    else:
        start_loop = last_dft + 1
        start_mode = "RMC"

    logger.info(f"[RESTART] start_loop={start_loop} start_mode={start_mode}")

    return start_loop, start_mode
