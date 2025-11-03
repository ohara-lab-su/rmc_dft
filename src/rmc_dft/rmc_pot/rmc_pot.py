#!/usr/bin/env python
"""
K.NAKADA, Kengo.nakada@gmail.com (1st, 3rd version)
K.KOBAYASHI (2nd version)
"""
import os
from typing import Any, Dict, List, Optional
import subprocess
import shutil

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_dat import RmcPotDat
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog

from rmc_dft.rmc_pot.util.cfg2poscar import cfg2poscar
from rmc_dft.util import ensure_vasp5_format

from x_logger import XLogger


class RmcPot:
    """
    Utility class for managing and running local RMC commands.
    And parsing configuration files.
    """

    def __init__(
        self,
        rmc_log: RmcPotLog = None,
        rmc_dat: RmcPotDat = None,
        cfg_name: str = "aaa",
        logger: XLogger = None,
    ):
        """

        Args:
            rmc_log: RMC_POT のログ処理用のインスタンス
            rmc_dat: RMC_POT のDAT処理用のインスタンス
            cfg_name (str): cfg-filename
            logger (XLogger):
        """
        if not logger:
            logger = XLogger()
        self._logger = logger

        # aaa.dat ファイルなどの CFG ファイル名 prefix
        self._cfg_name = cfg_name

        # .dat ファイル処理 instance
        if rmc_dat is None:
            rmc_dat = RmcPotDat(
                logger=logger,
                dat_name=cfg_name,
                auto_write=True,
            )
        self._rmc_dat = rmc_dat
        if self._rmc_dat:
            self._logger.info(f"== rmc_pot_dat()")

        # RMC 出力ファイル処理
        self._rmc_log = rmc_log
        if self._rmc_log:
            self._logger.info(f"== rmc_log.set_cfg_name({cfg_name})")
            self._rmc_log.set_cfg_name(cfg_name)

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name = cfg_name
        # rmc_log に cfg_name をセットする
        if self._rmc_log:
            self._rmc_log.set_cfg_name(cfg_name)

    # --------------------
    # 互換 I/F
    # --------------------
    def set_tag(self, tag_name: str, *args) -> None:
        """
        RmcPotData 側の set_xxx メソッドを呼び出す互換I/F。

        Args:
            tag_name (str): タグ名（例: 'cutoffs', 'potential'）
            *args: set_xxx に渡す引数
        """
        method_name = f"set_{tag_name.lower()}"
        method = getattr(self._rmc_dat, method_name, None)
        if method is None:
            raise AttributeError(
                f"RmcPotData に '{method_name}' が定義されていません。"
            )
        method(*args)

    def get_tag(self, tag_name: str, *args):
        """
        RmcPotData 側の get_xxx メソッドを呼び出す互換I/F。

        Args:
            tag_name (str): タグ名（例: 'cutoffs', 'potential'）
            *args: get_xxx に渡す引数（必要な場合）

        Returns:
            Any: 対応する get_xxx の戻り値
        """
        method_name = f"get_{tag_name.lower()}"
        method = getattr(self._rmc_dat, method_name, None)
        if method is None:
            raise AttributeError(
                f"RmcPotData に '{method_name}' が定義されていません。"
            )
        return method(*args)

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
        """
        このコードを動かすときは RMC_POT 入力が揃って意前提とする
        """
        self._logger.info("== preprocess()")

    def postprocess(
        self,
        log_dir: str = "log_rmc",
        cfg_name: str | None = None,
        element_info: str | list | None = None,
    ) -> bool:
        """
        後処理

        RMC 後に DFT を動かすにあたっての
        1) DATA-collect
        2) BACKUP
        3) CFG --> POSCAR (VASP4) 変換 --> VASP5 変換

        他のコードを使っても基本は poscar 経由を念頭におくので
        postprocess は poscar にしておけば他のライブラリを使っても
        齟齬は出ない

        Args:
            log_dir (str):
            cfg_name (str): cfg_name と vasp_name は等しいとする
            element_info (str | list): 元素情報

        Returns:
            bool:

        """
        self._logger.info(f"== postprocess()")

        if not cfg_name:
            cfg_name = self._cfg_name
        self._logger.info(f"cfg_name = {cfg_name}")

        if not element_info:
            element_info = "label.txt"

        # DATA-collect
        self._rmc_log.collect_result()

        # BACKUP-RESULT
        self._rmc_log.backup_result(
            log_dir=log_dir,
            cfg_name=cfg_name,
        )

        # RMC_POT 結果から、POSCAR (VASP4 style) 作成
        # --> xxx.vasp
        self._logger.info(f"== cfg2poscar({cfg_name}.vasp)")
        self.cfg2poscar(cfg_name=cfg_name, vasp_name=cfg_name)

        # VASP4 --> VASP5
        self._logger.info(f"== encure vasp5 format ({cfg_name}.vasp)")
        self.ensure_vasp5_format(
            poscar_name=f"{cfg_name}.vasp",
            element_info="label.txt",
        )

        # xxx.vasp --> POSCAR
        shutil.copy(f"{cfg_name}.vasp", "POSCAR")

        return True

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
    def ensure_vasp5_format(
        poscar_name: str,
        element_info: str | None = None,
        logger: XLogger = None,
    ) -> bool:
        if not logger:
            logger = XLogger()
        return ensure_vasp5_format(poscar_name, element_info, logger=logger)

    def cfg2poscar(
        self,
        cfg_name: str | None = None,
        vasp_name: str = None,
    ) -> bool:
        """

        Args:
            cfg_name (str):  xxx.cfg
            vasp_name (str):  xxx.vasp

        Returns:

        """
        if not cfg_name:
            cfg_name = self._cfg_name

        if not vasp_name:
            vasp_name = cfg_name
        self._logger.info(f"cfg_name = {cfg_name}")
        self._logger.info(f"vasp_name = {cfg_name}")

        cfg2poscar(cfg_name=cfg_name, vasp_name=vasp_name)

        # POSCAR を後に上書きしちゃうので保存しておく
        if os.path.exists("POSCAR"):
            shutil.copy("POSCAR", "POSCAR.bak")

        # xxx.vasp を POSCAR の名前でもコピーしておく
        shutil.copy((cfg_name + ".vasp"), "POSCAR")

        return True
