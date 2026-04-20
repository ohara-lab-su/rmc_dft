#!/usr/bin/env python
from __future__ import annotations

import math
from pathlib import Path

from pymatgen.io.vasp.outputs import Vasprun


def read_structures_from_vasprun(vasprun_filename: str) -> list:
    vasprun = Vasprun(
        vasprun_filename,
        exception_on_bad_xml=False,
        parse_dos=False,
        parse_eigen=False,
        parse_projected_eigen=False,
        parse_potcar_file=False,
    )

    structures: list = []

    for ionic_step in vasprun.ionic_steps:
        structures.append(ionic_step["structure"])

    return structures


def calc_step_displacements(
    structures: list,
) -> list[dict[str, float | int | list[float]]]:
    results: list[dict[str, float | int | list[float]]] = []

    step_index = 1
    while step_index < len(structures):
        previous_structure = structures[step_index - 1]
        current_structure = structures[step_index]

        atom_displacements: list[float] = []
        atom_index = 0

        while atom_index < len(current_structure):
            previous_site = previous_structure[atom_index]
            current_site = current_structure[atom_index]

            distance, _image = previous_structure.lattice.get_distance_and_image(
                previous_site.frac_coords,
                current_site.frac_coords,
            )

            atom_displacements.append(distance)
            atom_index = atom_index + 1

        max_displacement = max(atom_displacements)

        displacement_sum = 0.0
        squared_sum = 0.0
        max_atom_index = 0

        atom_index = 0
        while atom_index < len(atom_displacements):
            displacement = atom_displacements[atom_index]
            displacement_sum = displacement_sum + displacement
            squared_sum = squared_sum + displacement * displacement

            if displacement > atom_displacements[max_atom_index]:
                max_atom_index = atom_index

            atom_index = atom_index + 1

        mean_displacement = displacement_sum / len(atom_displacements)
        rms_displacement = math.sqrt(squared_sum / len(atom_displacements))

        results.append(
            {
                "ionic_step": step_index + 1,
                "max_displacement": max_displacement,
                "mean_displacement": mean_displacement,
                "rms_displacement": rms_displacement,
                "max_atom_index_0based": max_atom_index,
                "max_atom_index_1based": max_atom_index + 1,
                "atom_displacements": atom_displacements,
            }
        )

        step_index = step_index + 1

    return results


def write_step_summary(
    results: list[dict[str, float | int | list[float]]], output_filename: str
) -> None:
    with Path(output_filename).open("w", encoding="utf-8") as file:
        file.write(
            "ionic_step,max_displacement_A,mean_displacement_A,rms_displacement_A,"
            "max_atom_index_0based,max_atom_index_1based\n"
        )

        for result in results:
            file.write(
                f"{result['ionic_step']},"
                f"{result['max_displacement']:.10f},"
                f"{result['mean_displacement']:.10f},"
                f"{result['rms_displacement']:.10f},"
                f"{result['max_atom_index_0based']},"
                f"{result['max_atom_index_1based']}\n"
            )


def write_atomwise_displacements(
    results: list[dict[str, float | int | list[float]]],
    output_filename: str,
) -> None:
    with Path(output_filename).open("w", encoding="utf-8") as file:
        file.write("ionic_step,atom_index_0based,atom_index_1based,displacement_A\n")

        for result in results:
            ionic_step = int(result["ionic_step"])
            atom_displacements = result["atom_displacements"]

            atom_index = 0
            while atom_index < len(atom_displacements):
                displacement = atom_displacements[atom_index]
                file.write(
                    f"{ionic_step},"
                    f"{atom_index},"
                    f"{atom_index + 1},"
                    f"{displacement:.10f}\n"
                )
                atom_index = atom_index + 1


if __name__ == "__main__":
    vasprun_filename = "vasprun.xml"

    structures = read_structures_from_vasprun(vasprun_filename)
    results = calc_step_displacements(structures)

    write_step_summary(results, "ionic_step_displacement_summary.csv")
    write_atomwise_displacements(results, "ionic_step_atom_displacements.csv")

    for result in results:
        print(
            f"{int(result['ionic_step'])} "
            f"{float(result['max_displacement']):.6f} "
            f"{float(result['mean_displacement']):.6f} "
            f"{float(result['rms_displacement']):.6f} "
            f"{int(result['max_atom_index_1based'])}"
        )
