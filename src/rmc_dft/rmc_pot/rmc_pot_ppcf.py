#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
# ppcf_reader.py
# PPCF (g_ij(r))
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import numpy as np

from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotPpcf:
    def __init__(
        self,
        cfg_name: Optional[str] = None,
        config: Optional[Config] = None,  # Config(),
        logger: Optional[XLogger] = None,
    ):
        """

        Args:
            cfg_name (str):
            config (Config):
            logger (XLogger):
        """
        if cfg_name is None:
            cfg_name = config.cfg_name

        self._logger = logger or XLogger(logger_name="RmcPotFit")
        self._cfg_name = cfg_name
        self.filename: str = f"{cfg_name}.ppcf"

        self.r: np.ndarray = np.array([])
        self.gij: np.ndarray = np.array([])  # shape = (N_bins, 6)

    def load(self) -> None:
        data_start = False
        r_list: List[float] = []
        gij_list: List[Tuple[float, ...]] = []

        with open(self.filename, "r") as f:
            for line in f:
                if data_start:
                    parts = line.strip().split()
                    if len(parts) != 7:
                        continue
                    r_value = float(parts[0])
                    gij_values = tuple(float(v) for v in parts[1:])
                    r_list.append(r_value)
                    gij_list.append(gij_values)

                if line.strip().startswith("r value"):
                    data_start = True

        self.r = np.array(r_list)
        self.gij = np.array(gij_list)

    def get_r(self) -> np.ndarray:
        return self.r

    def get_gij(self) -> np.ndarray:
        return self.gij

    def get_single(self, index: int) -> np.ndarray:
        """
        index : 0=g11, 1=g12, 2=g13, 3=g22, 4=g23, 5=g33
        """
        return self.gij[:, index]
