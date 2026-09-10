"""
K.NAKADA, kengo.nakada@gmail.com (1st, 3rd varsion)
K.KOBAYASHI (2nd version)
"""

from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import yaml
import os

from x_logger import XLogger


class Config:
    max_rmc_dft_loop: int = 10

    N_tot: int = 400  # セルサイズ(原子数)
    # mass_density_g_cm3: float = 7.35  # 質量密度
    mass_density_g_cm3: float = 7.3336  # 質量密度
    # number_density_A3: float = 0.0915 # 数密度
    number_density_A3: float = 0.09119  # 数密度
    # element_info: Union[str, Sequence[str]] = "label.txt"
    element_info: Union[str, Sequence[str]] = ["Fe", "Si", "B"]
    # ratios: Sequence[int] = [80, 9, 11]
    ratios: Sequence[int] = [82, 4, 14]

    # RMC parameter mirror
    rmc_comment: Optional[str] = None
    rmc_cutoffs: Optional[Sequence[float]] = None
    rmc_max_moves: Optional[Sequence[float]] = None
    rmc_r_spacing: Optional[float] = None
    rmc_moveout_option: Optional[bool] = None
    rmc_time_and_save: Optional[Tuple[float, int]] = None
    rmc_data_flags: Optional[Sequence[int]] = None
    rmc_exp_range: Optional[Tuple[int, int]] = None
    rmc_sigma_factor: Optional[float] = None
    rmc_num_atoms_per_move: Optional[int] = None

    # VASP parameter mirror
    vasp_incar_tags: Dict[str, Any] = {}
    vasp_kpoints_mode: Optional[str] = None
    vasp_kpoints_grid: Optional[Tuple[int, int, int]] = None
    vasp_kpoints_shift: Optional[Tuple[int, int, int]] = None
    vasp_kpoints_comment: Optional[str] = None

    # ---------- RMC -----------
    rmc_code: str = "RmcPot"
    rmc_log_dir: str = "rmc_log"
    cfg_name: str = "aaa"  # aaa.cfg
    rmc_exp_filename: str = "ascast.xsq"

    # ------- DFT (VASP) --------
    dft_code: str = "Vasp"
    dft_log_dir: str = "vasp_log"
    vasp_name: str = "aaa"  # aaa.vasp
    run_mode: str = "local"

    #
    # RMCPOT path
    #
    # rmc_bin = "/home/k/Downloads/Source_RMC_POT_lin_2023.1/rmcp.exe"
    # rmc_bin = "/usr/local/src/RMCPOT/rmcp.exe"
    rmc_bin: str = "rmcp.exe"

    #
    # VASP  path
    #
    # dft_bin = f"/home/hpc/vasp/bin/vasp-gamma"
    # dft_bin = f"/home/k/Downloads/vasp.6.4.2/bin/vasp_gam"
    # dft_bin = "/home/hpc/vasp/bin/vasp"
    dft_bin: Optional[str] = f"vasp_gam"

    num_procs: Optional[int] = 1

    mpi_cmd: Optional[str] = "mpirun"
    # mpi = f"mpirun -np {num_procs} {os.path.expanduser('/home/hpc/vasp/bin/vasp')}"

    mpi_flag: Optional[str] = "-np"

    rmc_omp_num_threads: Optional[int] = None
    dft_omp_num_threads: Optional[int] = None

    # default job_name
    job_cmd: Optional[str] = "qsub job_hpcs2024_node2.sh"

    # 自動セーブ
    auto_write: bool = True

    def __init__(
        self,
        yaml_path: Optional[str] = None,
        *,
        logger: Optional[XLogger] = XLogger(),
    ):
        """

        Args:
            yaml_path (str):
            logger (XLogger):
        """
        self._logger = logger

        # インスタンスで使いたいときだけ、ここで個別設定
        if yaml_path:
            self._load_yaml(yaml_path)

    @classmethod
    def load_yaml(cls, yaml_path=None):
        if yaml_path is None:
            yaml_path = os.environ.get("RMC_DFT_CONFIG_YAML")
            if yaml_path is None:
                return
        # with open(yaml_path, "r") as f:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
            else:
                print("NO SUCH VAR:", k)

    def _load_yaml(self, yaml_path=None):
        # インスタンス用：インスタンスdictにのみ上書き
        self._logger.info(f"load_yaml: {yaml_path}")
        if yaml_path is None:
            yaml_path = os.environ.get("RMC_DFT_CONFIG_YAML")
            if yaml_path is None:
                return
        yaml_path = os.path.abspath(yaml_path)
        self._logger.info(f"abspath: {yaml_path}")
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            setattr(self, k, v)


if __name__ == "__main__":
    config = Config("config.yml")
    print(config.num_procs)
    print(type(config.num_procs))
