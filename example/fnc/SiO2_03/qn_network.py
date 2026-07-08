#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SiO2 Qn network analysis and RMC_POT input generation.

This module separates three responsibilities:

* VaspStructure: VASP/POSCAR structure data and periodic geometry.
* QnNetworkAnalysis: network construction, Qn statistics, and analysis output.
* RmcConstraintWriter: RMC_POT FNC/topology/DAT-snippet output.
"""
from __future__ import print_function
from __future__ import annotations

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


Pair = Tuple[int, int]
TypedPair = Tuple[int, int, int]
Angle = Tuple[int, int, int]
UnitMolecule = Tuple[str, List[int], List[Pair], List[Angle]]


class ConfigError(Exception):
    """設定ファイルまたは入力構造が不正な場合の例外。

    JSON 設定の必須キー不足、POSCAR の形式不整合、未知の constraint source など、
    ユーザー入力に起因するエラーをこの例外にまとめる。
    """


class VaspStructure(object):
    """VASP/POSCAR 構造データと PBC 幾何計算を保持するクラス。"""

    def __init__(self, labels: List[str], cell: np.ndarray, frac: np.ndarray) -> None:
        self.labels = labels
        self.cell = cell
        self.frac = frac

    @property
    def atom_count(self) -> int:
        return len(self.labels)

    def pbc_vector(self, i: int, j: int) -> np.ndarray:
        """i -> j の minimum-image vector を Angstrom 単位で返す。"""
        delta = self.frac[j] - self.frac[i]
        delta -= np.round(delta)
        return np.dot(delta, self.cell)

    def pbc_distance(self, i: int, j: int) -> float:
        """i-j の PBC 距離を Angstrom 単位で返す。"""
        return float(np.linalg.norm(self.pbc_vector(i, j)))

    def angle_degree(self, i: int, j: int, k: int) -> float:
        """i-j-k の角度を degree で返す。"""
        v1 = self.pbc_vector(j, i)
        v2 = self.pbc_vector(j, k)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        cosang = float(np.dot(v1, v2) / (n1 * n2))
        cosang = max(-1.0, min(1.0, cosang))
        return math.degrees(math.acos(cosang))

    @staticmethod
    def read_poscar(
        path: str, atom_types_from_config: Optional[List[str]]
    ) -> "VaspStructure":
        """POSCAR/CONTCAR/VASP 形式の構造ファイルを読む。

        VASP5 形式のように元素名行がある場合は、その元素名行を使う。
        VASP4 形式のように元素名行がなく個数行だけの場合は、
        JSON 設定の ``atom_types`` を ``atom_types_from_config`` として渡す。

        Args:
            path: POSCAR/CONTCAR/VASP ファイル名。
            atom_types_from_config: 元素名行がない場合に使う atom type 順。

        Returns:
            VaspStructure: 原子ラベル、格子、fractional coordinate。

        Raises:
            ConfigError: POSCAR として読めない、または atom type 数が一致しない場合。
        """
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        lines = []
        for line in raw_lines:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)

        if len(lines) < 8:
            raise ConfigError("POSCAR/CONTCAR として行数が不足しています。")

        scale = float(lines[1].split()[0])
        cell_rows = []
        for i in range(2, 5):
            row = []
            for token in lines[i].split()[:3]:
                row.append(float(token))
            cell_rows.append(row)
        cell = np.array(cell_rows, dtype=float) * scale

        # VASP5 形式では 6 行目に元素名、7 行目に原子数が来る。
        # VASP4 形式では 6 行目がそのまま原子数行になる。
        tokens5 = lines[5].split()
        has_symbol_line = True
        try:
            for token in tokens5:
                int(token)
            has_symbol_line = False
        except ValueError:
            has_symbol_line = True

        if has_symbol_line:
            atom_types = tokens5
            count_tokens = lines[6].split()
            coord_mode_index = 7
        else:
            if atom_types_from_config is None:
                raise ConfigError(
                    "元素名行がない POSCAR です。config の atom_types を指定してください。"
                )
            atom_types = atom_types_from_config
            count_tokens = tokens5
            coord_mode_index = 6

        counts = []
        for token in count_tokens:
            counts.append(int(token))

        if len(atom_types) != len(counts):
            raise ConfigError("atom_types の数と POSCAR の個数行の数が一致しません。")

        coord_mode = lines[coord_mode_index].lower()
        start = coord_mode_index + 1
        if coord_mode.startswith("s"):
            coord_mode = lines[coord_mode_index + 1].lower()
            start = coord_mode_index + 2

        total = sum(counts)
        if len(lines) < start + total:
            raise ConfigError("座標行の数が不足しています。")

        coords = []
        for i in range(total):
            row = []
            for token in lines[start + i].split()[:3]:
                row.append(float(token))
            coords.append(row)
        frac_or_cart = np.array(coords, dtype=float)

        # 内部処理は fractional coordinate に統一する。
        if coord_mode.startswith("d"):
            frac = frac_or_cart.copy()
        else:
            inv_cell = np.linalg.inv(cell)
            frac = frac_or_cart.dot(inv_cell)

        labels = []
        for atom_type, count in zip(atom_types, counts):
            for _ in range(count):
                labels.append(atom_type)

        frac = frac - np.floor(frac)
        return VaspStructure(labels, cell, frac)


class QnNetworkAnalysis(object):
    """Qn network の構築、解析、解析結果出力を行うクラス。"""

    def __init__(
        self,
        structure: Optional["VaspStructure"] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.poscar = structure
        self.structure = structure
        self.config = config
        self.first_map = defaultdict(list)
        self.bridge_second_map = defaultdict(list)
        self.qn_by_central = {}
        self.bridges_by_central = {}
        self.second_by_bridge_for_central = {}
        self.bond_pairs = set()
        self.fnc_pairs = []
        self.fnc_type_names = {}
        self.angles = []
        if structure is not None and config is not None:
            data = QnNetworkAnalysis.build_network(structure, config)
            QnNetworkAnalysis.build_fnc3_pairs(structure, config, data)
            self.first_map = data.first_map
            self.bridge_second_map = data.bridge_second_map
            self.qn_by_central = data.qn_by_central
            self.bridges_by_central = data.bridges_by_central
            self.second_by_bridge_for_central = data.second_by_bridge_for_central
            self.bond_pairs = data.bond_pairs
            self.fnc_pairs = data.fnc_pairs
            self.fnc_type_names = data.fnc_type_names
            self.angles = data.angles

    @classmethod
    def from_poscar(cls, poscar_name: str, config_name: str) -> "QnNetworkAnalysis":
        """VASP 構造ファイルと JSON 設定から QnNetworkAnalysis を作る。"""
        config = cls.load_config(config_name)
        atom_types = cls.QnNetworkAnalysis.get_structure_atom_types(config)
        structure = VaspStructure.read_poscar(poscar_name, atom_types)
        return cls(structure, config)

    def get_qn_counts(self) -> Dict[int, int]:
        """Qn 分布を返す。"""
        counter = Counter(self.qn_by_central.values())
        result = {}
        for key in sorted(counter.keys()):
            result[int(key)] = int(counter[key])
        return result

    def write_qn_csv(self, path: str) -> None:
        QnNetworkAnalysis.write_qn_csv_file(path, self.structure, self)

    def write_network_bonds_csv(self, path: str) -> None:
        QnNetworkAnalysis.write_network_bonds_csv_file(path, self.structure, self)

    def write_report(self, path: str) -> None:
        QnNetworkAnalysis.write_report_file(path, self.structure, self.config, self)

    def write_analysis(self, prefix: str) -> None:
        self.write_qn_csv(prefix + "_qn.csv")
        self.write_network_bonds_csv(prefix + "_network_bonds.csv")
        self.write_report(prefix + "_report.txt")

    def write_fnc3(self, path: str, title: Optional[str] = None) -> None:
        writer = RmcConstraintWriter(self)
        writer.write_fnc3(path, title=title)

    def write_unit_topology(self, path: str) -> None:
        writer = RmcConstraintWriter(self)
        writer.write_unit_topology(path)

    def write_network_topology(self, path: str) -> None:
        writer = RmcConstraintWriter(self)
        writer.write_network_topology(path)

    def write_dat_snippets(self, prefix: str) -> None:
        writer = RmcConstraintWriter(self)
        writer.write_dat_snippets(prefix)

    def write_all(self, prefix: str) -> None:
        writer = RmcConstraintWriter(self)
        writer.write_rmc_inputs(prefix)
        self.write_analysis(prefix)

    @staticmethod
    def load_config(path: str) -> Dict[str, Any]:
        """Qn/FNC 生成用 JSON 設定を読む。

        設定ファイルには atom type 順、hard-sphere cutoff、Qn 定義、
        FNC=3 の距離拘束、FNC=4 の bond/angle パラメータを置く。
        """
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config

    @staticmethod
    def get_required(config: Dict[str, Any], key: str) -> Any:
        """dict から必須キーを取得する。

        通常の ``dict.__getitem__`` でも取得できるが、エラー時にどの設定キーが
        欠けているかを明示するため、この小関数を通す。
        """
        if key not in config:
            raise ConfigError("config に %s がありません。" % key)
        return config[key]

    @staticmethod
    def get_structure_atom_types(config: Dict[str, Any]) -> Optional[List[str]]:
        """POSCAR に元素名行が無い場合に使う atom type 順を取得する。"""
        structure_config = config.get("structure", {})
        if "atom_types" in structure_config:
            return list(structure_config["atom_types"])
        if "atom_types" in config:
            return list(config["atom_types"])
        return None

    @staticmethod
    def get_network_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """VASP 構造から Qn network を作るための入力設定を取得する。"""
        if "network" in config:
            return config["network"]
        if "qn" in config:
            return config["qn"]
        raise ConfigError("config に network がありません。")

    @staticmethod
    def get_rmc_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """RMC_POT 出力用設定を取得する。"""
        if "rmc" in config:
            return config["rmc"]
        return config

    @staticmethod
    def get_fnc_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """RMC_POT .fnc 出力用設定を取得する。"""
        rmc_config = QnNetworkAnalysis.get_rmc_config(config)
        if "fnc" in rmc_config:
            return rmc_config["fnc"]
        if "fnc3" in config:
            return config["fnc3"]
        raise ConfigError("config に rmc.fnc がありません。")

    @staticmethod
    def get_dat_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """RMC_POT dat snippet 出力用設定を取得する。"""
        rmc_config = QnNetworkAnalysis.get_rmc_config(config)
        if "dat" in rmc_config:
            return rmc_config["dat"]
        return config

    @staticmethod
    def get_top_root_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """RMC_POT .top 出力用設定の root を取得する。"""
        rmc_config = QnNetworkAnalysis.get_rmc_config(config)
        if "top" in rmc_config:
            return rmc_config["top"]
        return config

    @staticmethod
    def get_top_atom_parameter(
        config: Dict[str, Any], label: str
    ) -> Tuple[float, float]:
        """[ atoms ] 行へ書く charge と mass を atom type ごとに取得する。

        この値は RMC_POT topology の [ atoms ] 列を埋めるための入力である。
        現状の exporter は non-bonded potential を有効化しないため、charge は
        Coulomb 計算の有効化フラグではない。
        """
        top_root = QnNetworkAnalysis.get_top_root_config(config)
        if "atoms" in top_root:
            atoms_config = top_root["atoms"]
            if label not in atoms_config:
                raise ConfigError("rmc.top.atoms に %s がありません。" % label)
            atom_config = atoms_config[label]
            charge = float(QnNetworkAnalysis.get_required(atom_config, "charge"))
            mass = float(QnNetworkAnalysis.get_required(atom_config, "mass"))
            return charge, mass

        masses = config.get("masses", {})
        charges = config.get("charges", {})
        charge = 0.0
        if label in charges:
            charge = float(charges[label])
        mass = 1.0
        if label in masses:
            mass = float(masses[label])
        return charge, mass

    @staticmethod
    def pbc_vector(i: int, j: int, frac: np.ndarray, cell: np.ndarray) -> np.ndarray:
        """PBC 下で i から j への最短イメージベクトルを返す。

        Args:
            i: 始点原子 index。0 始まり。
            j: 終点原子 index。0 始まり。
            frac: fractional coordinate。
            cell: 格子ベクトル行列。単位は Angstrom。
        """
        df = frac[j] - frac[i]
        df = df - np.rint(df)
        return df.dot(cell)

    @staticmethod
    def pbc_distance(i: int, j: int, frac: np.ndarray, cell: np.ndarray) -> float:
        """PBC 下で原子 i-j 間の最短距離を返す。単位は Angstrom。"""
        vec = QnNetworkAnalysis.pbc_vector(i, j, frac, cell)
        return float(np.linalg.norm(vec))

    @staticmethod
    def angle_degree(
        i: int, j: int, k: int, frac: np.ndarray, cell: np.ndarray
    ) -> float:
        """PBC 下で angle i-j-k を degree 単位で返す。

        j が中心原子である。現在の出力では topology の angle パラメータは
        JSON 設定値を使うため、この関数は検査・拡張用である。
        """
        v1 = QnNetworkAnalysis.pbc_vector(j, i, frac, cell)
        v2 = QnNetworkAnalysis.pbc_vector(j, k, frac, cell)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 <= 0.0 or n2 <= 0.0:
            return 0.0
        cos_value = float(np.dot(v1, v2) / (n1 * n2))
        if cos_value < -1.0:
            cos_value = -1.0
        if cos_value > 1.0:
            cos_value = 1.0
        return float(math.degrees(math.acos(cos_value)))

    @staticmethod
    def pair_key(i: int, j: int) -> Pair:
        """原子対を順序に依存しない key に正規化する。

        FNC=3 の距離拘束や topology の bond は i-j と j-i を同一視する。
        そのため、小さい index を先に置いた tuple を key として使う。
        """
        if i < j:
            return (i, j)
        return (j, i)

    @staticmethod
    def select_indices(labels: Sequence[str], wanted_types: Sequence[str]) -> List[int]:
        """指定した atom type に一致する原子 index を抽出する。"""
        wanted = set(wanted_types)
        result = []
        for i, label in enumerate(labels):
            if label in wanted:
                result.append(i)
        return result

    @staticmethod
    def find_neighbors(
        centers: Sequence[int],
        candidates: Sequence[int],
        poscar: VaspStructure,
        min_distance: float,
        max_distance: float,
        exclude_self: bool,
    ) -> Dict[int, List[int]]:
        """距離範囲で neighbour list を作る。

        Args:
            centers: neighbour を探す中心原子 index 群。
            candidates: neighbour 候補原子 index 群。
            poscar: 構造データ。
            min_distance: 最小距離。単位は Angstrom。
            max_distance: 最大距離。単位は Angstrom。
            exclude_self: True の場合、同一 index は除外する。

        Returns:
            dict: center index -> neighbour index list。
        """
        result = {}
        for center in centers:
            hits = []
            for candidate in candidates:
                if exclude_self:
                    if center == candidate:
                        continue
                distance = QnNetworkAnalysis.pbc_distance(
                    center, candidate, poscar.frac, poscar.cell
                )
                if distance >= min_distance and distance <= max_distance:
                    hits.append(candidate)
            hits.sort()
            result[center] = hits
        return result

    @staticmethod
    def build_network(
        poscar: VaspStructure, config: Dict[str, Any]
    ) -> QnNetworkAnalysis:
        """設定に従って central-bridge-second 型 Qn ネットワークを構築する。

        Qn 判定の基本は次の通りである。

        1. central atom の first neighbour として bridge atom を探す。
        2. bridge atom の second neighbour として second atom を探す。
        3. central-bridge-second が成立する bridge の数を、その central atom の Qn とする。

        ``first_mode`` は二種類ある。

        * ``cutoff``: first_min-first_max に入る bridge をすべて採用する。
        * ``nearest``: first_min-first_max に入る bridge のうち、距離が近い順に
          ``first_nearest_n`` 個だけ採用する。SiO2 のように四面体性を保ちたい場合に使う。

        ``second_use_first_network`` が True の場合、second neighbour は距離で再探索せず、
        first_map の逆写像から作る。これは、すでに決めた Si-O bond network と整合した
        Si-O-Si 判定を行うためのモードである。
        """
        qn_config = QnNetworkAnalysis.get_network_config(config)
        central_types = QnNetworkAnalysis.get_required(qn_config, "central_types")
        bridge_types = QnNetworkAnalysis.get_required(qn_config, "bridge_types")
        second_types = QnNetworkAnalysis.get_required(qn_config, "second_types")
        first_min = float(QnNetworkAnalysis.get_required(qn_config, "first_min"))
        first_max = float(QnNetworkAnalysis.get_required(qn_config, "first_max"))
        second_min = float(QnNetworkAnalysis.get_required(qn_config, "second_min"))
        second_max = float(QnNetworkAnalysis.get_required(qn_config, "second_max"))

        central_indices = QnNetworkAnalysis.select_indices(poscar.labels, central_types)
        bridge_indices = QnNetworkAnalysis.select_indices(poscar.labels, bridge_types)
        second_indices = QnNetworkAnalysis.select_indices(poscar.labels, second_types)

        if len(central_indices) == 0:
            raise ConfigError("central_types に対応する原子がありません。")
        if len(bridge_indices) == 0:
            raise ConfigError("bridge_types に対応する原子がありません。")
        if len(second_indices) == 0:
            raise ConfigError("second_types に対応する原子がありません。")

        data = QnNetworkAnalysis()
        # first neighbour の取り方は、純粋な距離 cutoff と最近接 N 個の二通り。
        # SiO2 では第 5 近接 O を誤って bond と見なさないため nearest=4 が有効な場合がある。
        first_mode = str(qn_config.get("first_mode", "cutoff"))
        first_map = {}
        if first_mode == "cutoff":
            first_map = QnNetworkAnalysis.find_neighbors(
                central_indices, bridge_indices, poscar, first_min, first_max, True
            )
        elif first_mode == "nearest":
            nearest_n = int(qn_config.get("first_nearest_n", 4))
            for central in central_indices:
                distances = []
                for bridge in bridge_indices:
                    distance = QnNetworkAnalysis.pbc_distance(
                        central, bridge, poscar.frac, poscar.cell
                    )
                    if distance >= first_min and distance <= first_max:
                        distances.append((distance, bridge))
                distances.sort()
                selected = []
                for distance, bridge in distances[:nearest_n]:
                    selected.append(bridge)
                selected.sort()
                first_map[central] = selected
        else:
            raise ConfigError("qn.first_mode は cutoff または nearest です。")

        # second_use_first_network=True の場合は、bridge-second 関係を距離から独立に
        # 作り直さず、決定済みの first_map を反転して作る。
        # これにより、Qn 判定と FNC=4 bond network の整合性を保つ。
        second_use_first_network = bool(
            qn_config.get("second_use_first_network", False)
        )
        if second_use_first_network:
            bridge_second_map = {}
            second_type_set = set(second_types)
            for bridge in bridge_indices:
                bridge_second_map[bridge] = []
            for central, bridges in first_map.items():
                if poscar.labels[central] not in second_type_set:
                    continue
                for bridge in bridges:
                    bridge_second_map[bridge].append(central)
            for bridge in bridge_second_map.keys():
                bridge_second_map[bridge] = sorted(set(bridge_second_map[bridge]))
        else:
            bridge_second_map = QnNetworkAnalysis.find_neighbors(
                bridge_indices, second_indices, poscar, second_min, second_max, True
            )

        data.first_map = first_map
        data.bridge_second_map = bridge_second_map

        # central ごとに、別の second atom へ接続している bridge の数を Qn とする。
        for central in central_indices:
            bridges = first_map[central]
            data.bridges_by_central[central] = list(bridges)
            qn_value = 0
            for bridge in bridges:
                second_hits = []
                for second in bridge_second_map[bridge]:
                    if second == central:
                        continue
                    second_hits.append(second)
                data.second_by_bridge_for_central[(central, bridge)] = second_hits
                if len(second_hits) > 0:
                    qn_value = qn_value + 1
            data.qn_by_central[central] = qn_value

        for central, bridges in first_map.items():
            for bridge in bridges:
                data.bond_pairs.add(QnNetworkAnalysis.pair_key(central, bridge))

        for bridge, seconds in bridge_second_map.items():
            for second in seconds:
                data.bond_pairs.add(QnNetworkAnalysis.pair_key(bridge, second))

        return data

    @staticmethod
    def add_typed_pair(
        pair_types: Dict[Pair, int], i: int, j: int, type_id: int
    ) -> None:
        """FNC=3 用 typed pair を重複なしで登録する。

        同じ原子対が同じ type_id で複数回出る場合は重複として無視する。
        同じ原子対に異なる type_id が割り当てられた場合は、設定または
        Q network 解析の矛盾として止める。

        FNC の type_id は距離範囲 rmin/rmax と一対一に対応するため、
        type_id の大小で自動的に優先順位を決めてはいけない。
        """
        key = QnNetworkAnalysis.pair_key(i, j)

        if key not in pair_types:
            pair_types[key] = type_id
            return

        old_type_id = pair_types[key]
        if old_type_id == type_id:
            return

        raise ConfigError(
            "同一 FNC pair に異なる type_id が割り当てられました: "
            "atom_i=%d atom_j=%d old_type_id=%d new_type_id=%d"
            % (i + 1, j + 1, old_type_id, type_id)
        )

    @staticmethod
    def build_fnc3_pairs(
        poscar: VaspStructure, config: Dict[str, Any], data: QnNetworkAnalysis
    ) -> None:
        """QnNetworkAnalysis から FNC=3 用の原子対リストを作る。

        JSON の ``fnc3.constraints`` で source を指定する。現在対応する source は次の通り。

        * ``central_bridge_bonds``: central-bridge の直接 bond。例: Si-O。
        * ``bridge_second_bonds``: bridge-second の直接 bond。例: O-Si。
        * ``central_second_through_bridge``: bridge を介した central-second。例: Si-O-Si の Si-Si。
        * ``bridge_bridge_around_central``: central 周りの bridge-bridge。例: SiO4 内 O-O。

        結果は ``data.fnc_pairs`` と ``data.fnc_type_names`` に格納する。
        """
        fnc3_config = QnNetworkAnalysis.get_fnc_config(config)
        constraints = QnNetworkAnalysis.get_required(fnc3_config, "constraints")

        pair_types = {}  # type: Dict[Pair, int]
        type_names = {}  # type: Dict[int, str]

        for item in constraints:
            type_id = int(QnNetworkAnalysis.get_required(item, "type_id"))
            name = str(QnNetworkAnalysis.get_required(item, "name"))
            source = str(QnNetworkAnalysis.get_required(item, "source"))
            type_names[type_id] = name

            if source == "central_bridge_bonds":
                for central, bridges in data.first_map.items():
                    for bridge in bridges:
                        QnNetworkAnalysis.add_typed_pair(
                            pair_types, central, bridge, type_id
                        )

            elif source == "bridge_second_bonds":
                for bridge, seconds in data.bridge_second_map.items():
                    for second in seconds:
                        QnNetworkAnalysis.add_typed_pair(
                            pair_types, bridge, second, type_id
                        )

            elif source == "central_second_through_bridge":
                for central, bridges in data.first_map.items():
                    for bridge in bridges:
                        second_hits = data.second_by_bridge_for_central[
                            (central, bridge)
                        ]
                        for second in second_hits:
                            QnNetworkAnalysis.add_typed_pair(
                                pair_types, central, second, type_id
                            )

            elif source == "bridge_bridge_around_central":
                for central, bridges in data.first_map.items():
                    sorted_bridges = sorted(bridges)
                    for bridge1, bridge2 in itertools.combinations(sorted_bridges, 2):
                        QnNetworkAnalysis.add_typed_pair(
                            pair_types, bridge1, bridge2, type_id
                        )

            else:
                raise ConfigError("未知の fnc3 constraint source です: %s" % source)

        typed_pairs = []
        for pair in sorted(pair_types.keys()):
            typed_pairs.append((pair[0], pair[1], pair_types[pair]))
        data.fnc_pairs = typed_pairs
        data.fnc_type_names = type_names

    @staticmethod
    def collect_fnc3_ranges(config: Dict[str, Any]) -> Dict[int, Tuple[float, float]]:
        """FNC=3 type_id ごとの rmin/rmax を JSON 設定から取り出す。"""
        result = {}
        fnc3_config = QnNetworkAnalysis.get_fnc_config(config)
        constraints = QnNetworkAnalysis.get_required(fnc3_config, "constraints")
        for item in constraints:
            type_id = int(QnNetworkAnalysis.get_required(item, "type_id"))
            rmin = float(QnNetworkAnalysis.get_required(item, "rmin"))
            rmax = float(QnNetworkAnalysis.get_required(item, "rmax"))
            result[type_id] = (rmin, rmax)
        return result

    @staticmethod
    def write_fnc(
        path: str,
        atom_count: int,
        typed_pairs: Sequence[TypedPair],
        ranges: Dict[int, Tuple[float, float]],
        title: str,
    ) -> None:
        """RMC_POT FNC=3 用 ``*.fnc`` ファイルを書く。

        ``typed_pairs`` は 0 始まり index で受け取り、ファイル出力時に 1 始まりへ変換する。
        ``ranges`` は FNC type_id -> (rmin, rmax) で、type_id は 1 から連番である必要がある。
        """
        neighbours = defaultdict(list)  # type: Dict[int, List[Tuple[int, int]]]
        for i, j, type_id in typed_pairs:
            neighbours[i].append((j, type_id))
            neighbours[j].append((i, type_id))

        max_type = 0
        for type_id in ranges.keys():
            if type_id > max_type:
                max_type = type_id

        with open(path, "w", encoding="utf-8") as f:
            # RMC_POT の .fnc は、先頭に constraint type ごとの rmin/rmax を書き、
            # その後に各 atom の neighbour index と type_id を並べる。
            f.write("Fixed neighbours constraints (.FNC) file for %s\n" % title)
            f.write("No. of possible rmin-rmax pairs:\n")
            f.write("%d\n" % max_type)
            rmin_values = []
            rmax_values = []

            for type_id in range(1, max_type + 1):
                if type_id not in ranges:
                    raise ConfigError("FNC type_id が連番ではありません: %d" % type_id)
                rmin_values.append("%.8f" % ranges[type_id][0])
                rmax_values.append("%.8f" % ranges[type_id][1])

            f.write(" ".join(rmin_values) + "\n")
            f.write(" ".join(rmax_values) + "\n")
            f.write("%d\n" % atom_count)
            for atom in range(atom_count):
                items = sorted(neighbours.get(atom, []))
                f.write("%d %d\n" % (atom + 1, len(items)))
                if len(items) > 0:
                    f.write(" ".join(str(item[0] + 1) for item in items) + "\n")
                    f.write(" ".join(str(item[1]) for item in items) + "\n")

    @staticmethod
    def write_qn_csv_file(
        path: str, poscar: VaspStructure, data: QnNetworkAnalysis
    ) -> None:
        """Central atom ごとの Qn 判定結果を CSV へ書く。

        ``central_rmc_index`` と ``bridge_rmc_indices`` は RMC_POT へ対応しやすいように
        1 始まり index で出力する。
        """
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "central_rmc_index",
                    "central_type",
                    "q_n",
                    "first_bridge_count",
                    "bridging_bridge_count",
                    "bridge_rmc_indices",
                    "bridge_types",
                ]
            )
            for central in sorted(data.qn_by_central.keys()):
                bridges = data.bridges_by_central[central]
                bridge_index_text = " ".join(str(bridge + 1) for bridge in bridges)
                bridge_type_text = " ".join(poscar.labels[bridge] for bridge in bridges)
                writer.writerow(
                    [
                        central + 1,
                        poscar.labels[central],
                        data.qn_by_central[central],
                        len(bridges),
                        data.qn_by_central[central],
                        bridge_index_text,
                        bridge_type_text,
                    ]
                )

    @staticmethod
    def write_network_bonds_csv_file(
        path: str, poscar: VaspStructure, data: QnNetworkAnalysis
    ) -> None:
        """検出された network bond を CSV へ書く。

        この CSV は FNC=4 topology の [ bonds ] に入る bond の確認用である。
        """
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["i_rmc_index", "j_rmc_index", "i_type", "j_type"])
            for i, j in sorted(data.bond_pairs):
                writer.writerow([i + 1, j + 1, poscar.labels[i], poscar.labels[j]])

    @staticmethod
    def summarize_distances(
        poscar: VaspStructure, typed_pairs: Sequence[TypedPair]
    ) -> Dict[int, List[float]]:
        """FNC type_id ごとに現在構造での実距離を集計する。"""
        result = defaultdict(list)  # type: Dict[int, List[float]]
        for i, j, type_id in typed_pairs:
            result[type_id].append(
                QnNetworkAnalysis.pbc_distance(i, j, poscar.frac, poscar.cell)
            )
        return result

    @staticmethod
    def percentile_line(values: Sequence[float]) -> str:
        """距離分布の代表値を report 用の 1 行文字列に変換する。"""
        if len(values) == 0:
            return "count=0"
        arr = np.array(values, dtype=float)
        ps = np.percentile(arr, [0, 1, 5, 50, 95, 99, 100])
        text = (
            "count=%d min=%.4f p1=%.4f p5=%.4f p50=%.4f p95=%.4f p99=%.4f max=%.4f"
            % (len(arr), ps[0], ps[1], ps[2], ps[3], ps[4], ps[5], ps[6])
        )
        return text

    @staticmethod
    def write_report_file(
        path: str,
        poscar: VaspStructure,
        config: Dict[str, Any],
        data: QnNetworkAnalysis,
    ) -> None:
        """Qn 解析と FNC 生成結果の確認用 report を書く。

        report には Qn 定義、Qn 分布、検出された bond/angle 数、
        FNC=3 type ごとの距離統計を含める。
        """
        qn_counts = Counter(data.qn_by_central.values())
        distances_by_type = QnNetworkAnalysis.summarize_distances(
            poscar, data.fnc_pairs
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write("Qn/RMC_POT constraint generation report\n")
            f.write("====================================\n\n")
            f.write("Atom count: %d\n" % poscar.atom_count)
            f.write(
                "Atom types in structure: %s\n" % " ".join(sorted(set(poscar.labels)))
            )
            f.write("Cell volume: %.8f A^3\n" % abs(float(np.linalg.det(poscar.cell))))
            f.write(
                "Number density: %.10f 1/A^3\n\n"
                % (float(poscar.atom_count) / abs(float(np.linalg.det(poscar.cell))))
            )

            f.write("Qn definition\n")
            f.write("-------------\n")
            qn_config = QnNetworkAnalysis.get_network_config(config)
            f.write("central_types: %s\n" % " ".join(qn_config["central_types"]))
            f.write("bridge_types : %s\n" % " ".join(qn_config["bridge_types"]))
            f.write("second_types : %s\n" % " ".join(qn_config["second_types"]))
            f.write(
                "first range  : %.4f - %.4f A\n"
                % (float(qn_config["first_min"]), float(qn_config["first_max"]))
            )
            f.write(
                "second range : %.4f - %.4f A\n\n"
                % (float(qn_config["second_min"]), float(qn_config["second_max"]))
            )

            f.write("Qn counts\n")
            f.write("---------\n")
            for qn_value in sorted(qn_counts.keys()):
                f.write("Q%d: %d\n" % (qn_value, qn_counts[qn_value]))
            f.write("\n")

            f.write("Network counts\n")
            f.write("--------------\n")
            f.write(
                "central-bridge entries: %d\n"
                % sum(len(v) for v in data.first_map.values())
            )
            f.write(
                "bridge-second entries : %d\n"
                % sum(len(v) for v in data.bridge_second_map.values())
            )
            f.write("unique bond pairs      : %d\n" % len(data.bond_pairs))
            f.write("FNC=3 pairs            : %d\n" % len(data.fnc_pairs))
            f.write("network topology angles: %d\n\n" % len(data.angles))

            f.write("FNC=3 distance statistics\n")
            f.write("-------------------------\n")
            for type_id in sorted(distances_by_type.keys()):
                type_name = data.fnc_type_names.get(type_id, "type_%d" % type_id)
                f.write(
                    "type %d %s: %s\n"
                    % (
                        type_id,
                        type_name,
                        QnNetworkAnalysis.percentile_line(distances_by_type[type_id]),
                    )
                )

            f.write("\nNotes\n")
            f.write("-----\n")
            f.write("FNC=3 is a distance-window constraint.\n")
            f.write(
                "RMC_POT topology uses bonded potential terms. The .top file is not an FNC file.\n"
            )
            f.write(
                "The standard generated topology is the independent-unit topology.\n"
            )
            f.write(
                "The current-network topology is generated only by an explicit call.\n"
            )
            f.write(
                "For production RMC_POT runs, check the .hst output and acceptance ratio, then tune sigmas/force constants.\n"
            )


class RmcConstraintWriter(object):
    """QnNetworkAnalysis の解析結果から RMC_POT 用 FNC/topology を出力するクラス。"""

    def __init__(self, network: QnNetworkAnalysis) -> None:
        self.network = network
        self.structure = network.structure
        self.config = network.config

    def write_fnc3(self, path: str, title: Optional[str] = None) -> None:
        output_title = title
        if output_title is None:
            output_title = Path(path).stem
        ranges = QnNetworkAnalysis.collect_fnc3_ranges(self.config)
        RmcConstraintWriter.write_fnc(
            path,
            self.structure.atom_count,
            self.network.fnc_pairs,
            ranges,
            output_title,
        )

    def write_unit_topology(self, path: str) -> None:
        RmcConstraintWriter.write_unit_topology_file(path, self.structure, self.config)

    def write_network_topology(self, path: str) -> None:
        RmcConstraintWriter.write_topology(
            path, self.structure, self.config, self.network
        )

    def write_dat_snippets(self, prefix: str) -> None:
        RmcConstraintWriter.write_dat_snippets_file(prefix, self.config)

    def write_rmc_inputs(self, prefix: str) -> None:
        self.write_fnc3(prefix + "_rmc_fnc3.fnc", title=prefix)
        self.write_unit_topology(prefix + "_rmc_unit.top")
        self.write_dat_snippets(prefix)

    @staticmethod
    def write_fnc(
        path: str,
        atom_count: int,
        typed_pairs: Sequence[TypedPair],
        ranges: Dict[int, Tuple[float, float]],
        title: str,
    ) -> None:
        """RMC_POT FNC=3 用 ``*.fnc`` ファイルを書く。

        ``typed_pairs`` は 0 始まり index で受け取り、ファイル出力時に 1 始まりへ変換する。
        ``ranges`` は FNC type_id -> (rmin, rmax) で、type_id は 1 から連番である必要がある。
        """
        neighbours = defaultdict(list)  # type: Dict[int, List[Tuple[int, int]]]
        for i, j, type_id in typed_pairs:
            neighbours[i].append((j, type_id))
            neighbours[j].append((i, type_id))

        max_type = 0
        for type_id in ranges.keys():
            if type_id > max_type:
                max_type = type_id

        with open(path, "w", encoding="utf-8") as f:
            # RMC_POT の .fnc は、先頭に constraint type ごとの rmin/rmax を書き、
            # その後に各 atom の neighbour index と type_id を並べる。
            f.write("Fixed neighbours constraints (.FNC) file for %s\n" % title)
            f.write("No. of possible rmin-rmax pairs:\n")
            f.write("%d\n" % max_type)
            rmin_values = []
            rmax_values = []
            for type_id in range(1, max_type + 1):
                if type_id not in ranges:
                    raise ConfigError("FNC type_id が連番ではありません: %d" % type_id)
                rmin_values.append("%.8f" % ranges[type_id][0])
                rmax_values.append("%.8f" % ranges[type_id][1])
            f.write(" ".join(rmin_values) + "\n")
            f.write(" ".join(rmax_values) + "\n")
            f.write("%d\n" % atom_count)
            for atom in range(atom_count):
                items = sorted(neighbours.get(atom, []))
                f.write("%d %d\n" % (atom + 1, len(items)))
                if len(items) > 0:
                    f.write(" ".join(str(item[0] + 1) for item in items) + "\n")
                    f.write(" ".join(str(item[1]) for item in items) + "\n")

    @staticmethod
    def get_topology_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """RMC_POT current-network topology 用設定を取得する。

        新しい JSON では ``rmc.top.network`` を使う。
        flat な旧 JSON 名はここでは読まない。
        """
        top_root = QnNetworkAnalysis.get_top_root_config(config)
        if "network" in top_root:
            return top_root["network"]
        raise ConfigError("config に rmc.top.network がありません。")

    @staticmethod
    def get_force_field_include(top_config: Dict[str, Any]) -> str:
        """RMC_POT が force field 名を判定するための include 名を返す。

        RMC_POT は FNC=4 topology の先頭付近にある force-field include 名から
        force field 種別を判定する。GROMACS 用の実力場を使わない RMC 専用 topology
        でも、``ffUNKNOWN_READ_PAIRS.itp`` などの認識可能な include 名が必要である。
        """
        include_name = top_config.get("force_field_include", None)
        if include_name is None:
            include_name = top_config.get("include", None)
        if include_name is None:
            include_name = "ffUNKNOWN_READ_PAIRS.itp"
        return str(include_name)

    @staticmethod
    def write_force_field_stub(topology_path: str, include_name: str) -> None:
        """RMC 専用 UNKNOWN force-field include の空 stub を必要に応じて作る。

        RMC_POT は force field 名を include 名から判定する。実際の非結合 parameter は
        ``*.dat`` 側から読むため、UNKNOWN 系では include file の中身は最小でよい。
        既存ファイルがある場合は上書きしない。
        """
        if os.path.isabs(include_name):
            include_path = include_name
        else:
            base_dir = os.path.dirname(os.path.abspath(topology_path))
            include_path = os.path.join(base_dir, include_name)

        if os.path.exists(include_path):
            return

        include_base = os.path.basename(include_name)
        if include_base not in (
            "ffUNKNOWN_READ_PAIRS.itp",
            "ffUNKNOWN_GENERATE_PAIRS.itp",
        ):
            return

        with open(include_path, "w", encoding="utf-8") as f:
            f.write("; Minimal RMC_POT force-field marker include.\n")
            f.write(
                "; RMC_POT uses the include file name to identify UNKNOWN_READ_PAIRS / UNKNOWN_GENERATE_PAIRS.\n"
            )
            f.write(
                "; Non-bonded parameters, if used, must be supplied from the RMC_POT *.dat file.\n"
            )

    @staticmethod
    def build_angles(
        poscar: VaspStructure, config: Dict[str, Any], data: QnNetworkAnalysis
    ) -> List[Tuple[int, int, int, str]]:
        """FNC=4 topology の [ angles ] に書く angle list を作る。

        JSON の ``rmc.top.network.angles`` で source を指定する。現在対応する source は次の通り。

        * ``bridge_central_bridge``: central を中心にした bridge-central-bridge。例: O-Si-O。
        * ``central_bridge_second``: bridge を中心にした central-bridge-second。例: Si-O-Si。

        戻り値の index は 0 始まりで、最後の文字列は angle parameter 名である。
        """
        top_config = RmcConstraintWriter.get_topology_config(config)
        angle_items = top_config.get("angles", [])
        angles = []  # type: List[Tuple[int, int, int, str]]
        seen = set()  # type: Set[Tuple[int, int, int, str]]

        for item in angle_items:
            name = str(QnNetworkAnalysis.get_required(item, "name"))
            source = str(QnNetworkAnalysis.get_required(item, "source"))
            if source == "bridge_central_bridge":
                for central, bridges in data.first_map.items():
                    sorted_bridges = sorted(bridges)
                    for bridge1, bridge2 in itertools.combinations(sorted_bridges, 2):
                        key = (bridge1, central, bridge2, name)
                        if key not in seen:
                            seen.add(key)
                            angles.append(key)

            elif source == "central_bridge_second":
                for central, bridges in data.first_map.items():
                    for bridge in bridges:
                        second_hits = data.second_by_bridge_for_central[
                            (central, bridge)
                        ]
                        for second in second_hits:
                            key = (central, bridge, second, name)
                            if key not in seen:
                                seen.add(key)
                                angles.append(key)

            else:
                raise ConfigError(
                    "未知の rmc.top.network angle source です: %s" % source
                )

        return angles

    @staticmethod
    def find_angle_parameter(config: Dict[str, Any], angle_name: str) -> Dict[str, Any]:
        """angle 名に対応する FNC=4 angle パラメータを JSON 設定から探す。"""
        top_config = RmcConstraintWriter.get_topology_config(config)
        for item in top_config.get("angles", []):
            name = str(QnNetworkAnalysis.get_required(item, "name"))
            if name == angle_name:
                return item
        raise ConfigError("angle parameter が見つかりません: %s" % angle_name)

    @staticmethod
    def write_topology(
        path: str,
        poscar: VaspStructure,
        config: Dict[str, Any],
        data: QnNetworkAnalysis,
    ) -> None:
        """RMC_POT FNC=4 用 topology を書く。

        ここで書く ``*.top`` は GROMACS で MD を実行するための topology ではない。
        RMC_POT が FNC=4 で bonded potential を計算するために読む topology である。

        RMC_POT の manual では topology の記法として GROMACS 型 directive 名が使われる。
        ただし RMC が認識する directive は限定されており、この exporter では
        Qn ネットワーク保持に必要な次の 5 種類だけを書く。

        * ``[ moleculetype ]``: ネットワーク全体を 1 つの molecule として扱うための名前。
        * ``[ atoms ]``: topology 内 atom index と RMC configuration 内 atom index の対応。
        * ``[ bonds ]``: Si-O など、ネットワーク edge に対する harmonic bond。
        * ``[ angles ]``: O-Si-O や Si-O-Si など、ネットワーク angle に対する harmonic angle。
        * ``[ system ]`` / ``[ molecules ]``: topology の末尾に必要な system 情報。

        ``[ atoms ]`` の行末にある ``; first_RMC_index second_RMC_index`` は RMC_POT 固有情報である。
        GROMACS ではコメントだが、RMC_POT はこの情報を使って topology atom と
        RMC configuration atom を対応付ける。ここでは 1 つの network molecule として書くため、
        first と second は同じ index にしている。

        ``[ bonds ]`` と ``[ angles ]`` は「結合がある」という幾何学的な宣言だけではない。
        RMC_POT は harmonic potential として使うため、平衡値、力定数、sigma が必要である。
        そのため、topology 用 JSON には最低限 ``bond.length_nm``、``bond.force_kj_mol_nm2``、
        ``bond.sigma``、および各 angle の ``theta_degree``、``force_kj_mol_rad2``、``sigma`` を置く。
        """
        top_config = RmcConstraintWriter.get_topology_config(config)

        molecule_name = str(top_config.get("molecule_name", "QNNET"))
        residue_name = str(top_config.get("residue_name", "QNN"))
        nrexcl = int(top_config.get("nrexcl", 2))

        atom_type_prefix = str(top_config.get("atom_type_prefix", ""))

        bond_config = top_config.get("bond", {})
        bond_length_nm = float(
            bond_config.get("length_nm", top_config.get("bond_length_nm", 0.161))
        )
        bond_force = float(
            bond_config.get(
                "force_kj_mol_nm2", top_config.get("bond_force_kj_mol_nm2", 10000.0)
            )
        )
        bond_sigma = float(bond_config.get("sigma", top_config.get("bond_sigma", 10.0)))

        angles = RmcConstraintWriter.build_angles(poscar, config, data)
        data.angles = angles

        include_name = RmcConstraintWriter.get_force_field_include(top_config)
        RmcConstraintWriter.write_force_field_stub(path, include_name)

        with open(path, "w", encoding="utf-8") as f:
            f.write("; RMC_POT FNC=4 topology generated by qn_network.py\n")
            f.write("; This is an RMC_POT topology, not a GROMACS MD topology.\n")
            f.write("; The current Qn network is treated as one flexible molecule.\n")
            f.write("; Tune force constants and sigmas by short RMC_POT test runs.\n")
            f.write('#include "%s"\n' % str(include_name))
            f.write("\n[ moleculetype ]\n")
            f.write("; molname nrexcl ; RMCindex_offset\n")
            f.write("%s %d ; 0\n\n" % (molecule_name, nrexcl))

            f.write("[ atoms ]\n")
            f.write(
                "; nr type resnr residue atom cgnr charge mass ; first_RMC_index second_RMC_index\n"
            )
            for i, label in enumerate(poscar.labels):
                if atom_type_prefix:
                    atom_type = "%s_%s" % (atom_type_prefix, label)
                else:
                    atom_type = label
                charge, mass = QnNetworkAnalysis.get_top_atom_parameter(config, label)
                atom_name = "%s%d" % (label, i + 1)
                f.write(
                    "%6d %-10s 1 %-6s %-8s %6d % .8f % .8f ; %d %d\n"
                    % (
                        i + 1,
                        atom_type,
                        residue_name,
                        atom_name,
                        i + 1,
                        charge,
                        mass,
                        i + 1,
                        i + 1,
                    )
                )

            f.write("\n[ bonds ]\n")
            f.write("; i j funct b_nm kb_kJ_mol_nm2 ; sigma\n")
            for i, j in sorted(data.bond_pairs):
                f.write(
                    "%6d %6d 1 %.8f %.8f ; %.8f\n"
                    % (i + 1, j + 1, bond_length_nm, bond_force, bond_sigma)
                )

            f.write("\n[ angles ]\n")
            f.write("; i j k funct theta_deg ktheta_kJ_mol_rad2 ; sigma ; name\n")
            for i, j, k, angle_name in angles:
                param = RmcConstraintWriter.find_angle_parameter(config, angle_name)
                theta = float(QnNetworkAnalysis.get_required(param, "theta_degree"))
                force = float(
                    QnNetworkAnalysis.get_required(param, "force_kj_mol_rad2")
                )
                sigma = float(QnNetworkAnalysis.get_required(param, "sigma"))
                f.write(
                    "%6d %6d %6d 1 %.8f %.8f ; %.8f ; %s\n"
                    % (i + 1, j + 1, k + 1, theta, force, sigma, angle_name)
                )

            f.write("\n[ system ]\n")
            f.write("Qn network generated from RMC/POSCAR structure\n\n")
            f.write("[ molecules ]\n")
            f.write("%s 1\n" % molecule_name)

    @staticmethod
    def get_unit_topology_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """独立分子・独立フラグメント topology 用設定を取得する。

        新しい JSON では ``rmc.top.unit`` を使う。
        新しい JSON では ``rmc.top.unit`` を使う。
        flat な旧 JSON 名はここでは読まない。
        """
        top_root = QnNetworkAnalysis.get_top_root_config(config)
        if "unit" in top_root:
            return top_root["unit"]
        raise ConfigError("config に rmc.top.unit がありません。")

    @staticmethod
    def _select_unit_ligand_candidates(
        poscar: VaspStructure,
        central_indices: Sequence[int],
        ligand_indices: Sequence[int],
        min_distance: float,
        max_distance: float,
    ) -> List[Tuple[float, int, int]]:
        """central-ligand 候補を距離順に並べて返す。

        戻り値は ``(distance, central_index, ligand_index)`` の list である。
        ``build_independent_unit_molecules`` の最近接排他的割当で使う。
        """
        candidates = []
        for central in central_indices:
            for ligand in ligand_indices:
                distance = QnNetworkAnalysis.pbc_distance(
                    central, ligand, poscar.frac, poscar.cell
                )
                if distance >= min_distance and distance <= max_distance:
                    candidates.append((distance, central, ligand))
        candidates.sort()
        return candidates

    @staticmethod
    def build_independent_unit_molecules(
        poscar: VaspStructure, config: Dict[str, Any]
    ) -> List[UnitMolecule]:
        """RMC_POT FNC=4 用の独立分子・独立フラグメント一覧を作る。

        この関数は、初期構造から検出したネットワーク全体を 1 つの molecule として固定しない。
        代わりに、central atom と一定数の ligand atom から成る独立 unit を作る。
        たとえば SiO2 の Packmol 初期配置に対応させるなら、Si 1 個 + O 2 個を 1 unit とする。

        重要な設計意図は次である。

        * unit 内の bond/angle は RMC_POT の bonded potential で保つ。
        * unit 間には bond/angle を張らない。
        * したがって、RMC は unit 間配置を実験データに合わせて探索できる。
        * 個別の Si-O-Si ネットワーク全体を固定しない。

        JSON の ``rmc.top.unit`` で使う主な項目:

        * ``central_types``: unit 中心 atom type。例: ["Si"]。
        * ``ligand_types``: unit に含める周辺 atom type。例: ["O"]。
        * ``ligand_count``: central 1 個あたりに割り当てる ligand 数。SiO2 unit なら 2。
        * ``distance_min`` / ``distance_max``: 割当候補とする central-ligand 距離範囲。
        * ``assignment``: 現在は ``nearest_exclusive`` のみ。ligand を複数 unit に重複所属させない。

        注意:
            この方法は「独立分子単位の保持」であり、共有酸素を持つ無限 Si-O-Si network を
            表現するものではない。共有ネットワークを固定したい場合は ``write_network_topology`` を使う。
        """
        unit_config = RmcConstraintWriter.get_unit_topology_config(config)
        central_types = unit_config.get("central_types", None)
        ligand_types = unit_config.get("ligand_types", None)

        if central_types is None:
            qn_config = QnNetworkAnalysis.get_network_config(config)
            central_types = qn_config.get("central_types", [])
        if ligand_types is None:
            qn_config = QnNetworkAnalysis.get_network_config(config)
            ligand_types = qn_config.get("bridge_types", [])

        ligand_count = int(QnNetworkAnalysis.get_required(unit_config, "ligand_count"))
        min_distance = float(unit_config.get("distance_min", 0.0))
        max_distance = float(unit_config.get("distance_max", 99.0))
        assignment = str(unit_config.get("assignment", "nearest_exclusive"))
        allow_incomplete = bool(unit_config.get("allow_incomplete", False))
        include_unassigned_atoms = bool(
            unit_config.get("include_unassigned_atoms", True)
        )
        molecule_name_prefix = str(unit_config.get("molecule_name", "UNIT"))
        generate_angles = bool(unit_config.get("generate_angles", True))

        if assignment != "nearest_exclusive":
            raise ConfigError(
                "rmc.top.unit.assignment は nearest_exclusive のみ対応しています。"
            )

        central_indices = QnNetworkAnalysis.select_indices(poscar.labels, central_types)
        ligand_indices = QnNetworkAnalysis.select_indices(poscar.labels, ligand_types)
        if len(central_indices) == 0:
            raise ConfigError("rmc.top.unit.central_types に対応する原子がありません。")
        if len(ligand_indices) == 0:
            raise ConfigError("rmc.top.unit.ligand_types に対応する原子がありません。")

        needs = {}
        assigned = defaultdict(list)  # type: Dict[int, List[int]]
        for central in central_indices:
            needs[central] = ligand_count

        used_ligands = set()  # type: Set[int]
        candidates = RmcConstraintWriter._select_unit_ligand_candidates(
            poscar,
            central_indices,
            ligand_indices,
            min_distance,
            max_distance,
        )

        # 距離が短い central-ligand 候補から順に採用する。
        # ligand は一度だけ使うので、unit 間で atom を共有しない。
        for distance, central, ligand in candidates:
            if ligand in used_ligands:
                continue
            if needs[central] <= 0:
                continue
            assigned[central].append(ligand)
            used_ligands.add(ligand)
            needs[central] = needs[central] - 1

        missing = []
        for central in central_indices:
            if needs[central] > 0:
                missing.append((central, needs[central]))
        if len(missing) > 0 and not allow_incomplete:
            raise ConfigError(
                "independent unit 作成で ligand 数が不足しました。"
                "distance range または ligand_count を見直してください。"
            )

        molecules = []  # type: List[UnitMolecule]
        molecule_index = 1
        included_atoms = set()  # type: Set[int]

        for central in sorted(central_indices):
            ligands = sorted(assigned.get(central, []))

            atom_indices = [central]
            for ligand in ligands:
                atom_indices.append(ligand)

            bonds = []  # type: List[Pair]
            for local_ligand_index in range(1, len(atom_indices)):
                bonds.append((0, local_ligand_index))

            angles = []  # type: List[Angle]
            if generate_angles:
                local_ligand_indices = list(range(1, len(atom_indices)))
                for local_i, local_k in itertools.combinations(local_ligand_indices, 2):
                    angles.append((local_i, 0, local_k))

            molecule_name = "%s%06d" % (molecule_name_prefix, molecule_index)
            molecules.append((molecule_name, atom_indices, bonds, angles))
            for atom_index in atom_indices:
                included_atoms.add(atom_index)
            molecule_index = molecule_index + 1

        if include_unassigned_atoms:
            for atom_index in range(poscar.atom_count):
                if atom_index in included_atoms:
                    continue
                molecule_name = "%s%06d" % (molecule_name_prefix, molecule_index)
                molecules.append((molecule_name, [atom_index], [], []))
                included_atoms.add(atom_index)
                molecule_index = molecule_index + 1

        return molecules

    @staticmethod
    def write_unit_topology_file(
        path: str, poscar: VaspStructure, config: Dict[str, Any]
    ) -> None:
        """独立分子・独立フラグメント型の RMC_POT topology を書く。

        ``write_topology`` は、検出した current network を 1 つの flexible molecule として書く。
        それに対して、この関数は unit 間をつながない。各 unit を別々の molecule type として書き、
        unit 内の bond/angle だけを RMC_POT の bonded potential に渡す。

        RMC_POT の観点では、この topology も FNC=4 用である。ただし、拘束の意味は次のように違う。

        * full network topology: 初期構造の個別 Si-O-Si 接続を固定する方向。
        * independent unit topology: SiO2, SiO4 などの unit 内形状だけを保持する方向。

        ユーザーが RMC の自由度を重視する場合、まずはこちらを試す方が安全である。
        """
        unit_config = RmcConstraintWriter.get_unit_topology_config(config)
        molecules = RmcConstraintWriter.build_independent_unit_molecules(poscar, config)

        residue_name = str(unit_config.get("residue_name", "UNIT"))
        nrexcl = int(unit_config.get("nrexcl", 2))
        atom_type_prefix = str(unit_config.get("atom_type_prefix", ""))

        bond_config = unit_config.get("bond", {})
        bond_length_nm = float(QnNetworkAnalysis.get_required(bond_config, "length_nm"))
        bond_force = float(
            QnNetworkAnalysis.get_required(bond_config, "force_kj_mol_nm2")
        )
        bond_sigma = float(QnNetworkAnalysis.get_required(bond_config, "sigma"))

        angle_config = unit_config.get("angle", {})
        angle_theta = float(angle_config.get("theta_degree", 109.47))
        angle_force = float(angle_config.get("force_kj_mol_rad2", 100.0))
        angle_sigma = float(angle_config.get("sigma", 10.0))

        include_name = RmcConstraintWriter.get_force_field_include(unit_config)
        RmcConstraintWriter.write_force_field_stub(path, include_name)

        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "; RMC_POT FNC=4 independent-unit topology generated by qn_network.py\n"
            )
            f.write(
                "; This file keeps only intramolecular / intra-fragment geometry.\n"
            )
            f.write("; No bonds or angles are written between different units.\n")
            f.write(
                "; It is intended to preserve local units while leaving RMC freedom between units.\n"
            )
            f.write('#include "%s"\n' % str(include_name))
            f.write("\n")

            molecule_names = []
            for molecule_name, atom_indices, bonds, angles in molecules:
                molecule_names.append(molecule_name)
                f.write("[ moleculetype ]\n")
                f.write("; molname nrexcl ; RMCindex_offset\n")
                f.write("%s %d ; 0\n\n" % (molecule_name, nrexcl))

                f.write("[ atoms ]\n")
                f.write(
                    "; nr type resnr residue atom cgnr charge mass ; first_RMC_index second_RMC_index\n"
                )
                for local_index, global_index in enumerate(atom_indices):
                    label = poscar.labels[global_index]
                    if atom_type_prefix:
                        atom_type = "%s_%s" % (atom_type_prefix, label)
                    else:
                        atom_type = label
                    charge, mass = QnNetworkAnalysis.get_top_atom_parameter(
                        config, label
                    )
                    atom_name = "%s%d" % (label, global_index + 1)
                    rmc_index = global_index + 1
                    f.write(
                        "%6d %-10s 1 %-6s %-8s %6d % .8f % .8f ; %d %d\n"
                        % (
                            local_index + 1,
                            atom_type,
                            residue_name,
                            atom_name,
                            local_index + 1,
                            charge,
                            mass,
                            rmc_index,
                            rmc_index,
                        )
                    )

                f.write("\n[ bonds ]\n")
                f.write("; i j funct b_nm kb_kJ_mol_nm2 ; sigma\n")
                for local_i, local_j in bonds:
                    f.write(
                        "%6d %6d 1 %.8f %.8f ; %.8f\n"
                        % (
                            local_i + 1,
                            local_j + 1,
                            bond_length_nm,
                            bond_force,
                            bond_sigma,
                        )
                    )

                if len(angles) > 0:
                    f.write("\n[ angles ]\n")
                    f.write("; i j k funct theta_deg ktheta_kJ_mol_rad2 ; sigma\n")
                    for local_i, local_j, local_k in angles:
                        f.write(
                            "%6d %6d %6d 1 %.8f %.8f ; %.8f\n"
                            % (
                                local_i + 1,
                                local_j + 1,
                                local_k + 1,
                                angle_theta,
                                angle_force,
                                angle_sigma,
                            )
                        )
                f.write("\n")

            f.write("[ system ]\n")
            f.write("Independent local units generated from RMC/POSCAR structure\n\n")
            f.write("[ molecules ]\n")
            for molecule_name in molecule_names:
                f.write("%s 1\n" % molecule_name)

    @staticmethod
    def write_dat_snippets_file(prefix: str, config: Dict[str, Any]) -> None:
        """RMC_POT dat ファイルへ転記するための補助 snippet を書く。

        CUT-OFF は RMC_POT の partial order、すなわち atom type 順の上三角順で出力する。
        例: atom_types が [Si, O] なら Si-Si, Si-O, O-O の順になる。

        実際の dat ファイルが old fixed format か free format かで書く位置は変わるため、
        ここでは完全な dat ファイルではなく snippet として出力する。

        ファイル名では FNC と topology を混同しない。
        ``*_rmc_fnc3.fnc`` は FNC ファイルである。
        ``*_rmc_unit.top`` は topology ファイルであり、FNC ファイルではない。
        """
        atom_types = QnNetworkAnalysis.get_structure_atom_types(config)
        if atom_types is None:
            raise ConfigError("config に structure.atom_types がありません。")
        dat_config = QnNetworkAnalysis.get_dat_config(config)
        cutoffs = QnNetworkAnalysis.get_required(dat_config, "hard_sphere_cutoffs")
        pair_order = []
        cutoff_values = []
        # RMC_POT partial order は atom type 順の上三角行列順。
        # 例: A, B, C なら A-A, A-B, A-C, B-B, B-C, C-C。
        for i, type_i in enumerate(atom_types):
            for j in range(i, len(atom_types)):
                type_j = atom_types[j]
                key1 = "%s-%s" % (type_i, type_j)
                key2 = "%s-%s" % (type_j, type_i)
                if key1 in cutoffs:
                    value = cutoffs[key1]
                elif key2 in cutoffs:
                    value = cutoffs[key2]
                else:
                    raise ConfigError(
                        "hard_sphere_cutoffs に %s/%s がありません。" % (key1, key2)
                    )
                pair_order.append(key1)
                cutoff_values.append(float(value))

        fnc3_path = prefix + "_dat_snippet_rmc_fnc3.txt"
        with open(fnc3_path, "w", encoding="utf-8") as f:
            f.write("# RMC_POT dat snippet for FNC=3\n")
            f.write("# Atom type order: %s\n" % " ".join(atom_types))
            f.write("# Partial order: %s\n" % " ".join(pair_order))
            f.write("# CUT-OFF values in Angstrom, RMC partial order.\n")
            f.write("CUT-OFF = %s\n" % " ".join("%.6f" % x for x in cutoff_values))
            f.write("# Fixed neighbour constraint mode. Use the generated .fnc file.\n")
            f.write(
                "# In old fixed-format input this corresponds to fnc=3 and filename below.\n"
            )
            f.write("FNC = 3 %s_rmc_fnc3.fnc\n" % os.path.basename(prefix))

        top_path = prefix + "_dat_snippet_rmc_unit_top.txt"
        with open(top_path, "w", encoding="utf-8") as f:
            f.write("# RMC_POT dat snippet for flexible molecule topology\n")
            f.write("# Atom type order: %s\n" % " ".join(atom_types))
            f.write("# Partial order: %s\n" % " ".join(pair_order))
            f.write("CUT-OFF = %s\n" % " ".join("%.6f" % x for x in cutoff_values))
            f.write(
                "# RMC_POT uses FNC=4 switch for flexible molecules. The .top file itself is not an FNC file.\n"
            )
            f.write(
                "# Exact keyword placement depends on the old/free-format dat file being used.\n"
            )
            f.write("FNC = 4\n")
            f.write("TOPOLOGY = %s_rmc_unit.top\n" % os.path.basename(prefix))
            f.write(
                "# If non-bonded potential is not used, bonded terms contribute to normal chi2.\n"
            )
            f.write(
                "# Start with weak angle/bond weights, then tighten after checking acceptance ratio.\n"
            )


class QnNetworkBuilder(object):
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
    def from_poscar(cls, poscar_name: str, config_name: str) -> "QnNetworkBuilder":
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

    def write_qn_csv(self, path: str) -> None:
        self.analysis.write_qn_csv(path)

    def write_network_bonds_csv(self, path: str) -> None:
        self.analysis.write_network_bonds_csv(path)

    def write_report(self, path: str) -> None:
        self.analysis.write_report(path)

    def write_analysis(self, prefix: str) -> None:
        self.analysis.write_analysis(prefix)

    def write_fnc3(self, path: str, title: Optional[str] = None) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_fnc3(path, title=title)

    def write_unit_topology(self, path: str) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_unit_topology(path)

    def write_network_topology(self, path: str) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_network_topology(path)

    def write_dat_snippets(self, prefix: str) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_dat_snippets(prefix)

    def write_all(self, prefix: str) -> None:
        writer = RmcConstraintWriter(self.analysis)
        writer.write_rmc_inputs(prefix)
        self.analysis.write_analysis(prefix)
