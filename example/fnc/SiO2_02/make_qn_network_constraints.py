#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMC_POT 用 Qn ネットワーク解析、FNC=3 用 .fnc、FNC=4 用 GROMACS 型 topology を生成する。

主用途:
    central-bridge-second で定義される Qn ネットワーク。
    例: Si-O-Si, B-O-Si/B, P-O-P, Ge-O-Ge。

入力:
    POSCAR/CONTCAR/VASP 形式。
    元素名行がない VASP4 形式では config JSON の atom_types を使う。

出力:
    *_qn.csv
    *_network_bonds.csv
    *_fnc3.fnc
    *_fnc4.top
    *_dat_snippet_fnc3.txt
    *_dat_snippet_fnc4.txt
    *_report.txt

注意:
    RMC_POT の cfg と POSCAR の原子順が一致していることを前提に RMC index を出力する。
    cfg 側で atom block 順や atom index が違う場合は、同じ順序に変換してから使う。
"""
from __future__ import print_function

import argparse
import csv
import itertools
import json
import math
import os
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


class ConfigError(Exception):
    """設定ファイルまたは入力構造が不正な場合の例外。"""


class PoscarData(object):
    """POSCAR/CONTCAR から読んだ構造データ。"""

    def __init__(self, labels: List[str], cell: np.ndarray, frac: np.ndarray) -> None:
        self.labels = labels
        self.cell = cell
        self.frac = frac

    @property
    def atom_count(self) -> int:
        return len(self.labels)


class NetworkData(object):
    """Qn ネットワーク解析で得られる接続情報。"""

    def __init__(self) -> None:
        self.first_map = defaultdict(list)       # type: Dict[int, List[int]]
        self.bridge_second_map = defaultdict(list)  # type: Dict[int, List[int]]
        self.qn_by_central = {}                  # type: Dict[int, int]
        self.bridges_by_central = {}             # type: Dict[int, List[int]]
        self.second_by_bridge_for_central = {}   # type: Dict[Tuple[int, int], List[int]]
        self.bond_pairs = set()                  # type: Set[Pair]
        self.fnc_pairs = []                      # type: List[TypedPair]
        self.fnc_type_names = {}                 # type: Dict[int, str]
        self.angles = []                         # type: List[Tuple[int, int, int, str]]


def read_poscar(path: str, atom_types_from_config: Optional[List[str]]) -> PoscarData:
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
            raise ConfigError("元素名行がない POSCAR です。config の atom_types を指定してください。")
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
    return PoscarData(labels, cell, frac)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def get_required(config: Dict[str, Any], key: str) -> Any:
    if key not in config:
        raise ConfigError("config に %s がありません。" % key)
    return config[key]


def pbc_vector(i: int, j: int, frac: np.ndarray, cell: np.ndarray) -> np.ndarray:
    df = frac[j] - frac[i]
    df = df - np.rint(df)
    return df.dot(cell)


def pbc_distance(i: int, j: int, frac: np.ndarray, cell: np.ndarray) -> float:
    vec = pbc_vector(i, j, frac, cell)
    return float(np.linalg.norm(vec))


def angle_degree(i: int, j: int, k: int, frac: np.ndarray, cell: np.ndarray) -> float:
    v1 = pbc_vector(j, i, frac, cell)
    v2 = pbc_vector(j, k, frac, cell)
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


def pair_key(i: int, j: int) -> Pair:
    if i < j:
        return (i, j)
    return (j, i)


def select_indices(labels: Sequence[str], wanted_types: Sequence[str]) -> List[int]:
    wanted = set(wanted_types)
    result = []
    for i, label in enumerate(labels):
        if label in wanted:
            result.append(i)
    return result


def find_neighbors(
    centers: Sequence[int],
    candidates: Sequence[int],
    poscar: PoscarData,
    min_distance: float,
    max_distance: float,
    exclude_self: bool,
) -> Dict[int, List[int]]:
    result = {}
    for center in centers:
        hits = []
        for candidate in candidates:
            if exclude_self:
                if center == candidate:
                    continue
            distance = pbc_distance(center, candidate, poscar.frac, poscar.cell)
            if distance >= min_distance and distance <= max_distance:
                hits.append(candidate)
        hits.sort()
        result[center] = hits
    return result


def build_network(poscar: PoscarData, config: Dict[str, Any]) -> NetworkData:
    qn_config = get_required(config, "qn")
    central_types = get_required(qn_config, "central_types")
    bridge_types = get_required(qn_config, "bridge_types")
    second_types = get_required(qn_config, "second_types")
    first_min = float(get_required(qn_config, "first_min"))
    first_max = float(get_required(qn_config, "first_max"))
    second_min = float(get_required(qn_config, "second_min"))
    second_max = float(get_required(qn_config, "second_max"))

    central_indices = select_indices(poscar.labels, central_types)
    bridge_indices = select_indices(poscar.labels, bridge_types)
    second_indices = select_indices(poscar.labels, second_types)

    if len(central_indices) == 0:
        raise ConfigError("central_types に対応する原子がありません。")
    if len(bridge_indices) == 0:
        raise ConfigError("bridge_types に対応する原子がありません。")
    if len(second_indices) == 0:
        raise ConfigError("second_types に対応する原子がありません。")

    data = NetworkData()
    first_mode = str(qn_config.get("first_mode", "cutoff"))
    first_map = {}
    if first_mode == "cutoff":
        first_map = find_neighbors(central_indices, bridge_indices, poscar, first_min, first_max, True)
    elif first_mode == "nearest":
        nearest_n = int(qn_config.get("first_nearest_n", 4))
        for central in central_indices:
            distances = []
            for bridge in bridge_indices:
                distance = pbc_distance(central, bridge, poscar.frac, poscar.cell)
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

    second_use_first_network = bool(qn_config.get("second_use_first_network", False))
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
        bridge_second_map = find_neighbors(bridge_indices, second_indices, poscar, second_min, second_max, True)

    data.first_map = first_map
    data.bridge_second_map = bridge_second_map

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
            data.bond_pairs.add(pair_key(central, bridge))

    for bridge, seconds in bridge_second_map.items():
        for second in seconds:
            data.bond_pairs.add(pair_key(bridge, second))

    return data


def add_typed_pair(pair_types: Dict[Pair, int], i: int, j: int, type_id: int) -> None:
    key = pair_key(i, j)
    if key in pair_types:
        old_type_id = pair_types[key]
        if type_id < old_type_id:
            pair_types[key] = type_id
    else:
        pair_types[key] = type_id


def build_fnc3_pairs(poscar: PoscarData, config: Dict[str, Any], data: NetworkData) -> None:
    fnc3_config = get_required(config, "fnc3")
    constraints = get_required(fnc3_config, "constraints")

    pair_types = {}  # type: Dict[Pair, int]
    type_names = {}  # type: Dict[int, str]

    for item in constraints:
        type_id = int(get_required(item, "type_id"))
        name = str(get_required(item, "name"))
        source = str(get_required(item, "source"))
        type_names[type_id] = name

        if source == "central_bridge_bonds":
            for central, bridges in data.first_map.items():
                for bridge in bridges:
                    add_typed_pair(pair_types, central, bridge, type_id)

        elif source == "bridge_second_bonds":
            for bridge, seconds in data.bridge_second_map.items():
                for second in seconds:
                    add_typed_pair(pair_types, bridge, second, type_id)

        elif source == "central_second_through_bridge":
            for central, bridges in data.first_map.items():
                for bridge in bridges:
                    second_hits = data.second_by_bridge_for_central[(central, bridge)]
                    for second in second_hits:
                        add_typed_pair(pair_types, central, second, type_id)

        elif source == "bridge_bridge_around_central":
            for central, bridges in data.first_map.items():
                sorted_bridges = sorted(bridges)
                for bridge1, bridge2 in itertools.combinations(sorted_bridges, 2):
                    add_typed_pair(pair_types, bridge1, bridge2, type_id)

        else:
            raise ConfigError("未知の fnc3 constraint source です: %s" % source)

    typed_pairs = []
    for pair in sorted(pair_types.keys()):
        typed_pairs.append((pair[0], pair[1], pair_types[pair]))
    data.fnc_pairs = typed_pairs
    data.fnc_type_names = type_names


def collect_fnc3_ranges(config: Dict[str, Any]) -> Dict[int, Tuple[float, float]]:
    result = {}
    fnc3_config = get_required(config, "fnc3")
    constraints = get_required(fnc3_config, "constraints")
    for item in constraints:
        type_id = int(get_required(item, "type_id"))
        rmin = float(get_required(item, "rmin"))
        rmax = float(get_required(item, "rmax"))
        result[type_id] = (rmin, rmax)
    return result


def write_fnc(path: str, atom_count: int, typed_pairs: Sequence[TypedPair], ranges: Dict[int, Tuple[float, float]], title: str) -> None:
    neighbours = defaultdict(list)  # type: Dict[int, List[Tuple[int, int]]]
    for i, j, type_id in typed_pairs:
        neighbours[i].append((j, type_id))
        neighbours[j].append((i, type_id))

    max_type = 0
    for type_id in ranges.keys():
        if type_id > max_type:
            max_type = type_id

    with open(path, "w", encoding="utf-8") as f:
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


def write_qn_csv(path: str, poscar: PoscarData, data: NetworkData) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "central_rmc_index",
            "central_type",
            "q_n",
            "first_bridge_count",
            "bridging_bridge_count",
            "bridge_rmc_indices",
            "bridge_types",
        ])
        for central in sorted(data.qn_by_central.keys()):
            bridges = data.bridges_by_central[central]
            bridge_index_text = " ".join(str(bridge + 1) for bridge in bridges)
            bridge_type_text = " ".join(poscar.labels[bridge] for bridge in bridges)
            writer.writerow([
                central + 1,
                poscar.labels[central],
                data.qn_by_central[central],
                len(bridges),
                data.qn_by_central[central],
                bridge_index_text,
                bridge_type_text,
            ])


def write_network_bonds_csv(path: str, poscar: PoscarData, data: NetworkData) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["i_rmc_index", "j_rmc_index", "i_type", "j_type"])
        for i, j in sorted(data.bond_pairs):
            writer.writerow([i + 1, j + 1, poscar.labels[i], poscar.labels[j]])


def summarize_distances(poscar: PoscarData, typed_pairs: Sequence[TypedPair]) -> Dict[int, List[float]]:
    result = defaultdict(list)  # type: Dict[int, List[float]]
    for i, j, type_id in typed_pairs:
        result[type_id].append(pbc_distance(i, j, poscar.frac, poscar.cell))
    return result


def percentile_line(values: Sequence[float]) -> str:
    if len(values) == 0:
        return "count=0"
    arr = np.array(values, dtype=float)
    ps = np.percentile(arr, [0, 1, 5, 50, 95, 99, 100])
    text = "count=%d min=%.4f p1=%.4f p5=%.4f p50=%.4f p95=%.4f p99=%.4f max=%.4f" % (
        len(arr), ps[0], ps[1], ps[2], ps[3], ps[4], ps[5], ps[6]
    )
    return text


def build_angles(poscar: PoscarData, config: Dict[str, Any], data: NetworkData) -> List[Tuple[int, int, int, str]]:
    fnc4_config = get_required(config, "fnc4")
    angle_items = fnc4_config.get("angles", [])
    angles = []  # type: List[Tuple[int, int, int, str]]
    seen = set()  # type: Set[Tuple[int, int, int, str]]

    for item in angle_items:
        name = str(get_required(item, "name"))
        source = str(get_required(item, "source"))
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
                    second_hits = data.second_by_bridge_for_central[(central, bridge)]
                    for second in second_hits:
                        key = (central, bridge, second, name)
                        if key not in seen:
                            seen.add(key)
                            angles.append(key)

        else:
            raise ConfigError("未知の fnc4 angle source です: %s" % source)

    return angles


def find_angle_parameter(config: Dict[str, Any], angle_name: str) -> Dict[str, Any]:
    fnc4_config = get_required(config, "fnc4")
    for item in fnc4_config.get("angles", []):
        name = str(get_required(item, "name"))
        if name == angle_name:
            return item
    raise ConfigError("angle parameter が見つかりません: %s" % angle_name)


def write_topology(path: str, poscar: PoscarData, config: Dict[str, Any], data: NetworkData) -> None:
    fnc4_config = get_required(config, "fnc4")
    molecule_name = str(fnc4_config.get("molecule_name", "QNNET"))
    residue_name = str(fnc4_config.get("residue_name", "QNN"))
    nrexcl = int(fnc4_config.get("nrexcl", 2))

    masses = config.get("masses", {})
    charges = config.get("charges", {})
    atom_type_prefix = str(fnc4_config.get("atom_type_prefix", "rmc"))

    bond_length_nm = float(fnc4_config.get("bond_length_nm", 0.161))
    bond_force = float(fnc4_config.get("bond_force_kj_mol_nm2", 10000.0))
    bond_sigma = float(fnc4_config.get("bond_sigma", 1.0))

    angles = build_angles(poscar, config, data)
    data.angles = angles

    with open(path, "w", encoding="utf-8") as f:
        f.write("; RMC_POT FNC=4 topology generated by make_qn_network_constraints.py\n")
        f.write("; Treats the current Qn network as one flexible molecule.\n")
        f.write("; Check the topology with a short RMC_POT test before production use.\n")
        f.write("#include \"ffUNKNOWN_READ_PAIRS.itp\"\n\n")
        f.write("[ moleculetype ]\n")
        f.write("; molname nrexcl\n")
        f.write("%s %d\n\n" % (molecule_name, nrexcl))

        f.write("[ atoms ]\n")
        f.write("; nr type resnr residue atom cgnr charge mass ; first_RMC_index second_RMC_index\n")
        for i, label in enumerate(poscar.labels):
            atom_type = "%s_%s" % (atom_type_prefix, label)
            charge = 0.0
            if label in charges:
                charge = float(charges[label])
            mass = 1.0
            if label in masses:
                mass = float(masses[label])
            atom_name = "%s%d" % (label, i + 1)
            f.write("%6d %-10s 1 %-6s %-8s %6d % .8f % .8f ; %d %d\n" % (
                i + 1, atom_type, residue_name, atom_name, i + 1, charge, mass, i + 1, i + 1
            ))

        f.write("\n[ bonds ]\n")
        f.write("; i j funct length_nm force_kJ_mol_nm2 ; sigma\n")
        for i, j in sorted(data.bond_pairs):
            f.write("%6d %6d 1 %.8f %.8f ; %.8f\n" % (
                i + 1, j + 1, bond_length_nm, bond_force, bond_sigma
            ))

        f.write("\n[ angles ]\n")
        f.write("; i j k funct theta_deg force_kJ_mol_rad2 ; sigma\n")
        for i, j, k, angle_name in angles:
            param = find_angle_parameter(config, angle_name)
            theta = float(get_required(param, "theta_degree"))
            force = float(get_required(param, "force_kj_mol_rad2"))
            sigma = float(get_required(param, "sigma"))
            f.write("%6d %6d %6d 1 %.8f %.8f ; %.8f ; %s\n" % (
                i + 1, j + 1, k + 1, theta, force, sigma, angle_name
            ))

        f.write("\n[ system ]\n")
        f.write("Qn network generated from RMC/POSCAR structure\n\n")
        f.write("[ molecules ]\n")
        f.write("%s 1\n" % molecule_name)


def write_dat_snippets(prefix: str, config: Dict[str, Any]) -> None:
    atom_types = get_required(config, "atom_types")
    cutoffs = get_required(config, "hard_sphere_cutoffs")
    pair_order = []
    cutoff_values = []
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
                raise ConfigError("hard_sphere_cutoffs に %s/%s がありません。" % (key1, key2))
            pair_order.append(key1)
            cutoff_values.append(float(value))

    fnc3_path = prefix + "_dat_snippet_fnc3.txt"
    with open(fnc3_path, "w", encoding="utf-8") as f:
        f.write("# RMC_POT dat snippet for FNC=3\n")
        f.write("# Atom type order: %s\n" % " ".join(atom_types))
        f.write("# Partial order: %s\n" % " ".join(pair_order))
        f.write("# CUT-OFF values in Angstrom, RMC partial order.\n")
        f.write("CUT-OFF = %s\n" % " ".join("%.6f" % x for x in cutoff_values))
        f.write("# Fixed neighbour constraint mode. Use the generated .fnc file.\n")
        f.write("# In old fixed-format input this corresponds to fnc=3 and filename below.\n")
        f.write("FNC = 3 %s_fnc3.fnc\n" % os.path.basename(prefix))

    fnc4_path = prefix + "_dat_snippet_fnc4.txt"
    with open(fnc4_path, "w", encoding="utf-8") as f:
        f.write("# RMC_POT dat snippet for FNC=4 / flexible molecule topology\n")
        f.write("# Atom type order: %s\n" % " ".join(atom_types))
        f.write("# Partial order: %s\n" % " ".join(pair_order))
        f.write("CUT-OFF = %s\n" % " ".join("%.6f" % x for x in cutoff_values))
        f.write("# FNC=4 means flexible MD-like molecule using bonded potentials from topology.\n")
        f.write("# Exact keyword placement depends on the old/free-format dat file being used.\n")
        f.write("FNC = 4\n")
        f.write("TOPOLOGY = %s_fnc4.top\n" % os.path.basename(prefix))
        f.write("# If non-bonded potential is not used, bonded terms contribute to normal chi2.\n")
        f.write("# Start with weak angle/bond weights, then tighten after checking acceptance ratio.\n")


def write_report(path: str, poscar: PoscarData, config: Dict[str, Any], data: NetworkData) -> None:
    qn_counts = Counter(data.qn_by_central.values())
    distances_by_type = summarize_distances(poscar, data.fnc_pairs)

    with open(path, "w", encoding="utf-8") as f:
        f.write("Qn/RMC_POT constraint generation report\n")
        f.write("====================================\n\n")
        f.write("Atom count: %d\n" % poscar.atom_count)
        f.write("Atom types in structure: %s\n" % " ".join(sorted(set(poscar.labels))))
        f.write("Cell volume: %.8f A^3\n" % abs(float(np.linalg.det(poscar.cell))))
        f.write("Number density: %.10f 1/A^3\n\n" % (float(poscar.atom_count) / abs(float(np.linalg.det(poscar.cell)))))

        f.write("Qn definition\n")
        f.write("-------------\n")
        qn_config = get_required(config, "qn")
        f.write("central_types: %s\n" % " ".join(qn_config["central_types"]))
        f.write("bridge_types : %s\n" % " ".join(qn_config["bridge_types"]))
        f.write("second_types : %s\n" % " ".join(qn_config["second_types"]))
        f.write("first range  : %.4f - %.4f A\n" % (float(qn_config["first_min"]), float(qn_config["first_max"])))
        f.write("second range : %.4f - %.4f A\n\n" % (float(qn_config["second_min"]), float(qn_config["second_max"])))

        f.write("Qn counts\n")
        f.write("---------\n")
        for qn_value in sorted(qn_counts.keys()):
            f.write("Q%d: %d\n" % (qn_value, qn_counts[qn_value]))
        f.write("\n")

        f.write("Network counts\n")
        f.write("--------------\n")
        f.write("central-bridge entries: %d\n" % sum(len(v) for v in data.first_map.values()))
        f.write("bridge-second entries : %d\n" % sum(len(v) for v in data.bridge_second_map.values()))
        f.write("unique bond pairs      : %d\n" % len(data.bond_pairs))
        f.write("FNC=3 pairs            : %d\n" % len(data.fnc_pairs))
        f.write("FNC=4 angles           : %d\n\n" % len(data.angles))

        f.write("FNC=3 distance statistics\n")
        f.write("-------------------------\n")
        for type_id in sorted(distances_by_type.keys()):
            type_name = data.fnc_type_names.get(type_id, "type_%d" % type_id)
            f.write("type %d %s: %s\n" % (type_id, type_name, percentile_line(distances_by_type[type_id])))

        f.write("\nNotes\n")
        f.write("-----\n")
        f.write("FNC=3 is a distance-window constraint.\n")
        f.write("FNC=4 uses bonded potential terms in the generated topology.\n")
        f.write("The generated topology treats the current network as one flexible molecule.\n")
        f.write("For production RMC_POT runs, check the .hst output and acceptance ratio, then tune sigmas/force constants.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("poscar", help="POSCAR/CONTCAR/VASP file")
    parser.add_argument("config", help="JSON configuration file")
    parser.add_argument("--prefix", default="qn_network", help="Output file prefix")
    args = parser.parse_args()

    config = load_config(args.config)
    atom_types = None
    if "atom_types" in config:
        atom_types = list(config["atom_types"])

    poscar = read_poscar(args.poscar, atom_types)
    data = build_network(poscar, config)
    build_fnc3_pairs(poscar, config, data)

    fnc_ranges = collect_fnc3_ranges(config)
    write_fnc(args.prefix + "_fnc3.fnc", poscar.atom_count, data.fnc_pairs, fnc_ranges, args.prefix)
    write_qn_csv(args.prefix + "_qn.csv", poscar, data)
    write_network_bonds_csv(args.prefix + "_network_bonds.csv", poscar, data)
    write_topology(args.prefix + "_fnc4.top", poscar, config, data)
    write_dat_snippets(args.prefix, config)
    write_report(args.prefix + "_report.txt", poscar, config, data)


if __name__ == "__main__":
    main()
