# -*- coding: utf-8 -*-
"""Run Qn/network state analysis for one VASP/POSCAR structure.

Edit the variables below to change the input file, config file, and output prefix.
No command-line arguments are used.
"""

from __future__ import print_function

from rmc_dft.rmc_pot.fnc.qn_network_state import analyze_vasp_file


STRUCTURE_FILE = "structure_after.vasp"
CONFIG_FILE = "qn_config_sio2.json"
OUTPUT_PREFIX = "structure_after"


def main():
    result = analyze_vasp_file(
        structure_path=STRUCTURE_FILE,
        config_path=CONFIG_FILE,
        output_prefix=OUTPUT_PREFIX,
    )
    print("network state written")
    print("natoms:", result["natoms"])
    print("Qn:", result["qn_counts"])
    print("O coordination:", result["oxygen_counts"])
    print(
        "largest_component_fraction:",
        result["components"]["largest_component_fraction"],
    )


if __name__ == "__main__":
    main()
