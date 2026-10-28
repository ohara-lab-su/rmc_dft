#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from __future__ import annotations

import math
from typing import List


def _is_float_text(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def extract_all_force_norms(outcar_filename: str) -> List[List[float]]:
    with open(outcar_filename, "r", encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()

    all_step_norms: List[List[float]] = []

    i = 0
    n_lines = len(lines)

    while i < n_lines:
        if "TOTAL-FORCE (eV/Angst)" in lines[i]:
            step_norms: List[float] = []

            i = i + 1

            while i < n_lines:
                line = lines[i].strip()

                if line.startswith("---"):
                    i = i + 1
                    break

                i = i + 1

            while i < n_lines:
                line = lines[i].strip()
                if line == "":
                    break

                if line.startswith("---"):
                    break

                cols = line.split()
                if len(cols) < 6:
                    break

                if _is_float_text(cols[0]) is False:
                    break

                fx = float(cols[3])
                fy = float(cols[4])
                fz = float(cols[5])

                norm = math.sqrt(fx * fx + fy * fy + fz * fz)
                step_norms.append(norm)
                i = i + 1

            all_step_norms.append(step_norms)

        i = i + 1

    return all_step_norms


if __name__ == "__main__":
    all_step_norms = extract_all_force_norms("OUTCAR")

    for step_index, norms in enumerate(all_step_norms, start=1):
        max_force = max(norms)
        print(f"{step_index} {max_force:.6f}")
