
# grep on python
def grep_energy():
    input_file = 'OSZICAR'
    output_file = 'grep_E0_OSZICAR.txt'
    key = 'E0'

    with open(output_file, 'w') as outfile:
        with open(input_file, 'r') as f:
            for line in f.readlines():
                if key in line:
                    print(line)
                    outfile.writelines(line)

def vasp_log():
    """
    This function is used to grep energy from OUTCAR file.
    """
    grep_energy()
    print("grep energy from OUTCAR file finished.")

def vasp_copy(log_dir: str = "log"):
    """
    Copy VASP log files to the specified directory.

    Args:
        log_dir (str): Directory to copy the log files to.
    """
    import shutil
    import os

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    files_to_copy = ['OUTCAR', 'OSZICAR', 'vasprun.xml', 'XDATCAR', 'CONTCAR', 'POSCAR', 'KPOINTS']

    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy(file_name, log_dir)
            print(f"Copied {file_name} to {log_dir}")
        else:
            print(f"{file_name} does not exist, skipping.")