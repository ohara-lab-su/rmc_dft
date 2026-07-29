#!/usr/bin/env pytnon
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from __future__ import annotations


def extract_last_forces(outcar_filename: str) -> list[list[float]]:
    with open(outcar_filename, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    start_index = -1
    for i, line in enumerate(lines):
        if "TOTAL-FORCE (eV/Angst)" in line:
            start_index = i

    if start_index == -1:
        raise RuntimeError("TOTAL-FORCE block not found")

    forces: list[list[float]] = []

    i = start_index + 2
    while i < len(lines):
        line = lines[i].strip()

        if line == "":
            break

        parts = line.split()
        if len(parts) < 6:
            break

        fx = float(parts[3])
        fy = float(parts[4])
        fz = float(parts[5])

        forces.append([fx, fy, fz])
        i += 1

    return forces


if __name__ == "__main__":
    forces = extract_last_forces("OUTCAR")

    for i, f in enumerate(forces):
        print(i, f[0], f[1], f[2])
