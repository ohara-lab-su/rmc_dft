#!/usr/bin/env python
import os
from typing import Any, Dict, List, Optional

from rmc_dft.vasp.vasp import Vasp
from rmc_dft.vasp.vasp_log import VaspLog
from rmc_dft.rmc_pot.rmc_pot import RmcPot
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog
from rmc_dft.config import Config

from x_logger import XLogger


class RmcDft:

    def __init__(
        self,
        rmc_code: str = "RmcPot",
        dft_code: str = "Vasp",
        cfg_name: str = "aaa",
        max_loop: int = 10,
        config: Config = Config(),
        logger: XLogger = None,
    ):
        """
        RMCとDFTの統合実行クラス。

        Args:
            rmc_code (str): RMCコード名 ("RmcPot", "RmcProfile" など)
            dft_code (str): DFTコード名 ("Vasp", "QE" など)
            cfg_name (str): CFGファイルのベース名
            max_loop (int): RMC-DFTループの最大回数
            config (Config): 設定オブジェクト
            logger (XLogger): ロガー（指定がなければ新規作成）
        """
        if logger is None:
            logger = XLogger()

        self._logger = logger
        self._cfg_name = cfg_name
        self._config = config
        self._max_loop = max_loop

        # --- DFT部分の動的生成 ---
        dft_log_class = globals().get(f"{dft_code}Log")
        dft_class = globals().get(dft_code)

        if dft_log_class is None or dft_class is None:
            raise ValueError(f"Unknown DFT code: {dft_code}")

        self._dft_log = dft_log_class(logger=logger)
        self._dft = dft_class(self._dft_log, cfg_name, logger=logger)

        # --- RMC部分の動的生成 ---
        rmc_log_class = globals().get(f"{rmc_code}Log")
        rmc_class = globals().get(rmc_code)

        if rmc_log_class is None or rmc_class is None:
            raise ValueError(f"Unknown RMC code: {rmc_code}")

        self._rmc_log = rmc_log_class(logger=logger)
        self._rmc = rmc_class(self._rmc_log, cfg_name, logger=logger)

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name: str = cfg_name

    def set_max_loop(self, max_loop: int):
        self._max_loop: int = max_loop

    def init(self, cfg_name: str):
        self._dft.init(cfg_name)
        self._rmc.init(cfg_name)

    def preprocess(self, cfg_name: str):
        self._dft.preprocess(cfg_name)

    def postprocess(self, cfg_name: str):
        self._dft.postprocess(cfg_name)

    def run(
        self,
        max_loop: int | None = None,
        mode: str = "local",
        cfg_name: str = None,
        logger: XLogger = None,
    ):
        if not max_loop:
            max_loop: int = self._max_loop

        if not cfg_name:
            cfg_name: str = self._cfg_name

        # 初期構造として POSCAR を用いた場合、それをベースに CFG ファイルを作成する
        self._dft.initprocess(cfg_name)

        digits: int = len(str(max_loop - 1))

        i = 0
        for i in range(0, max_loop):

            log_dir = f"log{str(i).zfill(digits)}"

            if not os.path.exists(log_dir):
                os.mkdir(log_dir)

            self._logger.info("== rmc" + str(i))
            self._rmc.run(cfg_name)

            self._logger.info("== vasp" + str(i))
            self._dft.run(mode=mode)
            # self._dft.run(mode="job", job_cmd="qsub job_hpcs2024_node2.sh")
            # self._dft.run(mode="test")
            self._logger.info("loop end " + str(i))


globals().update(
    {
        "RmcPot": RmcPot,
        "RmcPotLog": RmcPotLog,
        "Vasp": Vasp,
        "VaspLog": VaspLog,
    }
)


if __name__ == "__main__":
    _logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")

    rmc_dft = RmcDft(
        rmc_code="RmcPot",
        dft_code="Vasp",
        cfg_name="aaa",
        max_loop=5,
        logger=_logger,
    )

    # RMCの初期構造を POSCAR から作る
    rmc_dft.init(cfg_name)
    rmc_dft.run()
