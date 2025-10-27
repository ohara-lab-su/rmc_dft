#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
K.KOBAYASHI
"""
import subprocess
from config import Config

from vasp.util import poscar2cfg
from vasp.util import xdatcar2poscar
from vasp.vasp_log import vasp_log, vasp_copy

from x_logger.x_logger import XLogger
import os


class Vasp:

    def __init__(self, logger: XLogger = None):
        """
        Args:
            logger (XLogger):  ろがー
        """
        self._logger = logger
        if logger:
            self._logger.debug("== create Vasp()")

    def run(self, blocking: bool = True) -> bool:
        """
        VASP を実行する
        Args:
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)
        Returns:
            bool: 正しく終わったデー
        """
        self._logger.debug("=== run()")
        #subprocess.run(f"{Config.vasp_bin}", check=True, shell=True)
        subprocess.run(["mpirun", "-np", f"{Config.num_procs}" , f"{Config.vasp_bin}"], check=True)
        return True

    @staticmethod
    def poscar2cfg(self, cfg_name: str = "aaa"):
        """
        Convert VASP XDATCAR/POSCAR to cfg format through XDATCAR.
        Args:
            self:
            cfg_name: str = "aaa": Name of the output file without extension.
        Returns:
            bool: 正しく終わったデー
        """
        xdatcar2poscar(cfg_name)
        poscar2cfg(cfg_name)

    def get_poscar(self):
        self.poscar = fdfadf()

    def get_norm(self):
        pass
        # VASP (self.poscar))
        return None


    def u_label_back(self,cname: str = "aaa.vasp"):
        """
        VASPファイルの6行目にラベルを設定する
        Args:
            cname (str): VASPファイル名
        """
        from vasp.util.label_back import label_back
        label_back(cname)
        
    def u_vasp_log(self):
        """
        VASPのログを保存する
        """
        vasp_log()

    def u_vasp_copy(self, log_dir: str = "log"):
        vasp_copy(log_dir)

    def cp_XDATCAR(self, cname: str = "aaa"):
        """
        Copy XDATCAR to a new file with the specified name (... .vasp).

        Args:
            cname (str): Name of the new file to create. Without extension.
        Returns:
            bool: 正しく終わったデー
        """
        if os.path.exists(cname):
            conv_XDATCAR2vasp(cname)
            return True
        else:
            print(f"skipping cp_XDATCAR")
            return False


