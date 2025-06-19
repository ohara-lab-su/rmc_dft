import subprocess
import shutil

for i in range(0,1000):
    # run vasp
    check = subprocess.run("vasp_gam", check=True)
    shutil.copyfile("POSCAR", "aaa.vasp")
    # aaa.vasp -> aaa.cfg
    check = subprocess.run(["python3","Rcfg2vasp_nonLIB.py","aaa"], check=True)
    #run RMCPOT
    check = subprocess.run(["rmcp_v2023.1_lin.exe", "aaa"], check=True)
    check = subprocess.run(["python3","Rvasp2cfg_nonLIB.py","aaa"], check=True)
    shutil.copyfile("aaa.cfg", "POSCAR")

