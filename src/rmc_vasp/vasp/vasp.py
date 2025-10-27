#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
K.KOBAYASHI
"""
import os
import subprocess
from ase.io import read, write

from config import Config

from vasp.util.poscar2cfg import poscar2cfg
from vasp.util.xdatcar2poscar import xdatcar2poscar
from vasp.vasp_log import vasp_log, vasp_copy

from x_logger.x_logger import XLogger


class Vasp:

    def __init__(
        self,
        logger: XLogger = None,
    ):
        """
        Args:
            logger (XLogger):  ろがー
        """
        self._logger = logger
        if logger:
            self._logger.debug("== create Vasp()")

    def run(
        self,
        blocking: bool = True,
    ) -> bool:
        """
        VASP を実行する
        Args:
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)
        Returns:
            bool: 正しく終わったデー
        """
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
