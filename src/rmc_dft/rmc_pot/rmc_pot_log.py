#!/usr/bin/env python
from x_logger import XLogger


class RmcPotLog:

    def __init__(self, logger: XLogger = None):
        if not logger:
            logger = XLogger()
        self._logger = logger

    @staticmethod
    def collect_result():
        self._logger.info("collect_result")

    @staticmethod
    def backup_result(dst_log_dir: str = "log"):
        """
        Copy RMC log files to the specified directory.

        Args:
            dst_log_dir (str): Directory to copy the log files to.
        """
        import shutil
        import os

        if not os.path.exists(dst_log_dir):
            os.makedirs(dst_log_dir)

        files_to_copy = [
            "grep_khi_RMC.txt",
            "aaa.chi",
            "aaa.cfg",
            "aaa.sq",
            "aaa.dat",
            "aaa.hst",
            "aaa.ppcf",
            "aaa.fit",
            "aaa.pfq",
        ]

        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy(file_name, dst_log_dir)
                self._logger.info(f"Copied {file_name} to {dst_log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")
