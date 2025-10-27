#!/usr/bin/env python
from x_logger import XLogger


class VaspLog:

    def __init__(self, logger: XLogger = None):
        if logger:
            logger = XLogger()
        self._logger = logger

    # grep on python
    @staticmethod
    def grep_energy(
        input_filename: str = "OSZICAR",
        output_filename: str = "grep_E0_OSZICAR.txt",
        key: str = "E0",
    ):
        input_file = "OSZICAR"
        output_file = "grep_E0_OSZICAR.txt"
        key = "E0"

        with open(output_file, "w") as outfile:
            with open(input_file, "r") as f:
                for line in f.readlines():
                    if key in line:
                        print(line)
                        outfile.writelines(line)

    def vasp_log(self):
        """
        VASPのログを保存する
        This function is used to grep energy from OUTCAR file.
        """
        self.grep_energy()
        print("grep energy from OUTCAR file finished.")

    def vasp_copy(
        self,
        log_dir: str = "log",
    ):
        """
        Copy VASP log files to the specified directory.

        Args:
            log_dir (str): Directory to copy the log files to.
        """
        import shutil
        import os

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

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
                shutil.copy(file_name, log_dir)
                self._logger.info(f"Copied {file_name} to {log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")
