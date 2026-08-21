#!/usr/bin/env python3
"""VASP 構造からゼオライト型フレームワークを解析・表示する。

Usage:
    python analyze_zeolite.py
    python analyze_zeolite.py aaa.vasp
    python analyze_zeolite.py POSCAR

解析本体は ``rmc_dft.util.zeolite`` にあり、このファイルは
入力ファイル探索と表示だけを担当する。
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Iterable, Mapping, Optional

from pymatgen.core import Structure

##########
from rmc_dft.rmc_pot.util.zeolite import (
    ZeoliteCriteria,
    ZeoliteCutoffs,
    analyze_zeolite,
)

##########


DEFAULT_CANDIDATES = (
    Path("aaa.vasp"),
    Path("POSCAR"),
    Path("CONTCAR"),
)

# 現在の RMC 設定に合わせた bond 判定 cutoff。
CUTOFFS = ZeoliteCutoffs(
    si_o=(1.40, 1.90),
    al_o=(1.55, 2.10),
)

# RMC 途中構造の zeolite-like screening 閾値。
# IZA の正式な framework 同定条件ではない。
CRITERIA = ZeoliteCriteria(
    min_t4_fraction=0.90,
    min_bridging_o_fraction=0.90,
    min_largest_component_fraction=0.95,
    require_3d_periodic_network=True,
)

MAX_RING_SIZE = 16
CALCULATE_RINGS = True


def find_structure_file(argument_path: Optional[str]) -> Path:
    """解析する構造ファイルを決定する。"""
    if argument_path is not None:
        path = Path(argument_path)
        if not path.exists():
            raise FileNotFoundError(f"構造ファイルが見つかりません: {path}")
        return path

    for path in DEFAULT_CANDIDATES:
        print(f"[TRY] {path}")
        if path.exists():
            print(f"[USE] {path}")
            return path

    names = ", ".join(str(path) for path in DEFAULT_CANDIDATES)
    raise FileNotFoundError(f"構造ファイルが見つかりません。探索対象: {names}")


def _format_distribution(distribution: Mapping[int, int]) -> str:
    if not distribution:
        return "(none)"
    return "  ".join(
        f"CN{coordination}={count}"
        for coordination, count in sorted(distribution.items())
    )


def _format_stat(stat: Mapping[str, object], unit: str) -> str:
    count = int(stat["count"])
    if count == 0:
        return "count=0"

    mean = float(stat["mean"])
    std = float(stat["std"])
    minimum = float(stat["minimum"])
    maximum = float(stat["maximum"])

    return (
        f"count={count}  mean={mean:.4f} {unit}  "
        f"std={std:.4f}  min={minimum:.4f}  max={maximum:.4f}"
    )


def print_report(
    result: Mapping[str, object],
    structure_path: Path,
) -> None:
    """解析結果を人が比較しやすい形で表示する。"""
    coordination = result["coordination"]
    bond_lengths = result["bond_lengths"]
    angles = result["angles"]
    network = result["network"]
    rings = result["rings"]
    loewenstein = result["loewenstein"]
    screening = result["screening"]

    print()
    print("=" * 72)
    print("Zeolite framework analysis")
    print("=" * 72)
    print(f"Structure : {structure_path}")
    print(f"Atoms     : {int(result['atom_count'])}")
    print(f"Volume    : {float(result['volume_A3']):.6f} Å^3")
    print(
        "Framework density : "
        f"{float(result['framework_density_T_per_1000A3']):.6f} "
        "T / 1000 Å^3"
    )

    print()
    print("[1] Coordination / framework building blocks")
    print("Si -> O : " + _format_distribution(coordination["si_o_coordination"]))
    print("Al -> O : " + _format_distribution(coordination["al_o_coordination"]))
    print("O -> T  : " + _format_distribution(coordination["o_t_coordination"]))
    print(f"T4 fraction        : {100.0 * float(coordination['t4_fraction']):.4f} %")
    print(
        "Bridging-O fraction: "
        f"{100.0 * float(coordination['bridging_o_fraction']):.4f} %"
    )

    print()
    print("[2] T-O bond lengths")
    print("Si-O : " + _format_stat(bond_lengths["Si-O"], "Å"))
    print("Al-O : " + _format_stat(bond_lengths["Al-O"], "Å"))

    print()
    print("[3] Tetrahedral / hinge angles")
    for name in ("O-Si-O", "O-Al-O", "Si-O-Si", "Si-O-Al", "Al-O-Al"):
        print(f"{name:8s}: " + _format_stat(angles[name], "deg"))

    print()
    print("[4] Framework connectivity")
    print(f"Components              : {int(network['component_count'])}")
    print(
        "Largest component       : "
        f"{int(network['largest_component_size'])} atoms "
        f"({100.0 * float(network['largest_component_fraction']):.4f} %)"
    )
    print(
        "Periodic dimensionality : "
        f"{int(network['largest_component_periodic_dimension'])}D"
    )

    print()
    print("[5] T-T shortest-ring statistics")
    ring_counts = rings["ring_counts"]
    if ring_counts:
        for ring_size, count in sorted(ring_counts.items()):
            print(f"{int(ring_size):2d}-ring : {int(count)}")
    else:
        print("(no ring found in selected range)")

    print()
    print("[6] Al distribution / Loewenstein diagnostic")
    print(f"Si-O-Si pairs : {int(loewenstein['Si-O-Si'])}")
    print(f"Si-O-Al pairs : {int(loewenstein['Si-O-Al'])}")
    print(f"Al-O-Al pairs : {int(loewenstein['Al-O-Al'])}")
    print(
        "Al-O-Al fraction : " f"{100.0 * float(loewenstein['al_o_al_fraction']):.6f} %"
    )

    print()
    print("[7] Zeolite-like screening")
    checks = screening["checks"]
    criteria = screening["criteria"]

    print(
        "T4 fraction              : "
        f"{'PASS' if checks['t4_fraction'] else 'FAIL'}  "
        f"(threshold >= {100.0 * float(criteria['min_t4_fraction']):.1f} %)"
    )
    print(
        "Bridging-O fraction      : "
        f"{'PASS' if checks['bridging_o_fraction'] else 'FAIL'}  "
        f"(threshold >= {100.0 * float(criteria['min_bridging_o_fraction']):.1f} %)"
    )
    print(
        "Largest component        : "
        f"{'PASS' if checks['largest_component_fraction'] else 'FAIL'}  "
        f"(threshold >= {100.0 * float(criteria['min_largest_component_fraction']):.1f} %)"
    )
    print(
        "3D periodic network      : "
        f"{'PASS' if checks['periodic_network'] else 'FAIL'}"
    )
    print()
    print(
        "RESULT : "
        + (
            "ZEOLITE-LIKE"
            if screening["is_zeolite_like"]
            else "OUTSIDE DEFAULT ZEOLITE-LIKE SCREEN"
        )
    )
    print()
    print(
        "NOTE   : binary RESULT is only an RMC screening criterion. "
        "Use the continuous metrics above for comparison."
    )
    print("=" * 72)


def main() -> None:
    argument_path: Optional[str] = None
    if len(sys.argv) >= 2:
        argument_path = sys.argv[1]

    structure_path = find_structure_file(argument_path)
    structure = Structure.from_file(str(structure_path))

    result = analyze_zeolite(
        structure=structure,
        cutoffs=CUTOFFS,
        criteria=CRITERIA,
        max_ring_size=MAX_RING_SIZE,
        calculate_rings=CALCULATE_RINGS,
    )

    print_report(
        result=result,
        structure_path=structure_path,
    )


if __name__ == "__main__":
    main()
