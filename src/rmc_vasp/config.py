import os


class Config:
    rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe aaa"
    """
    RMCPOT path
    """
    # vasp_bin = "mpirun -np 4 vasp"
    num_procs = 4
    #vasp_bin = f"mpirun -np 4 /home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    vasp_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # vasp_bin = "/home/hpc/vasp/bin/vasp"
    """
    VASP  path
    """
