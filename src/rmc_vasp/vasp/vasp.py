import subprocess
from config import Config
from vasp.conv_vasp2cfg import conv_vasp2cfg
from x_logger.x_logger import XLogger
from ase.io import read, write
import os


class UtilVasp:

    def __init__(self, logger: XLogger = None):
        """
        コンストラクター
        Args:
            logger (XLogger):  ろがー
        """
        self._logger = logger
        if logger:
            self._logger.debug("== create UtilVasp()")

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
    def u_conv_vasp2cfg(self, cname: str = "aaa"):
        xfile = 'XDATCAR'
        atoms = read(xfile, index=-1)
        write( (cname + ".vasp"), atoms, format='vasp', direct=True)
        conv_vasp2cfg(cname)

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
        from .label_back import label_back
        label_back(cname)
        
    def u_vasp_log(self):
        """
        VASPのログを保存する
        """
        from vasp.vasp_log import vasp_log
        vasp_log()

    def u_vasp_copy(self, log_dir: str = "log"):
        from vasp.vasp_log import vasp_copy
        vasp_copy(log_dir)

    def cp_XDATCAR(self, cname: str = "aaa"):
        """
        Copy XDATCAR to a new file with the specified name.

        Args:
            cname (str): Name of the new file to create.
        """
        if os.path.exists(cname + ".vasp"):
            write( (cname + ".vasp"), read('XDATCAR', index=-1), format='vasp', direct=True)
        else:
            print(f"skipping cp_XDATCAR")