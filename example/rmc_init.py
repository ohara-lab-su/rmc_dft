#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

rmc_vasp_script.py はそのまま RMC-DFT で止めてしまうので、
DFT でおわる。
そこから一回RMCをかけるプログラム
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import os
import argparse
import sys
import shutil
import re

from rmc_dft import (
    Config,
    Vasp,
    VaspIncar,
    VaspKpoints,
    VaspOutcar,
    VaspPotcarBuilder,
    VaspLog,
    RmcPot,
    RmcPotLog,
    RmcPotDat,
    RmcPotFit,
    RmcPotHst,
    RmcPotPpcf,
)
from rmc_dft.util import poscar2cfg
from rmc_dft.util import next_log_dir_name as next_log_dir_name
from x_logger import XLogger


def run_rmc_init(
    config: Config,
    rmc_dat: Optional[RmcPotDat] = None,
    *,
    logger: Optional[Any] = None,
) -> bool:
    """
    RMC param
    """
    if logger is None:
        logger = XLogger()

    if rmc_dat is None:
        rmc_dat = RmcPotDat(config=config, logger=logger)

    ######################################
    # パラメーター調整

    # 1 行目のコメント（系名）を設定する
    # rmc_dat.set_comment("comment FeSiB")
    # rmc_dat.set_comment("comment Li3PO4")
    rmc_dat.set_comment("comment SiO2")

    # デフォルト値は config.yaml で書く(ここで書いた値のほうが優先される)
    # 2 行目：number density（数密度）を設定する
    # --- FeSiB
    # rmc_dat.set_density(0.0915)
    # rmc_dat.set_density(0.09119)
    # rmc_dat.set_density(0.0912)

    # --- Li3PO4
    # rmc_dat.set_density(0.0772877)

    # --- SiO2 製法A1 mass_density_g_cm3 = 2.214  # SiO2製法A: S1
    rmc_dat.set_density(0.0665715652)

    # 3 行目：cut offs（各原子種ペアのカットオフ距離）を設定する
    # rmc_dat.set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])
    # ---- FeSiB
    # 11(Fe-Fe) 2.45-2.55
    # 12(Fe-Si) 2.35-2.45
    # 13(Fe-B)  2.05-2.15
    # 22(Si-Si) 2.35-2.50
    # 23(Si-B)  2.0-2.1
    # 33(B-B)   1.7-1.9
    # rmc_dat.set_cutoffs([2.2, 1.9, 1.75, 1.8, 1.75, 1.5])
    # rmc_dat.set_cutoffs([2.1, 1.9, 1.75, 1.8, 1.75, 1.5])
    # rmc_dat.set_cutoffs([2.2, 2.2, 1.95, 1.8, 1.8, 2.8]) # 2026.02.16
    # rmc_dat.set_cutoffs([2.4, 2.3, 2.1, 2.0, 2.4, 1.7])
    # rmc_dat.set_cutoffs([2.2, 2.1, 1.75, 2.3, 1.6, 1.6])
    # --- Li3PO4 (test)
    # rmc_dat.set_cutoffs([2.4, 2.3, 2.1, 2.0, 2.4, 1.7])

    # --- SiO2 (test)
    # peak Si-Si:2.7-2.70, Si-O:1.5-1.55, O-O: 2.3-2.4
    # rmc_dat.set_cutoffs([2.40, 1.25, 2.10])  # Si-Si, Si-O, O-O
    rmc_dat.set_cutoffs([1.9, 1.1, 1.9])  # Si-Si, Si-O, O-O
    # rmc_dat.set_cutoffs([1.0, 1.0, 1.0])  # Si-Si, Si-O, O-O

    # 4 行目：maximum moves（1 回の移動での最大変位量）を設定する
    # --- FeSiB, Li3PO4
    # rmc_dat.set_maximum_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximum_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximum_moves([0.05, 0.01, 0.01])
    # rmc_dat.set_maximum_moves([0.05, 0.01, 0.01])  # 2026.02.16
    # rmc_dat.set_maximum_moves([0.01, 0.01, 0.01])  # 2026.02.16
    # --- SiO2
    rmc_dat.set_maximum_moves([0.01, 0.01])

    # 5 行目：r spacing を設定する(動径のビン幅)
    # rのステップ(Δr)
    rmc_dat.set_r_spacing(0.025)

    # 6行目: moveout を認めるかどうか？
    # カットオフ以下の位置での原子の存在を排除するか？認めるか？
    rmc_dat.set_moveout_option(True)
    # rmc_dat.set_moveout_option(False)

    # 9行目
    # 計算時間と構造をsaveするステップ間隔
    # rmc_dat.set_time_and_save(0.5, 0.5)
    # rmc_dat.set_time_and_save(5, 1)
    # rmc_dat.set_time_and_save(15, 1)
    rmc_dat.set_time_and_save(30, 1)
    # rmc_dat.set_time_and_save(60, 1)
    # rmc_dat.set_time_and_save(120, 1)
    # rmc_dat.set_time_and_save(360, 1)
    # rmc_dat.set_time_and_save(480, 1)
    # rmc_dat.set_time_and_save(720, 1)

    # 10 行目：データ種の使用フラグ（g(r), neutron, x-ray, EXAFS）を設定する
    rmc_dat.set_data_flags([0, 0, 1, 0])

    # 実験データファイル名（11 行目）を設定する
    # デフォルト値は config.yaml で書く(ここで書いた値のほうが優先される)
    # rmc_dat.set_exp_filename(config.rmc_exp_filename)
    # rmc_dat.set_exp_filename("ascast.xsq")
    # rmc_dat.set_exp_filename("HB1M_250_251224.xsq")
    # rmc_dat.set_exp_filename("as_cast_0305.xsq")

    # 12 (データ範囲)
    # ---- FeSiB
    # rmc_dat.set_exp_range(1, 1091, auto_write=True)
    # rmc_dat.set_exp_range(50, 1091)  # 2026.02.16
    # rmc_dat.set_exp_range(85, 1091)  # 2026.02.16
    # ---- Li3PO4
    # rmc_dat.set_exp_range(85, 771)
    # ---- SiO2,type-A
    rmc_dat.set_exp_range(1, 588)

    # 14 (温度因子)
    # σ（実験データの許容誤差の標準偏差）
    #    小さいほど「ズレ」を許さず、結果的により厳しくフィットさせようとする。
    # rmc_dat.set_sigma_factor(5e-4)
    # rmc_dat.set_sigma_factor(1e-5)
    # rmc_dat.set_sigma_factor(1e-2)  # 2026.02.16
    # rmc_dat.set_sigma_factor(1e-7)
    rmc_dat.set_sigma_factor(0.05)

    # 23 行目
    # aaa.fnc を aaa.cfg / aaa.dat と同じ basename 側に置いて使う
    # rmc_dat.set_fnc_switch(3)
    rmc_dat.set_fnc_switch(4)

    # FNC ファイルの距離範囲を RMC 実行前に変更する。
    # 作成時は、packmol_util つかっていたらそれで、初期設定はされている
    # その値を、rmc するときに rmc 毎に変えるなどするには、
    # ペア指定は変えず、constraint type ごとの rmin/rmax だけを書き換える。

    # rmc_dat.set_fnc_distance_ranges(
    #     {
    #         # 1: (1.24, 1.37),  # P-O
    #         # 2: (2.02, 2.25),  # O-O
    #         1: (1.20, 1.45),  # P-O
    #     }
    # )

    # 26 行目：1 回の move で動かす原子数（通常 1）を設定する
    rmc_dat.set_num_atoms_per_move(1)

    return True
