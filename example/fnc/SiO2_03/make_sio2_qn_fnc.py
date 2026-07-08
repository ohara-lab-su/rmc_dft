#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SiO2 構造から Qn 解析と RMC_POT 用 FNC 入力を作る実行例。

SiO2 固有の条件は隣の ``qn_config_sio2.json`` に置く。

実行位置はこのファイルと ``qn_config_sio2.json`` がある directory を想定する。
入力構造 ``SiO2_750_S1_nvt4.vasp`` も同じ directory に置く。

作成される主なファイル:
    * ``SiO2_750_S1_nvt4_qn.csv``
    * ``SiO2_750_S1_nvt4_network_bonds.csv``
    * ``SiO2_750_S1_nvt4_rmc_fnc3.fnc``
    * ``SiO2_750_S1_nvt4_rmc_unit.top``
    * ``SiO2_750_S1_nvt4_report.txt``
"""
from __future__ import print_function

from qn_network import QnNetworkBuilder


def main() -> None:
    """SiO2 用 JSON 設定を使って標準出力一式を作成する。"""
    poscar_name = "SiO2_750_S1_nvt4.vasp"
    config_name = "qn_config_sio2.json"
    prefix = "SiO2_750_S1_nvt4"

    builder = QnNetworkBuilder.from_poscar(
        poscar_name=poscar_name,
        config_name=config_name,
    )
    builder.write_all(prefix)

    print("Qn counts:", builder.get_qn_counts())
    print("created:", prefix + "_rmc_fnc3.fnc")
    print("created:", prefix + "_rmc_unit.top")
    print("created:", prefix + "_qn.csv")
    print("created:", prefix + "_report.txt")


if __name__ == "__main__":
    main()
