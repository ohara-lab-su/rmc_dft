# -*- coding: utf-8 -*-
"""Qn/network state analysis for one VASP/POSCAR structure.

This module contains only reusable parts.
The execution script decides file names and output names by plain variables.
"""

from __future__ import print_function

import csv
import json
import math
from collections import defaultdict, deque


class Structure(object):
    """Simple VASP/POSCAR structure container."""

    def __init__(self, symbols, positions, lattice):
        self.symbols = symbols
        self.positions = positions
        self.lattice = lattice
        self.inv_lattice = invert_3x3(lattice)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def mat_vec(m, v):
    return [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]


def invert_3x3(m):
    a = m[0][0]
    b = m[0][1]
    c = m[0][2]
    d = m[1][0]
    e = m[1][1]
    f = m[1][2]
    g = m[2][0]
    h = m[2][1]
    i = m[2][2]

    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1.0e-14:
        raise ValueError("lattice matrix is singular")

    inv = [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]
    return inv


def frac_to_cart(frac, lattice):
    x = frac[0] * lattice[0][0] + frac[1] * lattice[1][0] + frac[2] * lattice[2][0]
    y = frac[0] * lattice[0][1] + frac[1] * lattice[1][1] + frac[2] * lattice[2][1]
    z = frac[0] * lattice[0][2] + frac[1] * lattice[1][2] + frac[2] * lattice[2][2]
    return [x, y, z]


def cart_to_frac(cart, inv_lattice):
    return mat_vec(inv_lattice, cart)


def minimum_image_distance(pos_a, pos_b, lattice, inv_lattice):
    delta = [pos_b[0] - pos_a[0], pos_b[1] - pos_a[1], pos_b[2] - pos_a[2]]
    frac = cart_to_frac(delta, inv_lattice)
    frac = [frac[0] - round(frac[0]), frac[1] - round(frac[1]), frac[2] - round(frac[2])]
    cart = frac_to_cart(frac, lattice)
    return math.sqrt(dot(cart, cart))


def read_vasp(path):
    with open(path, "r") as handle:
        raw_lines = handle.readlines()

    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped != "":
            lines.append(stripped)

    if len(lines) < 8:
        raise ValueError("VASP file is too short: " + path)

    scale = float(lines[1].split()[0])
    lattice = []
    for row_index in range(2, 5):
        values = lines[row_index].split()
        lattice.append([
            float(values[0]) * scale,
            float(values[1]) * scale,
            float(values[2]) * scale,
        ])

    names = lines[5].split()
    counts = []
    for value in lines[6].split():
        counts.append(int(value))

    coord_line_index = 7
    if lines[coord_line_index].lower().startswith("s"):
        coord_line_index += 1

    coord_mode = lines[coord_line_index].lower()
    position_start = coord_line_index + 1

    symbols = []
    for name, count in zip(names, counts):
        for _ in range(count):
            symbols.append(name)

    positions = []
    for atom_index in range(len(symbols)):
        values = lines[position_start + atom_index].split()
        vec = [float(values[0]), float(values[1]), float(values[2])]
        if coord_mode.startswith("d"):
            pos = frac_to_cart(vec, lattice)
        else:
            pos = [vec[0] * scale, vec[1] * scale, vec[2] * scale]
        positions.append(pos)

    return Structure(symbols, positions, lattice)


def read_config(path):
    with open(path, "r") as handle:
        return json.load(handle)


def analyze_network_state(structure, config):
    qn_config = config["qn"]
    central_types = set(qn_config["central_types"])
    bridge_types = set(qn_config["bridge_types"])
    r_min = float(qn_config["first_min"])
    r_max = float(qn_config["first_max"])

    central_indices = []
    bridge_indices = []
    for atom_index, symbol in enumerate(structure.symbols):
        if symbol in central_types:
            central_indices.append(atom_index)
        if symbol in bridge_types:
            bridge_indices.append(atom_index)

    central_to_bridges = defaultdict(list)
    bridge_to_centrals = defaultdict(list)
    bonds = []

    for central_index in central_indices:
        for bridge_index in bridge_indices:
            distance = minimum_image_distance(
                structure.positions[central_index],
                structure.positions[bridge_index],
                structure.lattice,
                structure.inv_lattice,
            )
            if distance >= r_min and distance <= r_max:
                central_to_bridges[central_index].append(bridge_index)
                bridge_to_centrals[bridge_index].append(central_index)
                bonds.append((central_index, bridge_index, distance))

    atom_rows = build_atom_rows(structure, central_indices, bridge_indices, central_to_bridges, bridge_to_centrals)
    qn_counts = count_qn(structure, central_indices, central_to_bridges, bridge_to_centrals)
    oxygen_counts = count_oxygen_coordination(bridge_indices, bridge_to_centrals)
    components = build_central_components(central_indices, bridge_indices, bridge_to_centrals)

    result = {
        "natoms": len(structure.symbols),
        "central_count": len(central_indices),
        "bridge_count": len(bridge_indices),
        "bond_count": len(bonds),
        "qn_counts": qn_counts,
        "oxygen_counts": oxygen_counts,
        "components": components,
        "atom_rows": atom_rows,
        "bonds": bonds,
    }
    return result


def build_atom_rows(structure, central_indices, bridge_indices, central_to_bridges, bridge_to_centrals):
    rows = []
    for atom_index in central_indices:
        bridge_count = 0
        for bridge_index in central_to_bridges[atom_index]:
            if len(bridge_to_centrals[bridge_index]) >= 2:
                bridge_count += 1
        rows.append({
            "atom_index_1based": atom_index + 1,
            "symbol": structure.symbols[atom_index],
            "role": "central",
            "coordination": len(central_to_bridges[atom_index]),
            "network_label": "Q" + str(bridge_count),
        })

    for atom_index in bridge_indices:
        coordination = len(bridge_to_centrals[atom_index])
        rows.append({
            "atom_index_1based": atom_index + 1,
            "symbol": structure.symbols[atom_index],
            "role": "bridge",
            "coordination": coordination,
            "network_label": "O" + str(coordination),
        })
    return rows


def count_qn(structure, central_indices, central_to_bridges, bridge_to_centrals):
    counts = defaultdict(int)
    for atom_index in central_indices:
        bridge_count = 0
        for bridge_index in central_to_bridges[atom_index]:
            if len(bridge_to_centrals[bridge_index]) >= 2:
                bridge_count += 1
        counts["Q" + str(bridge_count)] += 1
    return dict(counts)


def count_oxygen_coordination(bridge_indices, bridge_to_centrals):
    counts = defaultdict(int)
    for atom_index in bridge_indices:
        coordination = len(bridge_to_centrals[atom_index])
        counts["O" + str(coordination)] += 1
    return dict(counts)


def build_central_components(central_indices, bridge_indices, bridge_to_centrals):
    graph = defaultdict(set)
    for atom_index in central_indices:
        graph[atom_index] = set()

    link_count = 0
    for bridge_index in bridge_indices:
        centrals = bridge_to_centrals[bridge_index]
        if len(centrals) >= 2:
            link_count += 1
            for i in range(len(centrals)):
                for j in range(i + 1, len(centrals)):
                    graph[centrals[i]].add(centrals[j])
                    graph[centrals[j]].add(centrals[i])

    visited = set()
    sizes = []
    for atom_index in central_indices:
        if atom_index in visited:
            continue
        queue = deque([atom_index])
        visited.add(atom_index)
        size = 0
        while len(queue) > 0:
            current = queue.popleft()
            size += 1
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        sizes.append(size)

    sizes.sort(reverse=True)
    largest_fraction = 0.0
    if len(central_indices) > 0 and len(sizes) > 0:
        largest_fraction = float(sizes[0]) / float(len(central_indices))

    return {
        "component_count": len(sizes),
        "component_sizes": sizes,
        "largest_component_fraction": largest_fraction,
        "bridge_link_count": link_count,
    }


def format_fraction(count, total):
    if total <= 0:
        return "0.000000"
    return "{0:.6f}".format(float(count) / float(total))


def write_report(result, output_path):
    with open(output_path, "w") as handle:
        handle.write("Qn network state\n")
        handle.write("================\n")
        handle.write("natoms: {0}\n".format(result["natoms"]))
        handle.write("central_count: {0}\n".format(result["central_count"]))
        handle.write("bridge_count: {0}\n".format(result["bridge_count"]))
        handle.write("central-bridge bond_count: {0}\n".format(result["bond_count"]))
        handle.write("\n")

        handle.write("Qn distribution\n")
        for key in sorted(result["qn_counts"].keys()):
            count = result["qn_counts"][key]
            fraction = format_fraction(count, result["central_count"])
            handle.write("{0}: {1}  fraction={2}\n".format(key, count, fraction))
        handle.write("\n")

        handle.write("Bridge atom coordination distribution\n")
        for key in sorted(result["oxygen_counts"].keys()):
            count = result["oxygen_counts"][key]
            fraction = format_fraction(count, result["bridge_count"])
            handle.write("{0}: {1}  fraction={2}\n".format(key, count, fraction))
        handle.write("\n")

        components = result["components"]
        handle.write("Network components among central atoms\n")
        handle.write("component_count: {0}\n".format(components["component_count"]))
        handle.write("largest_component_fraction: {0:.6f}\n".format(components["largest_component_fraction"]))
        handle.write("bridge_link_count: {0}\n".format(components["bridge_link_count"]))
        handle.write("component_sizes: {0}\n".format(components["component_sizes"]))


def write_atom_csv(result, output_path):
    fieldnames = ["atom_index_1based", "symbol", "role", "coordination", "network_label"]
    with open(output_path, "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in result["atom_rows"]:
            writer.writerow(row)


def write_bond_csv(result, output_path):
    with open(output_path, "w") as handle:
        writer = csv.writer(handle)
        writer.writerow(["central_index_1based", "bridge_index_1based", "distance_angstrom"])
        for central_index, bridge_index, distance in result["bonds"]:
            writer.writerow([central_index + 1, bridge_index + 1, "{0:.8f}".format(distance)])


def analyze_vasp_file(structure_path, config_path, output_prefix):
    structure = read_vasp(structure_path)
    config = read_config(config_path)
    result = analyze_network_state(structure, config)
    write_report(result, output_prefix + "_network_state.txt")
    write_atom_csv(result, output_prefix + "_atoms.csv")
    write_bond_csv(result, output_prefix + "_bonds.csv")
    return result
