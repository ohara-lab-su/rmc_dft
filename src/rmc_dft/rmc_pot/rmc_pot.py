#!/usr/bin/env python
"""
K.NAKADA, Kengo.nakada@gmail.com (1st, 3rd version)
K.KOBAYASHI (2nd version)
"""
import os
import sys
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
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
        *,
        rmc_log: RmcPotLog = None,  # instance
        rmc_dat: RmcPotDat = None,  # instance
        config: Config = Config(),  # instance
        logger: Optional[XLogger] = XLogger(),  # instance
        cfg_name: str = None,
    ) -> None:
        """
        config インスタンスを与えると、cfg_name はいらない

        Args:
            rmc_log: RMC_POT のログ処理用のインスタンス
            rmc_dat: RMC_POT のDAT処理用のインスタンス
            config (Config): 全てのインスタンスが同じ Config()
            logger (XLogger): 全てインスタンスが同じ XLogger()
            cfg_name (str): cfg-filename
        """
        self._logger = logger
        self._config = config

        if cfg_name is None:
            cfg_name: str = config.cfg_name

        # aaa.dat ファイルなどの CFG ファイル名 prefix
        self._cfg_name = cfg_name

        auto_write = config.auto_write

        # RMC 出力ファイル処理 instance
        if rmc_log is None:
            rmc_log = RmcPotLog(config=config, logger=logger)

        self._rmc_log = rmc_log
        self._logger.info(f"== rmc_log.set_cfg_name({cfg_name})")
        self._rmc_log.set_cfg_name(cfg_name)

        # .dat ファイル処理 instance
        if rmc_dat is None:
            rmc_dat = RmcPotDat(
                cfg_name=cfg_name,  # cfg_name = aaa.dat/aaa.cfg
                auto_write=auto_write,
                config=config,
                logger=logger,
            )

        self._rmc_dat = rmc_dat
        self._logger.info(f"== rmc_pot_dat()")

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

    def preprocess(self) -> None:
        """
        このコードを動かすときは RMC_POT 入力が揃っている前提とする
        1. 実験プロファイル（例: fesi04_smbt-rmc.txt）が実行カレントに存在しないときは止める
        2. label.txt が存在しないと止める

        *) 初期の構造変換は誤解が起きやすいので RmcPot クラスでは Preprocess() で勝手にやらないようにする
        """
        self._logger.info("== preprocess()")

        # 実行カレント（実行したPythonのパス）を基準にする
        work_dir = os.getcwd()
        self._logger.info(f"work_dir   = {work_dir}")

        # Config から elemento_info を取得
        label_name = self._config.element_info

        # RmcPotDat から実験データのファイル名を取得
        filename = self._rmc_dat.get_exp_filename()

        for name in [label_name, filename]:
            name_path = os.path.join(work_dir, name)
            self._logger.info(f"filename = {name}")
            self._logger.info(f"target_filename_path = {name_path}")
            self._logger.info(f".")

            # ファイルの存在チェック
            if not os.path.exists(name_path):
                self._logger.error(f"**Error**: {name_path} が見つかりません。")
                sys.exit(-1)

    def postprocess(
        self,
        log_dir: Optional[str] = None,
        cfg_name: Optional[str] = None,
        element_info: Union[str, list, None] = None,
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
            log_dir (str): RMC用の log_dir
            cfg_name (str): cfg_name と vasp_name は等しいとする(デフォルトはコンストラの引数での cfg_name)
            element_info (str | list): 元素情報

        Returns:
            bool:

        """
        self._logger.info(f"== postprocess()")

        if log_dir is None:
            log_dir = self._config.rmc_log_dir
        self._logger.info(f"log_dir(RMC) = {log_dir}")

        if cfg_name is None:
            cfg_name = self._cfg_name
        self._logger.info(f"cfg_name = {cfg_name}")

        if element_info is None:
            # element_info = "label.txt"
            element_info = self._config.element_info

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
        self._logger.info(f"== ensure vasp5 format ({cfg_name}.vasp)")
        self.ensure_vasp5_format(
            poscar_name=f"{cfg_name}.vasp",
            element_info="label.txt",
        )

        # xxx.vasp --> POSCAR
        shutil.copy(f"{cfg_name}.vasp", "POSCAR")

        return True

    def run(
        self,
        cfg_name: Optional[str] = None,
        blocking: Optional[bool] = True,
    ) -> bool:
        """
        RMC を実行する

        Args:
            cfg_name (str):
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)

        Returns:
            bool: 正しく終わったデー
        """
        if cfg_name is None:
            cfg_name = self._cfg_name
        self._logger.info(f"== run(cfg_name={cfg_name})")

        try:
            # 2025 あたりの rmc_pot
            # subprocess.run([f"{self._config.rmc_bin}", f"{cfg_name}"], check=True)
            # 2014 あたりの rmc_pot
            subprocess.run([f"{self._config.rmc_bin}", f"{cfg_name}", "y"], check=True)
            # 2014 あたりの書式で 2025 でも動く
        except subprocess.CalledProcessError as e:
            self._logger.error(f"**Error**: {e}")
            sys.exit(-1)

        return True

    #
    # Utilities
    #
    @staticmethod
    def ensure_vasp5_format(
        poscar_name: str,
        element_info: Optional[str] = None,
        logger: XLogger = XLogger(),
    ) -> bool:
        return ensure_vasp5_format(poscar_name, element_info, logger=logger)

    def cfg2poscar(
        self,
        cfg_name: Optional[str] = None,
        vasp_name: Optional[str] = None,
    ) -> bool:
        """
        Args:
            cfg_name (str):  xxx.cfg（拡張子なしのベース名を想定）
            vasp_name (str): xxx.vasp（拡張子なしのベース名を想定）
        """
        if cfg_name is None:
            cfg_name = self._cfg_name
        if vasp_name is None:
            vasp_name = cfg_name

        self._logger.info(f"cfg_name  = {cfg_name}")
        self._logger.info(f"vasp_name = {vasp_name}")

        cfg2poscar(cfg_name=cfg_name, vasp_name=vasp_name)

        # POSCAR を後に上書きしちゃうので保存しておく
        if os.path.exists("POSCAR"):
            shutil.copy("POSCAR", "POSCAR.bak")

        # xxx.vasp を POSCAR 名でもコピー
        shutil.copy((vasp_name + ".vasp"), "POSCAR")
        return True
