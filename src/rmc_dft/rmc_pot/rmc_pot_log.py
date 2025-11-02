#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com (2nd version)
K.KOBAYASHI (1st version)
"""
import os
import shutil

from typing import Any, Callable, Optional

from x_logger import XLogger


class RmcPotLog:

    def __init__(
        self,
        cfg_name: str,
        logger: XLogger = None,
    ):
        """
        Args:
            cfg_name (str):
            logger (XLogger):
        """
        if not logger:
            logger = XLogger()
        self._logger = logger

        # default name
        self._cfg_name: str = cfg_name

    def set_cfg_name(self, cfg_name: str) -> None:
        self._cfg_name: str = cfg_name

    def get_cfg_name(self) -> str:
        return self._cfg_name

    def clear(self, cfg_name: str) -> None:
        """
        rmc_pot の出力ファイルを消す

        Args:
            cfg_name (str):

        Returns:

        """
        delete_list = [
            "bcf",
            "calcdat",
            "chi",
            "expt",
            "fit",
            "free",
            "freer",
            "grid",
            "hgm",
            "hst",
            "pfq",
            "ppcf",
            "state",
            "",
        ]

        for extname in delete_list:
            if not os.path.isfile(f"{cfg_name}.{extname}"):
                continue
            try:
                self.remove_file(f"{cfg_name}.{extname}")

                if os.path.isfile(f"{cfg_name}start.grid"):
                    self.remove_file(f"{cfg_name}start.grid")
                if os.path.isfile(f"{cfg_name}start.hgm"):
                    self.remove_file(f"{cfg_name}start.hgm")
            except FileNotFoundError as e:
                self._logger.info(f"[SKIP] {e}")
            except PermissionError:
                self._logger.error(f"[Error] 権限がありません: {cfg_name}.{extname}")

    def remove_file(self, filename: str) -> bool:
        """
        現在の作業ディレクトリ（スクリプト実行フォルダ）にある指定ファイルを削除する。

        Args:
            filename (str): 削除するファイル名（相対/絶対どちらでも可）

        """
        # パスを絶対化（カレントディレクトリ基準）
        path = os.path.abspath(filename)

        if not os.path.isfile(path):
            self._logger.error(f"指定ファイルが存在しません: {path}")
            return False

        os.remove(path)
        self._logger.info(f"delete: {path}")
        return True

    def collect_result(self):
        self._logger.info("collect_result")

    def backup_result(
        self,
        log_dir: str = "log",
        cfg_name: str = "aaa",
    ):
        """
        Copy RMC log files to the specified directory.

        Args:
            log_dir (str): Directory to copy the log files to.
            cfg_name (str): Name of the configuration file.
        """
        self._logger.info("== backup_result")

        if not cfg_name:
            cfg_name = self.cfg_name

        if not os.path.exists(log_dir):
            self._logger.info(f"mkdir {log_dir}")
            os.makedirs(log_dir)

        files_to_copy = [
            "grep_khi_RMC.txt",
            f"{cfg_name}.chi",
            f"{cfg_name}.cfg",
            f"{cfg_name}.sq",
            f"{cfg_name}.dat",
            f"{cfg_name}.hst",
            f"{cfg_name}.ppcf",
            f"{cfg_name}.fit",
            f"{cfg_name}.pfq",
        ]

        for file_name in files_to_copy:
            if os.path.exists(f"{file_name}"):
                shutil.copy(file_name, log_dir)
                self._logger.info(f"Copied {file_name} to {log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")
