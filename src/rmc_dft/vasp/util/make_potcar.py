#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""

from rmc_dft.vasp.vasp_potcar_builder import VaspPotcarBuilder


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python potcar_builder.py Li Mn O [output_file(optional)]")
        sys.exit(1)

    # 最後の引数が出力ファイル名なら分離
    # . を含んでいる時は元素名ではなくてフォルダ名となる
    # make_poscar.py Li Mn O ./bb/POTCAR
    args = sys.argv[1:]
    if len(args) >= 2 and "." in args[-1]:
        _poscar_name = args[-1]
        _elements = args[:-1]
    else:
        _poscar_name = "POTCAR"
        _elements = args

    builder = VaspPotcarBuilder("~/potpaw_PBE.64")
    builder.build(_elements, poscar_name=_poscar_name)
