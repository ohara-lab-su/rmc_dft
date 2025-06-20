import subprocess
from config import Config
from vasp.conv_vasp2cfg import conv_vasp2cfg


class UtilVasp:

    def __init__(self):
        self.a = "b"

    def run(self, blocking: bool = True):
        subprocess.run(f"{Config.vasp_bin}", check=True)
        print(self.a)

    def conv_vasp2cfg(self, cname: str = "POSCAR"):
        conv_vasp2cfg(cname)

    def get_poscar(self):
        self.poscar = fdfadf()

    def get_norm(self):
        pass
        # VASP (self.poscar))
        return None
