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

        self.n_atom_types: int = 0
        self.n_partial_ppcf: int = 0
        self.r: np.ndarray = np.array([])
        self.gij: np.ndarray = np.empty((0, 0))

    def load(self) -> None:
        data_start = False
        r_list: List[float] = []
        gij_list: List[Tuple[float, ...]] = []

        with open(self.filename, "r") as f:
            for line in f:
                stripped_line = line.strip()

                if stripped_line.endswith("number of atom types"):
                    parts = stripped_line.split()
                    self.n_atom_types = int(parts[0])
                    self.n_partial_ppcf = (
                        self.n_atom_types * (self.n_atom_types + 1) // 2
                    )

                if data_start:
                    parts = stripped_line.split()
                    expected_columns = self.n_partial_ppcf + 1
                    if len(parts) != expected_columns:
                        continue
                    r_value = float(parts[0])
                    gij_values = tuple(float(v) for v in parts[1:])
                    r_list.append(r_value)
                    gij_list.append(gij_values)

                if stripped_line.startswith("r value"):
                    if self.n_atom_types <= 0:
                        raise ValueError(
                            f"The number of atom types could not be read from "
                            f"{self.filename}."
                        )
                    data_start = True

        if not gij_list:
            raise ValueError(
                f"PPCF data could not be read from {self.filename}."
            )

        self.r = np.array(r_list)
        self.gij = np.array(gij_list)

    def get_r(self) -> np.ndarray:
        return self.r

    def get_gij(self) -> np.ndarray:
        return self.gij

    def get_single(self, index: int) -> np.ndarray:
        """
        Return one partial g_ij(r) selected by its zero-based index.
        """
        return self.gij[:, index]

    def get_labels(self) -> List[str]:
        labels: List[str] = []

        for i in range(1, self.n_atom_types + 1):
            for j in range(i, self.n_atom_types + 1):
                labels.append(f"g{i}{j}(r)")

        return labels
