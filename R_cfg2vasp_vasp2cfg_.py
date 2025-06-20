import subprocess
import shutil

from Rvasp2cfg_nonLIB import conv, conv_vasp2cfg


def vasp_run(blocking: bool=True):
    subprocess.run("vasp_gam", check=True)

def rmc_run(blocking: bool=True):
    subprocess.run(["rmcp_v2023.1_lin.exe", "aaa"], check=True)


def conv_POSCAR2vasp(str)
    shutil.copyfile("POSCAR", "aaa.vasp")

def norm():
    pass


def run(max: int = 1000):
    for i in range(0, max):
        vasp_run()
        conv_vasp2cfg("aaa")
        run_rmc()
        conv_POSCAR2vasp("aaa")
        conv_cfg2vasp("aaa")
        dfadfa()


        # aaa.vasp -> aaa.cfg
        subprocess.run(["python3","Rvasp2cfg_nonLIB.py","aaa"], check=True)
        #run RMCPOT

        # aaa.vasp -> aaa.cfg
        # subprocess.run(["python3","Rcfg2vasp_nonLIB.py","aaa"], check=True)S

        shutil.copyfile("aaa.vasp", "POSCAR")

        if norm() < threshold:
            return


if __name__ ==  "__main__":
    num = get_main()
    run(num)