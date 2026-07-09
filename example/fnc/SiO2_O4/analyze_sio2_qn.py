#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SiO2 構造の Qn/network 解析だけを実行する。"""
from __future__ import print_function

import os
import sys
from pathlib import Path

from rmc_dft.rmc_pot.qn import QnNetworkAnalysis


def resolve_poscar_name(structure_name: str) -> str:
    """引数から解析対象の VASP 構造ファイル名を決める。"""
    path = Path(structure_name)
    if path.suffix:
        return str(path)
    return structure_name + ".vasp"


def resolve_prefix(structure_name: str) -> str:
    """引数から出力ファイル名の prefix を決める。"""
    return Path(structure_name).stem


def main() -> None:
    """SiO2 用 JSON 設定を使って解析結果だけを出力する。"""
    # 固定ファイル名で実行する場合は、下の 3 行を使う。
    # structure_name = "aaa"
    # config_name = "qn_config_sio2.json"
    # prefix = "aaa"

    if len(sys.argv) < 2:
        print("usage: python analyze_sio2_qn.py STRUCTURE_NAME [CONFIG_JSON]")
        print("example: python analyze_sio2_qn.py aaa")
        print("example: python analyze_sio2_qn.py aaa.vasp")
        sys.exit(1)

    structure_name = sys.argv[1]

    if len(sys.argv) >= 3:
        config_name = sys.argv[2]
    else:
        config_name = "qn_config_sio2.json"

    poscar_name = resolve_poscar_name(structure_name)
    prefix = resolve_prefix(structure_name)

    if not os.path.exists(poscar_name):
        raise FileNotFoundError(poscar_name)

    if not os.path.exists(config_name):
        raise FileNotFoundError(config_name)

    analysis = QnNetworkAnalysis.from_poscar(
        poscar_name=poscar_name,
        config_name=config_name,
    )
    analysis.write_analysis(prefix)

    print("Qn counts:", analysis.get_qn_counts())
    print("created:", prefix + "_qn.csv")
    print("created:", prefix + "_network_bonds.csv")
    print("created:", prefix + "_report.txt")


if __name__ == "__main__":
    main()
