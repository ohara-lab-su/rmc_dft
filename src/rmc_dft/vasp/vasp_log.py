#!/usr/bin/env python
import os
import sys

import glob
from pathlib import Path

from x_logger import XLogger


class VaspLog:
    """
    VASP の出力ファイルを計算後に整理・解析するクラス
    """

    def __init__(self, logger: XLogger = None):
        if not logger:
            logger = XLogger()
        self._logger = logger

    # grep on python
    @staticmethod
    def get_E0(
        input_filename: str = "OSZICAR",
        output_filename: str = "grep_E0_OSZICAR.txt",
        key: str = "E0",
    ):
        """
        OSZICAR から E0 を取り出して、ファイル保存する
        (廃止予定)

        Args:
            input_filename:
            output_filename:
            key:

        Returns:

        """
        input_file = "OSZICAR"
        output_file = "grep_E0_OSZICAR.txt"
        key = "E0"

        with open(output_file, "w") as outfile:
            with open(input_file, "r") as f:
                for line in f.readlines():
                    if key in line:
                        print(line)
                        outfile.writelines(line)

    def collect_result(self):
        """
        VASPのログからひつようなじょうほうをとりだして、保存する
        This function is used to grep energy from OUTCAR file.
        """
        self.get_E0()
        self._logger.info("grep energy from OUTCAR file finished.")

    def backup_result(
        self,
        dst_log_dir: str = "log",
    ):
        """
        Copy VASP log files to the specified directory.

        Args:
            dst_log_dir (str): Directory to copy the log files to.
        """
        import shutil
        import os

        if not os.path.exists(dst_log_dir):
            os.makedirs(dst_log_dir)

        files_to_copy = [
            "grep_E0_OSZICAR.txt",
            "OUTCAR",
            "OSZICAR",
            "vasprun.xml",
            "XDATCAR",
            "CONTCAR",
            "POSCAR",
            "KPOINTS",
        ]

        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy(file_name, dst_log_dir)
                self._logger.info(f"Copied {file_name} to {dst_log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")

    def remove_file(self, filename: str) -> None:
        """存在するファイルを削除"""
        if os.path.exists(filename):
            os.remove(filename)
            self._logger.info(f"removed: {filename}")

    def remove_pattern(self, pattern: str) -> None:
        """ワイルドカードパターンで一致するファイルを削除"""
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                self._logger.info(f"removed: {f}")
            except FileNotFoundError:
                pass

    def clean(self, suffixes: list[str]) -> None:
        """
        cleanvasp.py
        cleanvasp.py _1
        cleanvasp.py _1 _2 _3

        Args:
            suffixes:

        Returns:

        """
        base_files = [
            "AECCAR0",
            "AECCAR1",
            "AECCAR2",
            "LOCPOT",
            "CHG",
            "CHGCAR",
            "CHGCAR_sum",
            "PARCHG",
            "CONTCAR",
            "DOSCAR",
            "EIGENVAL",
            "IBZKPT",
            "OSZICAR",
            "PCDAT",
            "WAVECAR",
            "XDATCAR",
            "PROCAR",
            "OUTCAR",
            "TMPCAR",
            "OUTPAR",
            "ELFCAR",
            "REPORT",
            "vasprun.xml",
            "vaspout.h5",
            "PROJCAR",
            "LOCPROJ",
        ]

        # 共通ワイルドカード削除（lobster, wannier90, job system）
        patterns = [
            "p4vasp.log",
            "*.lobster",
            "lobsterout",
            "*.werr",
            "*.wout",
            "wannier90.chk",
            "wannier90.amn",
            "wannier90.eig",
            "wannier90.mmn",
            "wannier90_*.xsf",
            "wannier90_centres.xyz",
            "UNK*.1",
            "UNK*.2",
            "LSF_*",
            "PBS_*",
            "tmp.*",
        ]

        if not suffixes:
            # 引数なし：通常ファイル削除
            for f in base_files:
                remove_file(f)
            for p in patterns:
                remove_pattern(p)

        else:
            # 引数あり：サフィックス付きファイル削除
            for suf in suffixes:
                for f in base_files:
                    remove_file(f.lower() + suf)
                    remove_file(f.lower() + suf + ".gz")
                    remove_file(f.upper() + suf)
                    remove_file(f.upper() + suf + ".gz")

                # 特殊ケース
                remove_file(f"vasprun{suf}.xml")
                remove_file(f"vaspout{suf}.h5")
                remove_file(f"vasprun{suf}.xml.gz")
                remove_file(f"vaspout{suf}.h5.gz")


if __name__ == "__main__":
    vasp_log = VaspLog()
    vasp_log.collect_result()
