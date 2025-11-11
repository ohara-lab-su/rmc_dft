#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from rmc_dft.rmc_pot import RmcPot, RmcPotLog
from rmc_dft.vasp import Vasp, VaspLog
from rmc_dft.config import Config
from rmc_dft.util import poscar2cfg
from rmc_dft.util import ensure_vasp5_format

from x_logger import XLogger


class RmcDft:

    def __init__(
        self,
        rmc_code: Optional[str] = None,  # "RmcPot"
        dft_code: Optional[str] = None,  # "Vasp",
        max_rmc_dft_loop: Optional[int] = None,
        config: Config = Config(),
        logger: XLogger = XLogger(),
        *,
        cfg_name: str = None,
    ):
        """
        RMCとDFTの統合実行クラス。

        Args:
            rmc_code (str): RMCコード名 ("RmcPot", "RmcProfile" など)
            dft_code (str): DFTコード名 ("Vasp", "QE" など)
            max_rmc_dft_loop (int): RMC-DFTループの最大回数
            config (Config): 設定オブジェクト
            logger (XLogger): ロガー（指定がなければ新規作成）
            cfg_name (str): CFGファイルのベース名
        """
        self._logger = logger
        if rmc_code is None:
            rmc_code = config.rmc_code
        if dft_code is None:
            dft_code = config.dft_code
        if cfg_name is None:
            cfg_name = config.cfg_name
        if max_rmc_dft_loop is None:
            max_rmc_dft_loop = config.max_rmc_dft_loop

        self._cfg_name = cfg_name
        self._config = config
        self._max_rmc_dft_loop = max_rmc_dft_loop
        self._dft_code = dft_code
        self._rmc_code = rmc_code

        # --- RMC部分の動的生成 ---
        rmc_log_class = globals().get(f"{rmc_code}Log")
        rmc_class = globals().get(rmc_code)

        if rmc_log_class is None or rmc_class is None:
            raise ValueError(f"Unknown RMC code: {rmc_code}")

        # self._rmc_log = rmc_log_class(
        #     config=self._config,
        #     logger=logger,
        # )
        self._rmc = rmc_class(
            config=self._config,
            logger=logger,
        )

        # --- DFT部分の動的生成 ---
        dft_log_class = globals().get(f"{dft_code}Log")
        dft_class = globals().get(dft_code)

        if dft_log_class is None or dft_class is None:
            raise ValueError(f"Unknown DFT code: {dft_code}")

        # self._dft_log = dft_log_class(
        #     self._config,
        #     logger=logger,
        # )
        self._dft = dft_class(
            config=config,
            logger=logger,
        )

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name: str = cfg_name

    def set_max_rmc_dft_loop(self, max_rmc_dft_loop: int):
        self._max_rmc_dft_loop: int = max_rmc_dft_loop

    def init(self, cfg_name: str):
        # self._dft.init(cfg_name)
        # self._rmc.init(cfg_name)
        pass

    def preprocess(self):
        # self._dft.preprocess(cfg_name)
        self._dft.preprocess()

    def postprocess(self):
        # self._dft.postprocess(cfg_name)
        self._dft.postprocess()

    def run(
        self,
        mode: Optional[str] = "local",
        max_rmc_dft_loop: Optional[int] = None,
        *,
        logger: Optional[XLogger] = XLogger(),
    ):
        """

        Args:
            mode (str):
            max_rmc_dft_loop:
            logger (XLogger):

        Returns:

        """
        self._logger.info(f"== run({mode})")

        if max_rmc_dft_loop is None:
            max_rmc_dft_loop: int = self._max_rmc_dft_loop
        self._config.max_rmc_dft_loop = max_rmc_dft_loop
        self._logger.info(f"max_rmc_dft_loop = {max_rmc_dft_loop}")

        # コンストラクで Config() から cfg_name にとってくる形
        cfg_name: str = self._cfg_name

        digits: int = len(str(max_rmc_dft_loop - 1))

        i = 0
        for i in range(0, max_rmc_dft_loop):

            log_rmc_dir = f"{self._config.rmc_log_dir}{str(i).zfill(digits)}"
            log_dft_dir = f"{self._config.dft_log_dir}{str(i).zfill(digits)}"
            # log_rmc_dir = f"log{str(i).zfill(digits)}"
            # log_dft_dir = f"log{str(i).zfill(digits)}"

            if not os.path.exists(log_dft_dir):
                os.mkdir(log_dft_dir)

            self._logger.info(f"== {self._rmc_code}{str(i)}, log_dir={log_rmc_dir}")
            # self._rmc.run(cfg_name=cfg_name)
            self._rmc.run()
            self._rmc.postprocess(
                log_dir=log_rmc_dir,  # loop での名前変更に対応
                # cfg_name=cfg_name,
                # element_info="label.txt",
            )

            self._logger.info(
                f"== {self._dft_code}{str(i)}, mode={mode}, log_dir={log_dft_dir}"
            )
            self._dft.run(mode=mode)
            self._dft.postprocess(
                log_dir=log_dft_dir,  # loop での名前変更に対応
                # cfg_name=cfg_name,
            )
            self._logger.info("loop end " + str(i))
        self._logger.info("run end")

    @staticmethod
    def poscar2cfg(
        self,
        cfg_name: str,
        posscar_name: Optional[str] = None,
    ) -> bool:
        if not posscar_name:
            posscar_name = f"{cfg_name}.vasp"

        # CFG ファイルを作る
        poscar2cfg(cfg_name=cfg_name)
        return True


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

    _config = Config()
    # rmc_dft = RmcDft(
    #     rmc_code="RmcPot",
    #     dft_code="Vasp",
    #     cfg_name="aaa",
    #     max_rmc_dft_loop=5,
    #     logger=_logger,
    # )

    rmc_dft = RmcDft(
        config=_config,
        logger=_logger,
    )

    # RMCの初期構造を POSCAR から作る
    rmc_dft.init(cfg_name)
    rmc_dft.run()
