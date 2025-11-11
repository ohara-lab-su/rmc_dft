import os


class Config:
    rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe"
    """
    RMCPOT path
    """
    # dft_bin = "mpirun -np 4 vasp"
    num_procs = 4
    # dft_bin = f"mpirun -np 4 /home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    dft_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_std"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # dft_bin = "/home/hpc/vasp/bin/vasp"
    """
    VASP  path
    """
