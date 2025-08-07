import subprocess
import shutil
from config import Config
from rmc.Rcfg2vasp_nonLIB import conv_cfg2vasp
import os


class UtilRmc:
    """
    Utility class for managing and running local RMC commands.
    And parsing configuration files.
    """

    def run(self, name: str = "local", blocking: bool = True) -> bool:
        """
        RMC を実行する

        Args:
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)

        Returns:
            bool: 正しく終わったデー
        """
#        if name == "local":
#            self.run_local()

        subprocess.run([f"{Config.rmc_bin}", f"{name}"], check=True)

        return True

    def run_asc(self):
        pass

#    def run_local(mystr: str, blocking: bool = True):
#        """
#        It calls a local RMC command.
#
#        :param mystr: RMC input file name without extension (project name).
#        :type mystr: str
#        :param blocking: Blocking mode. Default is True.
#        :type blocking: bool
#        :return: None
#        """
#        subprocess.run([f"{Config.rmc_bin}", f"{mystr}"], check=True)

    @staticmethod
    def u_conv_cfg2vasp(self, cname: str = "aaa"):
        conv_cfg2vasp(cname)
        if os.path.exists("POSCAR"):
            shutil.copy( "POSCAR", "POSCAR.bak")
        shutil.copy( (cname + ".vasp"), "POSCAR")

    def get_norm(self):
        pass

    def get_cfg(self):
        pass

    def get_norm(self):
        pass

    def u_rmc_log(self):
        """
        RMCのログを保存する
        """
        from rmc.rmc_log import rmc_log
        rmc_log()

    def u_rmc_copy(self, log_dir: str = "log"):
        """
        Copy RMC log files to the specified directory.

        Args:
            log_dir (str): Directory to copy the log files to.
        """
        from rmc.rmc_log import rmc_copy
        rmc_copy(log_dir)