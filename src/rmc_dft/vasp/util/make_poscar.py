#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指定された元素リスト（例: Li Mn O）から、最適な POTCAR を自動構築するスクリプト。
優先順位は potpaw_PBE ディレクトリ内の実在フォルダをもとに自動選択。
"""

import os
import sys

POTCAR_BASE = "~/potpaw_PBE.64"

# 各元素の優先候補（上位が優先）
# 存在チェックを行い、最初に見つかったものを採用
DEFAULT_PRIORITY = {
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
    "Be": [
        "Be",
        "Be_sv",
        "Be_sv_GW",
        "Be_GW",
    ],
    "B": ["B", "B_GW_new", "B_GW", "B_h_GW", "B_h", "B_s"],
    "C": ["C", "C_GW_new", "C_GW", "C_h_GW", "C_h", "C_s_GW", "C_s"],
    "N": ["N", "N_GW_new", "N_GW", "N_h_GW", "N_h", "N_s_GW", "N_s"],
    "O": ["O", "O_GW_new", "O_GW", "O_h_GW", "O_h", "O_s_GW", "O_s"],
    "F": ["F", "F_GW_new", "F_GW", "F_h_GW", "F_h", "F_s"],
    "Na": ["Na", "Na_sv_GW", "Na_sv", "Na_pv"],
    "Mg": ["Mg", "Mg_sv_GW", "Mg_sv", "Mg_pv_GW", "Mg_pv", "Mg_GW"],
    "Al": ["A", "Al_sv_GW", "Al_GW"],
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
    "Ga": ["Ga_sv_GW", "Ga_GW", "Ga_d_GW", "Ga_d", "Ga_h", "Ga"],
    "Ge": ["Ge_sv_GW", "Ge_GW", "Ge_d_GW", "Ge_d", "Ge_h", "Ge"],
    "As": ["As_sv_GW", "As_GW", "As_d", "As"],
    "Se": ["Se_sv_GW", "Se_GW", "Se"],
    "Br": ["Br_sv_GW", "Br_GW", "Br"],
    "Kr": ["Kr_GW", "Kr"],
    "Rb": ["Rb_sv_GW", "Rb_sv", "Rb_pv"],
    "Sr": ["Sr_sv_GW", "Sr_sv"],
    "Y": ["Y_sv_GW", "Y_sv"],
    "Zr": ["Zr_sv_GW", "Zr_sv"],
    "Nb": ["Nb_sv_GW", "Nb_sv", "Nb_pv"],
    "Mo": ["Mo_sv_GW", "Mo_sv", "Mo_pv", "Mo"],
    "Ru": ["Ru_sv_GW", "Ru_sv", "Ru_pv", "Ru"],
    "Rh": ["Rh_sv_GW", "Rh_GW", "Rh_pv", "Rh"],
    "Pd": ["Pd_sv_GW", "Pd_GW", "Pd_pv", "Pd"],
    "Ag": ["Ag_sv_GW", "Ag_GW", "Ag_pv", "Ag"],
    "Cd": ["Cd_sv_GW", "Cd_GW", "Cd"],
    "In": ["In_sv_GW", "In_d_GW", "In_d", "In"],
    "Sn": ["Sn_sv_GW", "Sn_d_GW", "Sn_d", "Sn"],
    "Sb": ["Sb_sv_GW", "Sb_d_GW", "Sb_GW", "Sb"],
    "Te": ["Te_sv_GW", "Te_GW", "Te"],
    "I": ["I_sv_GW", "I_GW", "I"],
    "Xe": ["Xe_sv_GW", "Xe_GW", "Xe"],
    "Cs": ["Cs_sv_GW", "Cs_sv"],
    "Ba": ["Ba_sv_GW", "Ba_sv"],
    "La": ["La_GW", "La_s", "La"],
    "Ce": ["Ce_GW", "Ce_h", "Ce_3", "Ce"],
    "Pr": ["Pr_h", "Pr_3", "Pr"],
    "Nd": ["Nd_h", "Nd_3", "Nd"],
    "Pm": ["Pm_h", "Pm_3", "Pm"],
    "Sm": ["Sm_h", "Sm_3", "Sm"],
    "Eu": ["Eu_h", "Eu_3", "Eu_2", "Eu"],
    "Gd": ["Gd_h", "Gd_3", "Gd"],
    "Tb": ["Tb_h", "Tb_3", "Tb"],
    "Dy": ["Dy_h", "Dy_3", "Dy"],
    "Ho": ["Ho_h", "Ho_3", "Ho"],
    "Er": ["Er_h", "Er_3", "Er_2", "Er"],
    "Tm": ["Tm_h", "Tm_3", "Tm"],
    "Yb": ["Yb_h", "Yb_3", "Yb_2", "Yb"],
    "Lu": ["Lu_3", "Lu"],
    "Hf": ["Hf_sv_GW", "Hf_sv", "Hf_pv", "Hf"],
    "Ta": ["Ta_sv_GW", "Ta_pv", "Ta"],
    "W": ["W_sv_GW", "W_sv", "W"],
    "Re": ["Re_sv_GW", "Re_pv", "Re"],
    "Os": ["Os_sv_GW", "Os_pv", "Os"],
    "Ir": ["Ir_sv_GW", "Ir"],
    "Pt": ["Pt_sv_GW", "Pt_GW", "Pt_pv", "Pt"],
    "Au": ["Au_sv_GW", "Au_GW", "Au"],
    "Hg": ["Hg_sv_GW", "Hg"],
    "Tl": ["Tl_sv_GW", "Tl_d_GW", "Tl_d", "Tl"],
    "Pb": ["Pb_sv_GW", "Pb_d_GW", "Pb_d", "Pb"],
    "Bi": ["Bi_sv_GW", "Bi_d_GW", "Bi_d", "Bi_GW", "Bi"],
    "Po": ["Po_sv_GW", "Po_d_GW", "Po_d", "Po"],
    "At": ["At_sv_GW", "At_d_GW", "At"],
    "Rn": ["Rn_sv_GW", "Rn_d_GW", "Rn"],
    "Fr": ["Fr_sv"],
    "Ra": ["Ra_sv"],
    "Ac": ["Ac"],
    "Th": ["Th_s", "Th"],
    "Pa": ["Pa_s", "Pa"],
    "U": ["U_s", "U"],
    "Np": ["Np_s", "Np"],
    "Pu": ["Pu_s", "Pu"],
    "Am": ["Am"],
    "Cm": ["Cm"],
    "Cf": ["Cf"],
}


def choose_potential(element: str) -> str:
    """最適な POTCAR パスを返す"""
    if element not in DEFAULT_PRIORITY:
        raise KeyError(f"{element} は未登録です。")
    for candidate in DEFAULT_PRIORITY[element]:
        path = os.path.join(POTCAR_BASE, candidate, "POTCAR")
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"{element} に対応する POTCAR が存在しません。")


def make_potcar(elements):
    """複数元素から POTCAR を構築"""
    with open("POTCAR", "wb") as fout:
        for elem in elements:
            pot = choose_potential(elem)
            print(f"{elem:>3} → {os.path.basename(os.path.dirname(pot))}")
            with open(pot, "rb") as fin:
                fout.write(fin.read())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_potcar.py Li Mn O")
        sys.exit(1)
    make_potcar(sys.argv[1:])
