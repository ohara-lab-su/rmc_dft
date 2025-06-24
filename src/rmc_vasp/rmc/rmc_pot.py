import subprocess

from config import Config


class UtilRmc:
    """
    Utility class for managing and running RMC commands.

    This class provides methods to execute local RMC commands, parse
    configuration files. It provides RMC-related tools and configurations.
    """

    def run(self, name: str = "local"):
        if name == "local":
            self.run_local()

    def run_asc(self):
        pass

    def run_local(mystr: str, blocking: bool = True):
        """
        It calls a local RMC command.

        :param mystr: RMC input file name without extension.
        :type mystr: str
        :param blocking: Blocking mode. Default is True.
        :type blocking: bool
        :return: None
        """
        subprocess.run([f"{Config.rmc_bin}", mystr], check=True)

    def get_norm(self):
        pass

    def get_cfg(self):
        pass

    def get_norm(self):
        pass
