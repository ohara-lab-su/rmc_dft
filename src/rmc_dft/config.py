import os


class Config:

    #
    # RMCPOT path
    #
    # rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe"
    # rmc_bin = "/usr/local/src/RMCPOT/rmcp.exe"
    rmc_bin = "rmcp.exe"

    #
    # VASP  path
    #

    # vasp_bin = "mpirun -np 4 vasp"
    num_procs = 1
    # vasp_bin = f"/home/hpc/vasp/bin/vasp-gamma"
    # vasp_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    vasp_bin = f"vasp_gam"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"
    # mpi_opt =
    # vasp_bin = "/home/hpc/vasp/bin/vasp"

    #
    # default job_name
    #
    job_cmd = "qsub job_hpcs2024_node2.sh"
