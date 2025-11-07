"""
K.NAKADA, kengo.nakada@gmail.com (1st, 3rd varsion)
K.KOBAYASHI (2nd version)
"""

import os


class Config:

    cfg_name: str = "aaa"  # aaa.cfg
    vasp_name: str = "aaa"  # aaa.vasp

    #
    # RMCPOT path
    #
    # rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe"
    # rmc_bin = "/usr/local/src/RMCPOT/rmcp.exe"
    rmc_bin: str = "rmcp.exe"

    #
    # VASP  path
    #

    # vasp_bin = "mpirun -np 4 vasp"
    num_procs: int = 1
    # vasp_bin = f"/home/hpc/vasp/bin/vasp-gamma"
    # vasp_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    vasp_bin: str = f"vasp_gam"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # vasp_bin = "/home/hpc/vasp/bin/vasp"

    #
    # default job_name
    #
    job_cmd: str = "qsub job_hpcs2024_node2.sh"

    def __init__(self, yaml_path=None):
        # インスタンスで使いたいときだけ、ここで個別設定
        if yaml_path:
            self._load_yaml(yaml_path)

    @classmethod
    def load_yaml(cls, yaml_path=None):
        if yaml_path is None:
            yaml_path = os.environ.get("RMC_DFT_CONFIG_YAML")
            if yaml_path is None:
                return
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
            else:
                print("NO SUCH VAR:", k)

    def _load_yaml(self, yaml_path=None):
        # インスタンス用：インスタンスdictにのみ上書き
        print("load_yaml:", yaml_path)
        if yaml_path is None:
            yaml_path = os.environ.get("RMC_DFT_CONFIG_YAML")
            if yaml_path is None:
                return
        yaml_path = os.path.abspath(yaml_path)
        print("abspath:", yaml_path)
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            setattr(self, k, v)
