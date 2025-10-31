#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POTCAR 自動生成クラス
ex) make_poscar.py Li Mn O
"""

import os
import sys
from csv import excel_tab

from x_logger import XLogger


class PotcarBuilder:
    """
    指定された元素リストから最適なポテンシャルを選び、
    一つの POTCAR に連結して出力するクラス。
    """

    def __init__(
        self,
        base_dir: str = "~/potpaw_PBE.64",
        logger: XLogger = None,
    ):
        """

        Args:
            base_dir (str):
            logger (XLogger):
        """

        if not logger:
            logger = XLogger()
        self._logger = logger

        self.base_dir = os.path.expanduser(base_dir)
        self.priority = {
            "H": [
                "H",
                "H_GW_new",
                "H_GW",
                "H_AE",
                "H_s",
                "H_h",
                "H1.75",
                "H1.66",
                "H1.5",
                "H1.33",
                "H1.25",
            ],
            "He": ["He", "He_GW", "He_AE"],
            "Li": ["Li", "Li_sv", "Li_sv_GW", "Li_GW", "Li_AE_GW"],
            "Be": ["Be", "Be_sv", "Be_sv_GW", "Be_GW"],
            "B": ["B", "B_GW_new", "B_GW", "B_h_GW", "B_h", "B_s"],
            "C": ["C", "C_GW_new", "C_GW", "C_h_GW", "C_h", "C_s_GW", "C_s"],
            "N": ["N", "N_GW_new", "N_GW", "N_h_GW", "N_h", "N_s_GW", "N_s"],
            "O": ["O", "O_GW_new", "O_GW", "O_h_GW", "O_h", "O_s_GW", "O_s"],
            "F": ["F", "F_GW_new", "F_GW", "F_h_GW", "F_h", "F_s"],
            "Na": ["Na", "Na_sv_GW", "Na_sv", "Na_pv"],
            "Mg": ["Mg", "Mg_sv_GW", "Mg_sv", "Mg_pv_GW", "Mg_pv", "Mg_GW"],
            "Al": ["Al", "Al_sv_GW", "Al_GW"],
            "Si": ["Si", "Si_sv_GW", "Si_GW"],
            "P": ["P", "P_GW", "P_h"],
            "S": ["S", "S_GW", "S_h"],
            "Cl": ["Cl", "Cl_GW", "Cl_h"],
            "K": ["K_pv", "K_sv_GW", "K_sv"],
            "Ca": ["Ca_pv", "Ca_sv_GW", "Ca_sv"],
            "Sc": ["Sc", "Sc_sv_GW", "Sc_sv"],
            "Ti": ["Ti", "Ti_sv_GW", "Ti_sv", "Ti_pv"],
            "V": ["V", "V_sv_GW", "V_sv", "V_pv"],
            "Cr": ["Cr", "Cr_sv_GW", "Cr_sv", "Cr_pv"],
            "Mn": ["Mn", "Mn_sv_GW", "Mn_sv", "Mn_GW", "Mn_pv"],
            "Fe": ["Fe", "Fe_sv_GW", "Fe_sv", "Fe_GW", "Fe_pv"],
            "Co": ["Co", "Co_sv_GW", "Co_sv", "Co_GW", "Co_pv"],
            "Ni": ["Ni", "Ni_sv_GW", "Ni_GW", "Ni_pv"],
            "Cu": ["Cu", "Cu_sv_GW", "Cu_GW", "Cu_pv"],
            "Zn": ["Zn", "Zn_sv_GW", "Zn_GW"],
            "Ga": ["Ga", "Ga_sv_GW", "Ga_GW", "Ga_d_GW", "Ga_d", "Ga_h"],
            "Ge": ["Ge", "Ge_sv_GW", "Ge_GW", "Ge_d_GW", "Ge_d", "Ge_h"],
            "As": ["As", "As_sv_GW", "As_GW", "As_d"],
            "Se": ["Se", "Se_sv_GW", "Se_GW"],
            "Br": ["Br", "Br_sv_GW", "Br_GW"],
            "Kr": ["Kr", "Kr_GW"],
            "Rb": ["Rb_pv", "Rb_sv_GW", "Rb_sv"],
            "Sr": ["Sr_sv", "Sr_sv_GW"],
            "Y": ["Y_sv", "Y_sv_GW"],
            "Zr": ["Zr_sv", "Zr_sv_GW"],
            "Nb": ["Nb_sv", "Nb_pv", "Nb_sv_GW"],
            "Mo": ["Mo", "Mo_sv_GW", "Mo_sv", "Mo_pv"],
            "Ru": ["Ru", "Ru_sv_GW", "Ru_sv", "Ru_pv"],
            "Rh": ["Rh", "Rh_sv_GW", "Rh_GW", "Rh_pv"],
            "Pd": ["Pd", "Pd_sv_GW", "Pd_GW", "Pd_pv"],
            "Ag": ["Ag", "Ag_sv_GW", "Ag_GW", "Ag_pv"],
            "Cd": ["Cd", "Cd_sv_GW", "Cd_GW"],
            "In": ["In", "In_sv_GW", "In_d_GW", "In_d"],
            "Sn": ["Sn", "Sn_sv_GW", "Sn_d_GW", "Sn_d"],
            "Sb": ["Sb", "Sb_sv_GW", "Sb_d_GW", "Sb_GW"],
            "Te": ["Te", "Te_sv_GW", "Te_GW"],
            "I": ["I", "I_sv_GW", "I_GW"],
            "Xe": ["Xe", "Xe_sv_GW", "Xe_GW"],
            "Cs": ["Cs_sv", "Cs_sv_GW"],
            "Ba": ["Ba_sv", "Ba_sv_GW"],
            "La": ["La", "La_GW", "La_s"],
            "Ce": ["Ce", "Ce_GW", "Ce_h", "Ce_3"],
            "Pr": ["Pr", "Pr_h", "Pr_3"],
            "Nd": ["Nd", "Nd_h", "Nd_3"],
            "Pm": ["Pm", "Pm_h", "Pm_3"],
            "Sm": ["Sm", "Sm_h", "Sm_3"],
            "Eu": ["Eu", "Eu_h", "Eu_3", "Eu_2"],
            "Gd": ["Gd", "Gd_h", "Gd_3"],
            "Tb": ["Tb", "Tb_h", "Tb_3"],
            "Dy": ["Dy", "Dy_h", "Dy_3"],
            "Ho": ["Ho", "Ho_h", "Ho_3"],
            "Er": ["Er", "Er_h", "Er_3", "Er_2"],
            "Tm": ["Tm", "Tm_h", "Tm_3"],
            "Yb": ["Yb", "Yb_h", "Yb_3", "Yb_2"],
            "Lu": ["Lu", "Lu_3"],
            "Hf": ["Hf", "Hf_sv_GW", "Hf_sv", "Hf_pv"],
            "Ta": ["Ta", "Ta_sv_GW", "Ta_pv"],
            "W": ["W", "W_sv_GW", "W_sv"],
            "Re": ["Re", "Re_sv_GW", "Re_pv"],
            "Os": ["Os", "Os_sv_GW", "Os_pv"],
            "Ir": ["Ir", "Ir_sv_GW"],
            "Pt": ["Pt", "Pt_sv_GW", "Pt_GW", "Pt_pv"],
            "Au": ["Au", "Au_sv_GW", "Au_GW"],
            "Hg": ["Hg_sv_GW", "Hg"],
            "Tl": ["Tl", "Tl_sv_GW", "Tl_d_GW", "Tl_d"],
            "Pb": ["Pb", "Pb_sv_GW", "Pb_d_GW", "Pb_d"],
            "Bi": ["Bi", "Bi_sv_GW", "Bi_d_GW", "Bi_d", "Bi_GW"],
            "Po": ["Po", "Po_sv_GW", "Po_d_GW", "Po_d"],
            "At": ["At", "At_sv_GW", "At_d_GW"],
            "Rn": ["Rn", "Rn_sv_GW", "Rn_d_GW"],
            "Fr": ["Fr_sv"],
            "Ra": ["Ra_sv"],
            "Ac": ["Ac"],
            "Th": ["Th", "Th_s"],
            "Pa": ["Pa", "Pa_s"],
            "U": ["U", "U_s"],
            "Np": ["Np", "Np_s"],
            "Pu": ["Pu", "Pu_s"],
            "Am": ["Am"],
            "Cm": ["Cm"],
            "Cf": ["Cf"],
        }

    def choose_potential(
        self,
        element: str,
    ) -> str:
        """最適な POTCAR のファイルパスを返す"""
        if element not in self.priority:
            raise KeyError(f"{element} は未登録の元素")

        for candidate in self.priority[element]:
            path = os.path.join(self.base_dir, candidate, "POTCAR")
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"{element} に対応する POTCAR が見つかりません。")

    def build(
        self,
        elements: list[str],
        poscar_name: str = "POTCAR",
    ) -> bool:
        """
        指定元素リストから POTCAR を構築して出力する。

        判定規則:
          - poscar_name が区切り記号で終わる、または実在するディレクトリ -> ディレクトリ扱い（中に POTCAR）
          - 上記以外 -> ファイル扱い（親ディレクトリを作成）

        Args:
            elements (list[str])::
            poscar_name (str):

        Returns:
            bool:

        """
        # 親ディレクトリを作成
        output_dir: str = os.path.dirname(poscar_name)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        try:
            # POTCAR ファイル生成
            with open(poscar_name, "wb") as fout:
                for elem in elements:
                    pot_src_path: str = os.path.join(self.base_dir, elem, "POTCAR")
                    if not os.path.isfile(pot_src_path):
                        raise FileNotFoundError(
                            f"ポテンシャルが見つかりません: {pot_src_path}"
                        )
                    self._logger.info(f"{elem:>3} <- {pot_src_path}")
                    with open(pot_src_path, "rb") as fin:
                        fout.write(fin.read())
        except Exception as e:
            self._logger.error(f"Error: {e}")
            return False

        self._logger.info(f"POTCAR を出力しました: {poscar_name}")
        return True


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

    builder = PotcarBuilder("~/potpaw_PBE.64")
    builder.build(_elements, poscar_name=_poscar_name)
