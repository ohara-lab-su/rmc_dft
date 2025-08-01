import os


class Config:
    rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe aaa"
    """
    RMCPOT path
    """
    # vasp_bin = "mpirun -np 16 vasp"
    num_procs = 16
    vasp_bin = f"mpirun -np {num_procs} vasp"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # vasp_bin = "/home/hpc/vasp/bin/vasp"
    """
    VASP  path
    """
