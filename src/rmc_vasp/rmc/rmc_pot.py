import subprocess

from config import Config


class UtilRmc:

    def run(self, name: str = "local"):
        if name == "local":
            self.run_local()

    def run_asc(self):
        pass

    def run_local(mystr: str, blocking: bool = True):
        subprocess.run([f"{Config.rmc_bin}", mystr], check=True)

    def get_norm(self):
        pass

    def get_cfg(self):
        pass

    def get_norm(self):
        pass