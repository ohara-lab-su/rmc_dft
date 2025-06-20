import subprocess
import shutil

from Rvasp2cfg_nonLIB import conv


def vasp_run(blocking: bool=True):
    subprocess.run("vasp_gam", check=True)


def norm():
    pass


def run(max: int = 1000):
    for i in range(0, max):
        # run vasp
        vasp_run()
        cnv()
        rmc_fdfa()
        dfadfa()

        shutil.copyfile("POSCAR", "aaa.vasp")
        # aaa.vasp -> aaa.cfg
        subprocess.run(["python3","Rvasp2cfg_nonLIB.py","aaa"], check=True)
        #run RMCPOT
        subprocess.run(["rmcp_v2023.1_lin.exe", "aaa"], check=True)
        # aaa.vasp -> aaa.cfg
        # subprocess.run(["python3","Rcfg2vasp_nonLIB.py","aaa"], check=True)S
        conv("aaa")
        shutil.copyfile("aaa.vasp", "POSCAR")

        if norum()


if __name__ ==  "__main__":
    numn = get_main()
    run(num)