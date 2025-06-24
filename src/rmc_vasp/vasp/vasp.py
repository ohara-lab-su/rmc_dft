import subprocess
from config import Config
from vasp.conv_vasp2cfg import conv_vasp2cfg
from x_logger.x_logger import XLogger


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
        subprocess.run(f"{Config.vasp_bin}", check=True)
        return True

    @staticmethod
    def conv_vasp2cfg(self, cname: str = "POSCAR"):
        conv_vasp2cfg(cname)

    def get_poscar(self):
        self.poscar = fdfadf()

    def get_norm(self):
        pass
        # VASP (self.poscar))
        return None
