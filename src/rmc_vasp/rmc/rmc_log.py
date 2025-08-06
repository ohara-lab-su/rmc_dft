def rmc_log():
    print("rmc_log")

def rmc_copy(log_dir: str = "log"):
    """
    Copy RMC log files to the specified directory.

    Args:
        log_dir (str): Directory to copy the log files to.
    """
    import shutil
    import os

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    files_to_copy = ['grep_khi_RMC.txt', 'RMC.log', 'RMC.cfg']

    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy(file_name, log_dir)
            print(f"Copied {file_name} to {log_dir}")
        else:
            print(f"{file_name} does not exist, skipping.")