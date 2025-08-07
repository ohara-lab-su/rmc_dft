import os


class Config:
    #rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe"
    rmc_bin = "/usr/local/src/RMCPOT/rmcp.exe"
    """
    RMCPOT path
    """
    # vasp_bin = "mpirun -np 4 vasp"
    num_procs = 4
    vasp_bin = f"/home/hpc/vasp/bin/vasp-gamma"
    #vasp_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_std"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # vasp_bin = "/home/hpc/vasp/bin/vasp"
    """
    VASP  path
    """

