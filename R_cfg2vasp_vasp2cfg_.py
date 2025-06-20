import subprocess
import shutil

from Rvasp2cfg_nonLIB import conv_vasp2cfg
from Rcfg2vasp_nonLIB import conv_cfg2vasp

def vasp_run(blocking: bool=True):
    subprocess.run("vasp_gam", check=True)

def rmc_run(mystr:str, blocking: bool=True):
    subprocess.run(["rmcp_v2023.1_lin.exe", mystr], check=True)


def conv_POSCAR2vasp(mystr:str):
    shutil.copyfile("POSCAR", mystr)

def norm():
    pass

def reach_threshold():
    norm_threshold = 1e-3
    if norm() < norm_threshold:
        return 1
    else:
        return 0


def get_main():
    ###############################################
    ## optparse
    parser = optparse.OptionParser()

    parser.add_option(
        "-n",
        "--num",
        dest="INPUT",
        default=cname,
    )
    options, args = parser.parse_args()

    if options.INPUT:
        cname = options.INPUT

    if len(args) > 0:
        cname = int(args[0])
        return cname
    else:
        return 1000

def run(max: int = 1000):
    for i in range(0, max):
        vasp_run()
        conv_vasp2cfg("aaa")
        rmc_run("aaa")
        conv_POSCAR2vasp("aaa.vasp")
        conv_cfg2vasp("aaa")
        dfadfa()
        if reach_threshold():
            return


if __name__ ==  "__main__":
    num = get_main()
    run(num)