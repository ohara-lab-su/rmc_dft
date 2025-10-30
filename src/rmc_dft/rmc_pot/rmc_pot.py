#!/usr/bin/env python
import os
import subprocess
import shutil
from typing import Any, Dict, List, Optional

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog
from rmc_dft.rmc_pot.util.cfg2poscar import cfg2poscar

from x_logger import XLogger


class RmcPot:
    """
    Utility class for managing and running local RMC commands.
    And parsing configuration files.
    """

    def __init__(
        self,
        rmc_log: RmcPotLog = None,
        cfg_name: str = "aaa",
        logger: XLogger = None,
    ):
        """

        Args:
            rmc_log: RMC_POT のログ処理用のインスタンス
            cfg_name (str): cfg-filename
            logger (XLogger):
        """
        self._rmc_log = rmc_log
        self._cfg_name = cfg_name

        if not logger:
            logger = XLogger()
        self._logger = logger

        # rmc_log に cfg_name をセットする
        if self._rmc_log:
            self._logger.info(f"== rmc_log.set_cfg_name({cfg_name})")
            self._rmc_log.set_cfg_name(cfg_name)

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name = cfg_name
        # rmc_log に cfg_name をセットする
        if self._rmc_log:
            self._rmc_log.set_cfg_name(cfg_name)

    def init(self, cfg_name: str):
        """
        RMC-DFT は RMC から始める。しかし構造ファイルは VASP ベースから
        スタートするので、rmc_pot 側での初期化はこのルーチンでは明示的にしない
        互換のフェイクI/F

        Args:
            cfg_name:

        Returns:

        """
        pass

    def preprocess(self):
        pass

    def postprocess(
        self,
        log_dir: str = "log",
        cfg_name: str | None = None,
    ):
        """
        RMC 後に DFT を動かすにあたっての
        cfg --> poscar 変換

        他のコードを使っても基本は poscar 経由を念頭におくので
        postprocess は poscar にしておけば他のライブラリを使っても
        齟齬は出ない

        Args:
            log_dir (str):
            cfg_name (str): cfg_name と vasp_name は等しいとする

        Returns:

        """
        self._logger.info(f"== postprocess()")

        if not cfg_name:
            cfg_name = self._cfg_name
        self._logger.info(f"cfg_name = {cfg_name}")

        # RMC_POT 結果保存
        self._rmc_log.collect_result()
        self._rmc_log.backup_result(
            log_dir=log_dir,
            cfg_name=cfg_name,
        )

        # RMC_POT 結果から、POSCAR 作成
        self._logger.info(f"== cfg2poscar({cfg_name})")
        self.cfg2poscar(cfg_name)
        pass

    @staticmethod
    def run(
        cfg_name: str,
        blocking: bool = True,
    ) -> bool:
        """
        RMC を実行する

        Args:
            cfg_name (str):
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)

        Returns:
            bool: 正しく終わったデー
        """
        subprocess.run([f"{Config.rmc_bin}", f"{cfg_name}"], check=True)
        return True

    #
    # Utilities
    #

    @staticmethod
    def cfg2poscar(cfg_name: str | None = None):
        if not cfg_name:
            cfg_name = self._cfg_name

        cfg2poscar(cfg_name)
        if os.path.exists("POSCAR"):
            shutil.copy("POSCAR", "POSCAR.bak")
        shutil.copy((cfg_name + ".vasp"), "POSCAR")
