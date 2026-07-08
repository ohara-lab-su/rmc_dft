import csv
import itertools
import json
import math
import os
from pathlib import Path
from collections import Counter
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple

import numpy as np

from rmc_dft.rmc_pot.qn.qn_network_analysis import QnNetworkAnalysis
from rmc_dft.rmc_pot.qn.rmc_constraint_writer import RmcConstraintWriter
from rmc_dft.rmc_pot.qn.vasp_structure import VaspStructure


Pair = Tuple[int, int]
TypedPair = Tuple[int, int, int]
Angle = Tuple[int, int, int]
UnitMolecule = Tuple[str, List[int], List[Pair], List[Angle]]


class QnNetworkBuilder:
    """既存の呼び出しを維持するための入口クラス。

    このクラスは処理本体を持たず、VaspStructure、QnNetworkAnalysis、
    RmcConstraintWriter を生成して呼び出すだけの薄い facade として使う。
    """

    def __init__(
        self,
        structure: Optional["VaspStructure"] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.analysis = QnNetworkAnalysis(structure, config)

    @classmethod
    def from_poscar(
        cls,
        poscar_name: str,
        config_name: str,
    ) -> "QnNetworkBuilder":
        config = QnNetworkAnalysis.load_config(config_name)
        atom_types = QnNetworkAnalysis.get_structure_atom_types(config)
        structure = VaspStructure.read_poscar(poscar_name, atom_types)
        return cls(structure, config)

    @property
    def structure(self) -> Optional["VaspStructure"]:
        return self.analysis.structure

    @property
    def config(self) -> Optional[Dict[str, Any]]:
        return self.analysis.config

    def get_qn_counts(self) -> Dict[int, int]:
        return self.analysis.get_qn_counts()

    def write_qn_csv(
        self,
        path: str,
    ) -> None:
        self.analysis.write_qn_csv(path)

    def write_network_bonds_csv(
        self,
        path: str,
    ) -> None:
        self.analysis.write_network_bonds_csv(path)

    def write_report(
        self,
        path: str,
    ) -> None:
        self.analysis.write_report(path)

    def write_analysis(
        self,
        prefix: str,
    ) -> None:
        self.analysis.write_analysis(prefix)

    def write_fnc3(
        self,
        path: str,
        title: Optional[str] = None,
    ) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_fnc3(path, title=title)

    def write_unit_topology(
        self,
        path: str,
    ) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_unit_topology(path)

    def write_network_topology(
        self,
        path: str,
    ) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_network_topology(path)

    def write_all(
        self,
        prefix: str,
    ) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_rmc_inputs(prefix)
        self.analysis.write_analysis(prefix)
