#!/usr/bin/env python
import os
import subprocess
import shutil

from rmc_dft.config import Config
from rmc_dft.rmc_pot.util.cfg2poscar import cfg2poscar

from x_logger import XLogger


class RmcPot:
    """
    Utility class for managing and running local RMC commands.
    And parsing configuration files.
    """

    def __init__(
        self,
        rmc_log,
        cfg_name: str,
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

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name = cfg_name

    def preprocess(self):
        pass

    def postprocess(
        self,
        log_dir: str = "log",
        cfg_name: str | None = None,
    ):
        """

        Args:
            log_dir:
            cfg_name:

        Returns:

        """
        if not cfg_name:
            cfg_name = self._cfg_name

        # RMC_POT 結果保存
        self._rmc_log.collect_result()
        self._rmc_log.backup_result(log_dir)

        # RMC_POT 結果から、POSCAR 作成
        self._logger.info(f"== cfg2poscar({cfg_name})")
        self._rmc.cfg2poscar(cfg_name)
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

    def run_asc(self):
        pass

    #    def run_local(mystr: str, blocking: bool = True):
    #        """
    #        It calls a local RMC command.
    #
    #        :param mystr: RMC input_poscar file name without extension (project name).
    #        :type mystr: str
    #        :param blocking: Blocking mode. Default is True.
    #        :type blocking: bool
    #        :return: None
    #        """
    #        subprocess.run([f"{Config.rmc_bin}", f"{mystr}"], check=True)

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
