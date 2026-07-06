#!/usr/bin/env python3
"""
SiO2 glass 用 RMC_POT FNC / cutoff 作成スクリプト。

入力は VASP POSCAR/CONTCAR 形式を想定する。
元素名行が無い VASP4 形式の場合は、--elements で原子種順を指定する。
RMC_POT の固定フォーマット cfg が Si block, O block の順である前提なら、
生成される FNC index はそのまま使える。
"""
import argparse
import csv
import itertools
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Sequence, Optional, Set

import numpy as np


Pair = Tuple[int, int]
FncPair = Tuple[int, int, int]


def read_poscar(path: str, elements_arg: Optional[str]) -> Tuple[List[str], np.ndarray, np.ndarray]:
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    scale = float(lines[1].split()[0])
    cell = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)], dtype=float)
    cell = cell * scale

    tokens5 = lines[5].split()
    has_symbol_line = False
    try:
        [int(x) for x in tokens5]
    except ValueError:
        has_symbol_line = True

    if has_symbol_line:
        elements = tokens5
        counts = [int(x) for x in lines[6].split()]
        coord_mode_index = 7
    else:
        counts = [int(x) for x in tokens5]
        coord_mode_index = 6
        if elements_arg is None:
            if len(counts) == 2:
                elements = ["Si", "O"]
            else:
                raise ValueError("元素名行が無い POSCAR です。--elements で指定してください。")
        else:
            elements = [x.strip() for x in elements_arg.split(",")]

    if len(elements) != len(counts):
        raise ValueError("元素数と個数行の数が一致しません。")

    coord_mode = lines[coord_mode_index].lower()
    start = coord_mode_index + 1
    total = sum(counts)
    frac_or_cart = np.array([[float(x) for x in lines[start + i].split()[:3]] for i in range(total)], dtype=float)

    if coord_mode.startswith("d"):
        frac = frac_or_cart.copy()
    else:
        inv_cell = np.linalg.inv(cell)
        frac = frac_or_cart @ inv_cell

    labels = []
    for element, count in zip(elements, counts):
        for _ in range(count):
            labels.append(element)

    return labels, cell, frac


def pbc_distance(i: int, j: int, frac: np.ndarray, cell: np.ndarray) -> float:
    df = frac[j] - frac[i]
    df = df - np.rint(df)
    cart = df @ cell
    return float(np.linalg.norm(cart))


def element_indices(labels: Sequence[str], element: str) -> List[int]:
    result = []
    for i, label in enumerate(labels):
        if label == element:
            result.append(i)
    return result


def detect_si_o_bonds(
    si_indices: Sequence[int],
    o_indices: Sequence[int],
    frac: np.ndarray,
    cell: np.ndarray,
    mode: str,
    si_o_cut: float,
    nearest_n: int,
) -> Dict[int, List[int]]:
    bonds = {}
    for si in si_indices:
        distances = []
        for o in o_indices:
            distances.append((pbc_distance(si, o, frac, cell), o))
        distances.sort()

        selected = []
        if mode == "cutoff":
            for distance, o in distances:
                if distance <= si_o_cut:
                    selected.append(o)
        elif mode == "nearest":
            for distance, o in distances[:nearest_n]:
                selected.append(o)
        else:
            raise ValueError("mode は cutoff または nearest です。")

        bonds[si] = selected
    return bonds


def build_fnc_pairs(
    bonds: Dict[int, List[int]],
    frac: np.ndarray,
    cell: np.ndarray,
    include_angle_pairs: bool,
) -> List[FncPair]:
    pair_types = {}

    for si, oxygens in bonds.items():
        for o in oxygens:
            a = min(si, o)
            b = max(si, o)
            pair_types[(a, b)] = 1

    if include_angle_pairs:
        o_to_si = defaultdict(list)
        for si, oxygens in bonds.items():
            for o in oxygens:
                o_to_si[o].append(si)

        for o, silicons in o_to_si.items():
            for si1, si2 in itertools.combinations(sorted(silicons), 2):
                a = min(si1, si2)
                b = max(si1, si2)
                pair_types[(a, b)] = 2

        for si, oxygens in bonds.items():
            for o1, o2 in itertools.combinations(sorted(oxygens), 2):
                a = min(o1, o2)
                b = max(o1, o2)
                pair_types[(a, b)] = 3

    fnc_pairs = []
    for pair, type_id in sorted(pair_types.items()):
        fnc_pairs.append((pair[0], pair[1], type_id))
    return fnc_pairs


def write_fnc(path: str, atom_count: int, fnc_pairs: Sequence[FncPair], ranges: Dict[int, Tuple[float, float]]) -> None:
    neighbours = defaultdict(list)
    for i, j, type_id in fnc_pairs:
        neighbours[i].append((j, type_id))
        neighbours[j].append((i, type_id))

    max_type = max(ranges.keys())
    with open(path, "w", encoding="utf-8") as f:
        f.write("Fixed neighbours constraints (.FNC) file for SiO2\n")
        f.write("No. of possible rmin-rmax pairs:\n")
        f.write("%d\n" % max_type)
        f.write(" ".join("%.8f" % ranges[i][0] for i in range(1, max_type + 1)) + "\n")
        f.write(" ".join("%.8f" % ranges[i][1] for i in range(1, max_type + 1)) + "\n")
        f.write("%d\n" % atom_count)
        for atom in range(atom_count):
            items = sorted(neighbours.get(atom, []))
            atom_index = atom + 1
            f.write("%d %d\n" % (atom_index, len(items)))
            if items:
                f.write(" ".join(str(j + 1) for j, type_id in items) + "\n")
                f.write(" ".join(str(type_id) for j, type_id in items) + "\n")


def write_qn_csv(path: str, si_indices: Sequence[int], bonds: Dict[int, List[int]], o_to_si: Dict[int, List[int]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["si_rmc_index", "q_n", "n_si_o", "n_bridging_o", "o_rmc_indices"])
        for si in si_indices:
            oxygens = bonds[si]
            q_n = 0
            for o in oxygens:
                if len(o_to_si[o]) >= 2:
                    q_n = q_n + 1
            writer.writerow([si + 1, q_n, len(oxygens), q_n, " ".join(str(o + 1) for o in oxygens)])


def summarize_distances(fnc_pairs: Sequence[FncPair], frac: np.ndarray, cell: np.ndarray) -> Dict[int, List[float]]:
    result = defaultdict(list)
    for i, j, type_id in fnc_pairs:
        result[type_id].append(pbc_distance(i, j, frac, cell))
    return result


def percentile_text(values: Sequence[float]) -> str:
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return "count=0"
    ps = np.percentile(arr, [0, 1, 5, 50, 95, 99, 100])
    return "count=%d min=%.4f p1=%.4f p5=%.4f p50=%.4f p95=%.4f p99=%.4f max=%.4f" % (
        len(arr), ps[0], ps[1], ps[2], ps[3], ps[4], ps[5], ps[6]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("poscar")
    parser.add_argument("--elements", default=None)
    parser.add_argument("--si-o-cut", type=float, default=1.80)
    parser.add_argument("--mode", choices=["cutoff", "nearest"], default="nearest")
    parser.add_argument("--nearest-n", type=int, default=4)
    parser.add_argument("--no-angle-pairs", action="store_true")
    parser.add_argument("--prefix", default="SiO2_750_S1_nvt4")
    args = parser.parse_args()

    labels, cell, frac = read_poscar(args.poscar, args.elements)
    si_indices = element_indices(labels, "Si")
    o_indices = element_indices(labels, "O")
    if not si_indices or not o_indices:
        raise ValueError("Si と O の atom block が必要です。")

    bonds = detect_si_o_bonds(si_indices, o_indices, frac, cell, args.mode, args.si_o_cut, args.nearest_n)
    o_to_si = defaultdict(list)
    for si, oxygens in bonds.items():
        for o in oxygens:
            o_to_si[o].append(si)

    include_angle_pairs = True
    if args.no_angle_pairs:
        include_angle_pairs = False

    fnc_pairs = build_fnc_pairs(bonds, frac, cell, include_angle_pairs)

    ranges = {
        1: (1.45, 1.85),
    }
    if include_angle_pairs:
        ranges[2] = (2.75, 3.45)
        ranges[3] = (2.30, 3.10)

    fnc_path = args.prefix + ".fnc"
    qn_path = args.prefix + "_qn.csv"
    report_path = args.prefix + "_rmc_constraints_report.txt"
    dat_snippet_path = args.prefix + "_dat_snippet.txt"

    write_fnc(fnc_path, len(labels), fnc_pairs, ranges)
    write_qn_csv(qn_path, si_indices, bonds, o_to_si)

    volume = abs(float(np.linalg.det(cell)))
    density = len(labels) / volume
    q_counter = Counter()
    si_cn_counter = Counter()
    for si in si_indices:
        oxygens = bonds[si]
        si_cn_counter[len(oxygens)] = si_cn_counter[len(oxygens)] + 1
        q_n = 0
        for o in oxygens:
            if len(o_to_si[o]) >= 2:
                q_n = q_n + 1
        q_counter[q_n] = q_counter[q_n] + 1

    o_cn_counter = Counter()
    for o in o_indices:
        o_cn_counter[len(o_to_si[o])] = o_cn_counter[len(o_to_si[o])] + 1

    by_type = summarize_distances(fnc_pairs, frac, cell)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("SiO2 RMC_POT constraint report\n")
        f.write("atom_count = %d\n" % len(labels))
        f.write("Si_count = %d\n" % len(si_indices))
        f.write("O_count = %d\n" % len(o_indices))
        f.write("cell_volume_A3 = %.10f\n" % volume)
        f.write("number_density_A3 = %.10f\n" % density)
        f.write("bond_detection_mode = %s\n" % args.mode)
        f.write("si_o_cut_A = %.4f\n" % args.si_o_cut)
        f.write("nearest_n = %d\n" % args.nearest_n)
        f.write("Si-O coordination distribution = %s\n" % dict(sorted(si_cn_counter.items())))
        f.write("O-Si coordination distribution = %s\n" % dict(sorted(o_cn_counter.items())))
        f.write("Qn distribution from detected network = %s\n" % dict(sorted(q_counter.items())))
        f.write("RMC_POT fixed-format cutoff order for Si,O: Si-Si Si-O O-O\n")
        f.write("recommended hard-sphere cutoffs_A = 2.40 1.25 2.10\n")
        f.write("FNC type 1 = Si-O bond, range 1.45 1.85 A\n")
        if include_angle_pairs:
            f.write("FNC type 2 = Si-Si through bridging O, range 2.75 3.45 A\n")
            f.write("FNC type 3 = O-O in SiO4 tetrahedron, range 2.30 3.10 A\n")
        for type_id in sorted(by_type.keys()):
            f.write("FNC type %d distance stats: %s\n" % (type_id, percentile_text(by_type[type_id])))

    with open(dat_snippet_path, "w", encoding="utf-8") as f:
        f.write("# RMC_POT fixed-format .dat values for atom order: Si O\n")
        f.write("comment SiO2\n")
        f.write("%.10f ! number density\n" % density)
        f.write("2.40 1.25 2.10 ! cut offs: Si-Si Si-O O-O\n")
        f.write("0.01 0.01 ! maximum moves: Si O\n")
        f.write("3 ! FNC switch; use SiO2_750_S1_nvt4.fnc\n")

    print("created", fnc_path)
    print("created", qn_path)
    print("created", report_path)
    print("created", dat_snippet_path)


if __name__ == "__main__":
    main()
