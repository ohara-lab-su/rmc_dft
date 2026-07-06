#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SiO2 構造から Qn 解析、FNC=3、FNC=4 topology を作成する例。"""
from __future__ import print_function

from rmc_dft.rmc_pot.fnc import QnNetworkBuilder


def main() -> None:
    poscar_name = "SiO2_750_S1_nvt4.vasp"
    config_name = "qn_config_sio2.json"
    prefix = "SiO2_750_S1_nvt4"

    builder = QnNetworkBuilder.from_poscar(
        poscar_name=poscar_name,
        config_name=config_name,
    )
    builder.write_all(prefix)

    print("Qn counts:", builder.get_qn_counts())
    print("created:", prefix + "_fnc3.fnc")
    print("created:", prefix + "_fnc4.top")
    print("created:", prefix + "_qn.csv")
    print("created:", prefix + "_report.txt")


if __name__ == "__main__":
    main()
