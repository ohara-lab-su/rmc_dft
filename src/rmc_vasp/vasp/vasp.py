#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
K.KOBAYASHI
"""
import os
import subprocess
from ase.io import read, write

from config import Config

from rmc_vasp.vasp.util.poscar2cfg import poscar2cfg
from rmc_vasp.vasp.util.xdatcar2poscar import xdatcar2poscar

# from vasp.util.poscar2cfg import poscar2cfg
# from vasp.util.xdatcar2poscar import xdatcar2poscar
# from vasp.vasp_log import vasp_log, vasp_copy
# from .util.poscar2cfg import poscar2cfg
# from .util.xdatcar2poscar import xdatcar2poscar

from x_logger.x_logger import XLogger


class Vasp:

    def __init__(
        self,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = Config.num_procs,
        vasp_bin: str = Config.vasp_bin,
        job_cmd: str = None,
        logger: XLogger = None,
    ):
        """
        Args:
            mpi_cmd (str):
            num_procs (int):
            vasp_bin (str):
            logger (XLogger):  ろがー
        """
        if not logger:
            logger = XLogger()
        self._logger = logger
        self._logger.debug("== create Vasp()")

        self.mpi_cmd = mpi_cmd or "mpirun"  # 規定のMPIコマンド
        self.mpi_flag = mpi_flag or "-np"
        self.num_procs = num_procs or Config.num_procs
        self.vasp_bin = vasp_bin or Config.vasp_bin
        self.job_cmd = job_cmd or ""

    def preprocess(self):
        pass

    def postprocess(self):
        pass

    def set_mpi(
        self,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = None,
    ):
        """MPI設定書き換え"""
        if mpi_cmd:
            self.mpi_cmd = mpi_cmd
        if num_procs:
            self.num_procs = num_procs
        if mpi_flag:
            self.mpi_flag = mpi_flag

    def run(
        self,
        mode: str = "local",
        blocking: bool = True,
    ) -> bool:
        """
        VASP を実行する
        Args:
            mode (str): "local" vasp_bin
                        "mpi" mpi_cmd + mpi_flag + num_procs + vasp_bin
                        "job" job_cmd + vasp_bin
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)
        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"=== run(mode={mode}) ===")

        if mode == "local":
            cmd = [self.vasp_bin]

        elif mode == "mpi":
            # 最初の仕様通り: mpi_cmd + num_procs + vasp_bin
            cmd = [self.mpi_cmd, self.mpi_flag, str(self.num_procs), self.vasp_bin]

        elif mode == "job":
            if not self.job_cmd:
                raise RuntimeError("job_cmd が設定されていません。")
            # job_cmd は launcher として vas_bin の前に置くのみ
            cmd = shlex.split(self.job_cmd) + [self.vasp_bin]

        else:
            raise ValueError(f"未知の mode: {mode}")

        self._logger.info("Executing: " + " ".join(cmd))
        subprocess.run(cmd, check=True)
        return True

        self._logger.info("=== run()")
        # subprocess.run(f"{Config.vasp_bin}", check=True, shell=True)
        subprocess.run(
            ["mpirun", "-np", f"{Config.num_procs}", f"{Config.vasp_bin}"], check=True
        )
        return True

    @staticmethod
    def poscar2cfg(
        cfg_name: str = "aaa",
    ):
        """
        Convert VASP XDATCAR/POSCAR を RMC CFG 形式に変換する

        Args:
            cfg_name: str = "aaa": Name of the output file without extension.

        Returns:
            bool: 正しく終わったデー
        """
        xdatcar2poscar(cfg_name)
        poscar2cfg(cfg_name)
        return True

    @staticmethod
    def add_element_name(
        poscar_name: str = "aaa.vasp",
        element_info: str | None = None,
    ) -> bool:
        """
        VASPファイルの6行目にラベルを設定する

        RMC pot の cfg 形式は元素名がないために、POSCAR 形式に変換したときに困る場合があるので
        VASP5 形式にする( cfg2poscar は element 情報がない VASP4 形式)

        Args:
            poscar_name (str): POSCARファイル名
            element_info (str): element 情報があるファイル名

        Returns:
            bool: True/False
        """
        if element_info is None:
            element_info = "label.txt"

        # element 情報があるファイルを開く
        try:
            with open(element_info, "r") as file:
                label_line = file.readline().strip()
        except FileNotFoundError:
            print(f"File not found.")

        with open(poscar_name, "r") as file:
            lines = file.readlines()
            label_place = 6
        if 1 <= label_place <= len(lines):
            lines[label_place - 1] = label_line + "\n"  # 改行を付けて置換

            # ファイルに上書き保存
            with open(poscar_name, "w") as file:
                file.writelines(lines)
            print(f"{poscar_name} label back.")
        else:
            printf("error: line number out of range.")

        return True

    @staticmethod
    def xdatcar2poscar(cfg_name: str = "aaa"):
        """
        Copy XDATCAR to a new file with the specified name (... .vasp).

        Args:
            cfg_name (str): Name of the new file to create. Without extension.
        Returns:
            bool: 正しく終わったデー
        """

    @staticmethod
    def pdb2poscar(pdb_name: str = "aaa"):
        atoms = read((str + ".pdb"), format="pdb")
        write((str + ".vasp"), atoms, format="vasp", direct=True)
