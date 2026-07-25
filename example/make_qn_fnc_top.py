#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

SiO2 構造から Qn 解析と RMC_POT 用 FNC 入力を作る実行例。


SiO2 固有の条件は隣の ``qn_config_sio2_fnc.json`` に置く。

実行位置はこのファイルと ``qn_config_sio2_fnc.json`` がある directory を想定する。
入力構造 ``SiO2_750_S1_nvt4.vasp`` も同じ directory に置く。

作成される主なファイル:
    * ``SiO2_750_S1_nvt4_qn.csv``
    * ``SiO2_750_S1_nvt4_network_bonds.csv``
    * ``SiO2_750_S1_nvt4_rmc_fnc3.fnc``
    * ``SiO2_750_S1_nvt4_rmc_unit.top``
    * ``SiO2_750_S1_nvt4_report.txt``
"""
# from __future__ import print_function

import shutil
from rmc_dft.rmc_pot.qn import QnNetworkBuilder


def main() -> None:
    """SiO2 用 JSON 設定を使って標準出力一式を作成する。"""
    poscar_name = "aaa.vasp"
    config_name = "qn_config.json"
    cfg_name = "aaa"

    builder = QnNetworkBuilder.from_poscar(
        poscar_name=poscar_name,
        config_name=config_name,
    )
    if builder.analysis.fnc_error is not None:
        print("FNC3 warning:", builder.analysis.fnc_error)

    builder.write_unit_topology(cfg_name + "_rmc_unit.top")
    builder.write_analysis(cfg_name)

    # shutil.copyfile("POSCAR", f"{poscar_name}")
    shutil.copyfile(f"{cfg_name}_rmc_unit.top", f"{cfg_name}.top")

    print("Qn counts:", builder.get_qn_counts())
    print("created:", cfg_name + "_rmc_unit.top")
    print("created:", cfg_name + "_qn.csv")
    print("created:", cfg_name + "_report.txt")


if __name__ == "__main__":
    main()
