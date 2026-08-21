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
    RmcPotDat,  # fixed-format *.dat
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
    use_free_format: bool = False,
    logger: Optional[Any] = None,
) -> bool:
    """
    RMC param
    """
    if logger is None:
        logger = XLogger()

    if rmc_dat is None:
        rmc_dat = RmcPotDat(
            config=config,
            logger=logger,
        )

    ##########################################
    # Free Format / Fixed Format の指定
    #
    # 繰り返し動作しても、一度intしたら次はintしない
    rmc_dat.init(
        # use_free_format=use_free_format,
        # use_free_format=False, # for FNC/TOP
        use_free_format=True,  # for SNC
        prefer_existing=True,
    )

    ######################################
    # パラメーター調整

    ###################################
    # 1 行目のコメント（系名）を設定する
    # rmc_dat.set_comment("comment FeSiB")
    # rmc_dat.set_comment("comment Li3PO4")

    # --- SiO2 ---
    rmc_dat.set_comment("comment SiO2 type-A")

    # --- Zeolite: Si488 Al12 O1000 Na12, Si/Al=40, Na/Al=1 ---
    # rmc_dat.set_comment(
    #     "comment Si488 Al12 O1000 Na12 H-free zeolite; Si/Al=40; Na/Al=1"
    # )

    # rmc_dat.set_comment("comment LiSPC")

    ###################################
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

    # --- Zeolite: Si488 Al12 O1000 Na12, cubic a=29.8080539703 A ---
    # rmc_dat.set_density(0.0570888006875)

    # --- LiSPC
    # rmc_dat.set_density(0.0453277972)

    ###################################
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
    # rmc_dat.set_cutoffs(
    #     [
    #         1.8,  # Li-Li
    #         2.0,  # Li-P
    #         1.7,  # Li-O
    #         2.5,  # P-P
    #         1.3,  # P-O
    #         2.0,  # O-O
    #     ]
    # )

    # --- SiO2 (test)
    # peak Si-Si:2.7-2.70, Si-O:1.5-1.55, O-O: 2.3-2.4
    # rmc_dat.set_cutoffs([2.40, 1.25, 2.10])  # Si-Si, Si-O, O-O
    # rmc_dat.set_cutoffs([1.0, 1.0, 1.0])  # Si-Si, Si-O, O-O
    # rmc_dat.set_cutoffs([1.9, 1.1, 1.9])  # Si-Si, Si-O, O-O
    rmc_dat.set_cutoffs(
        [
            1.9,  # Si-Si
            1.4,  # Si-O
            1.9,  # O-O
        ]
    )  # Si-Si, Si-O, O-O  # trial: Si-O cutoff 1.1 -> 1.4

    # --- Zeolite ---
    # partial order:
    # Si-Si, Si-Al, Si-O, Si-Na, Al-Al, Al-O, Al-Na, O-O, O-Na, Na-Na
    # rmc_dat.set_cutoffs(
    #     [
    #         2.10,  # Si-Si
    #         2.20,  # Si-Al
    #         1.35,  # Si-O
    #         2.20,  # Si-Na
    #         2.20,  # Al-Al
    #         1.50,  # Al-O
    #         2.20,  # Al-Na
    #         2.00,  # O-O
    #         1.90,  # O-Na
    #         2.30,  # Na-Na
    #     ]
    # )

    # ---- Li,S,P,C
    # rmc_dat.set_cutoffs(
    #     [
    #         1.80,  # Li-Li
    #         1.80,  # Li-S
    #         1.80,  # Li-P
    #         1.70,  # Li-C
    #         1.80,  # S-S
    #         1.75,  # S-P
    #         1.60,  # S-C
    #         1.80,  # P-P
    #         1.60,  # P-C
    #         1.30,  # C-C
    #     ],
    # )

    ###################################
    # 4 行目：maximum moves（1 回の移動での最大変位量）を設定する
    # --- FeSiB, Li3PO4
    # rmc_dat.set_maximum_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximum_moves([0.1, 0.1, 0.1])
    # rmc_dat.set_maximum_moves([0.05, 0.01, 0.01])
    # rmc_dat.set_maximum_moves([0.05, 0.01, 0.01])  # 2026.02.16
    # rmc_dat.set_maximum_moves([0.01, 0.01, 0.01])  # 2026.02.16

    # --- SiO2
    rmc_dat.set_maximum_moves(
        [
            0.01,  # Si
            0.01,  # O
        ]
    )

    # --- Zeolite: Si, Al, O, Na ---
    # rmc_dat.set_maximum_moves(
    #     [
    #         0.01,  # Si
    #         0.01,  # Al
    #         0.01,  # O
    #         0.01,  # Na
    #     ],
    # )

    # -- LiSPC
    # rmc_dat.set_maximum_moves(
    #     [
    #         0.01,  # Li
    #         0.01,  # S
    #         0.01,  # P
    #         0.01,  # C
    #     ],
    # )

    ###################################
    # 5 行目：r spacing を設定する(動径のビン幅)
    # rのステップ(Δr)
    rmc_dat.set_r_spacing(0.025)

    ###################################
    # 6行目: moveout を認めるかどうか？
    # カットオフ以下の位置での原子の存在を排除するか？認めるか？
    rmc_dat.set_moveout_option(True)
    # rmc_dat.set_moveout_option(
    #     False
    # )  # trial: cutoff を通常の hard-sphere 条件として評価

    ###################################
    # 9行目
    # 計算時間と構造をsaveするステップ間隔
    # rmc_dat.set_time_and_save(0.5, 0.5)
    # rmc_dat.set_time_and_save(5, 1)
    rmc_dat.set_time_and_save(15, 1)
    # rmc_dat.set_time_and_save(30, 1)
    # rmc_dat.set_time_and_save(60, 1)
    # rmc_dat.set_time_and_save(120, 1)
    # rmc_dat.set_time_and_save(360, 1)
    # rmc_dat.set_time_and_save(480, 1)
    # rmc_dat.set_time_and_save(720, 1)

    ###################################
    # 10 行目：データ種の使用フラグ（g(r), neutron, x-ray, EXAFS）を設定する
    rmc_dat.set_data_flags([0, 0, 1, 0])

    ###################################
    # 実験データファイル名（11 行目）を設定する
    # デフォルト値は config.yaml で書く(ここで書いた値のほうが優先される)
    # rmc_dat.set_exp_filename(config.rmc_exp_filename)
    # rmc_dat.set_exp_filename("ascast.xsq")
    # rmc_dat.set_exp_filename("HB1M_250_251224.xsq")
    # rmc_dat.set_exp_filename("as_cast_0305.xsq")

    ###################################
    # 12 (データ範囲)
    # ---- FeSiB
    # rmc_dat.set_exp_range(1, 1091, auto_write=True)
    # rmc_dat.set_exp_range(50, 1091)  # 2026.02.16
    # rmc_dat.set_exp_range(85, 1091)  # 2026.02.16
    # ---- Li3PO4
    # rmc_dat.set_exp_range(85, 771)
    # ---- SiO2,type-A
    rmc_dat.set_exp_range(1, 588)
    # ---- LiSPC
    # rmc_dat.set_exp_range(50, 1092)

    ###################################
    # 14 (温度因子)
    # σ（実験データの許容誤差の標準偏差）
    #    小さいほど「ズレ」を許さず、結果的により厳しくフィットさせようとする。
    # rmc_dat.set_sigma_factor(5e-4)
    # rmc_dat.set_sigma_factor(1e-5)
    # rmc_dat.set_sigma_factor(1e-2)  # 2026.02.16
    # rmc_dat.set_sigma_factor(1e-7)
    rmc_dat.set_sigma_factor(0.05)

    ###################################
    # swap
    # rmc_dat.set_swap_settings(0.0, 0)
    # ---- SiO2
    # Si-Si, Si-O, O-O
    # rmc_dat.set_swap_settings(0.1, 1)  # trial: 10% of moves are Si-O swaps
    rmc_dat.set_swap_settings(0.0, 0)  # COORD trial: swap disabled

    # ------------------------------------------------------------------
    # 角度拘束(free-format)
    # ------------------------------------------------------------------
    if rmc_dat.is_free_format:
        pass
        # --- SiO2: O-Si-O ---
        # rmc_dat.set_angle_constraint(
        #     central_type=1,  # Si
        #     neighbor1=(2, 1.40, 1.90),  # O
        #     neighbor2=(2, 1.40, 1.90),  # O
        #     distribution_type="GAUSSIAN",
        #     angle_degrees=109.47,
        #     distribution_width=0.12,  # sigma in cos(theta)
        #     dcosth=0.05,
        #     sigma=0.01,
        #         index=0,
        # )

        # --- Zeolite: O-Si-O ---
        # rmc_dat.set_angle_constraint(
        #     central_type=1,  # Si
        #     neighbor1=(3, 1.40, 1.90),  # O
        #     neighbor2=(3, 1.40, 1.90),  # O
        #     distribution_type="GAUSSIAN",
        #     angle_degrees=109.47,
        #     distribution_width=0.12,
        #     dcosth=0.05,
        #     sigma=0.03,
        #         index=0,
        # )

        # --- Zeolite: O-Al-O ---
        # rmc_dat.set_angle_constraint(
        #     central_type=2,  # Al
        #     neighbor1=(3, 1.55, 2.10),  # O
        #     neighbor2=(3, 1.55, 2.10),  # O
        #     distribution_type="GAUSSIAN",
        #     angle_degrees=109.47,
        #     distribution_width=0.15,
        #     dcosth=0.05,
        #     sigma=0.03,
        #         index=1,
        # )

    ###################################
    # Coordination constraint
    if rmc_dat.is_free_format:
        # --- SiO2 ---
        # Si の first-neighbor O 配位を先に形成し、
        # その上で SNC/Qn によって Si-O-Si network を形成させる。
        rmc_dat.set_coord_constraint(
            central_type=1,  # Si
            neighbors=[
                (2, 1.40, 1.90),  # O: Si-O neighbour range [Å]
            ],
            subconstraints=[
                (4, 0.998, 0.003),  # SiO4: 99.8 %
                (5, 0.002, 0.012),  # SiO5: 0.2 %
            ],
            index=0,
        )

        # --- Zeolite: Si -> O, CN=4 ---
        # rmc_dat.set_coord_constraint(
        #     central_type=1,  # Si
        #     neighbors=[
        #         (3, 1.40, 1.90),  # O
        #     ],
        #     subconstraints=[
        #         (4, 1.0, 0.01),
        #     ],
        #         index=0,
        # )

        # --- Zeolite: Al -> O, CN=4 ---
        # rmc_dat.set_coord_constraint(
        #     central_type=2,  # Al
        #     neighbors=[
        #         (3, 1.55, 2.10),  # O
        #     ],
        #     subconstraints=[
        #         (4, 1.0, 0.01),
        #     ],
        #         index=1,
        # )

        # --- Zeolite: O -> (Si + Al), total CN=2 ---
        # rmc_dat.set_coord_constraint(
        #     central_type=3,  # O
        #     neighbors=[
        #         (1, 1.40, 1.90),  # Si
        #         (2, 1.55, 2.10),  # Al
        #     ],
        #     subconstraints=[
        #         (2, 1.0, 0.01),
        #     ],
        #         index=2,
        # )

    # ------------------------------------------------------------------
    # FNC / topology を使用する場合だけ、次のどちらかを有効にする。
    # ------------------------------------------------------------------
    # 何も呼ばなければ、自由形式側の初期値は FNC-TYPE=NONE であり、
    # [ BPOT ] も作成されないため、FNC も topology も使用しない。
    #
    # aaa.fnc を使用する場合:
    # rmc_dat.set_fnc_switch(3)
    #
    # aaa.top を使用する場合:
    # rmc_dat.set_fnc_switch(4)

    # ------------------------------------------------------------------
    # FNC ファイルの距離範囲を RMC 実行前に変更する。
    #   固定フォーマットで FNC/TOP を用いたときの FNC/TOP の値設定
    # ------------------------------------------------------------------
    # 作成時は、packmol_util つかっていたらそれで、初期設定はされている
    # その値を、rmc するときに rmc 毎に変えるなどするには、
    # ペア指定は変えず、constraint type ごとの rmin/rmax だけを書き換える。

    # rmc_dat.set_fnc_distance_ranges(
    #     {
    #         # 1: (1.24, 1.37),  # P-O
    #         # 2: (2.02, 2.25),  # O-O
    #         # 1: (1.20, 1.45),  # P-O
    #         1: (1.20, 1.8),  # P-O
    #     }
    # )

    # 自由形式フォーマットだと element 情報が必須となる
    if rmc_dat.is_free_format:
        pass
        # element
        # element_info = config.element_info
        # rmc_dat.set_element_info(element_info)

        # --- SiO2 ---
        rmc_dat.set_element_info(["Si", "O"])

        # --- Zeolite: RMC type order 1=Si, 2=Al, 3=O, 4=Na ---
        # rmc_dat.set_element_info(["Si", "Al", "O", "Na"])

        # HST
        rmc_dat.set_history_buffer_size(200)
        # SAVE (固定フォーマットからの互換メソッドの方でセットされるのでなくてもいい)
        # HST-STEP-FACTOR は独立した時間ではなく、SAVE-TIME を基準にした倍率
        # rmc_dat.set_display_update_interval(1)

    # ------------------------------------------------------------------
    # SiO2 Qn / SNC constraint
    #   自由フォーマットのみ
    # ------------------------------------------------------------------
    # SNC を使用しない場合は、該当する set_qn_constraint() 呼び出しを
    # まとめてコメントアウトする。
    #
    # Q5/Q4/Q3 は、それぞれ独立した [ SNC ] セクションとして出力される。
    # fraction は全中心 Si に対する目標割合で、百分率ではなく 0～1 で指定する。
    if rmc_dat.is_free_format:
        pass

        # Q5 = 0.2 %
        rmc_dat.set_qn_constraint(
            central_type=1,
            first_neighbor_type=2,
            # first_neighbor_minimum=1.40,
            # first_neighbor_maximum=1.90,
            # second_neighbors=[(1, 1.40, 1.90)],
            first_neighbor_minimum=1.45,
            first_neighbor_maximum=1.80,
            second_neighbors=[(1, 1.45, 1.80)],
            coordination_number=5,
            fraction=0.002,
            # sigma=1.0,
            # sigma=0.1,
            sigma=0.04,
            index=0,
        )

        # Q4 = 99.4 %
        rmc_dat.set_qn_constraint(
            central_type=1,
            first_neighbor_type=2,
            # first_neighbor_minimum=1.40,
            # first_neighbor_maximum=1.90,
            # second_neighbors=[(1, 1.40, 1.90)],
            first_neighbor_minimum=1.45,
            first_neighbor_maximum=1.80,
            second_neighbors=[(1, 1.45, 1.80)],
            coordination_number=4,
            fraction=0.994,
            # sigma=1.0,
            # sigma=0.1,
            sigma=0.04,
            index=1,
        )

        # Q3 = 0.4 %
        rmc_dat.set_qn_constraint(
            central_type=1,
            first_neighbor_type=2,
            # first_neighbor_minimum=1.40,
            # first_neighbor_maximum=1.90,
            # second_neighbors=[(1, 1.40, 1.90)],
            first_neighbor_minimum=1.45,
            first_neighbor_maximum=1.80,
            second_neighbors=[(1, 1.45, 1.80)],
            coordination_number=3,
            fraction=0.004,
            # sigma=1.0,
            # sigma=0.1,
            sigma=0.04,
            index=2,
        )

    # ------------------------------------------------------------------
    # Zeolite SNC / Qn constraint
    #   T-O-T の相手そのものは固定しない。second neighbor は Si/Al の両方。
    # ------------------------------------------------------------------
    # if rmc_dat.is_free_format:

    #     # Si: Q4, Si-O-(Si/Al)
    #     rmc_dat.set_qn_constraint(
    #         central_type=1,
    #         first_neighbor_type=3,  # O
    #         first_neighbor_minimum=1.40,
    #         first_neighbor_maximum=1.90,
    #         second_neighbors=[
    #             (1, 1.40, 1.90),  # Si
    #             (2, 1.55, 2.10),  # Al
    #         ],
    #         coordination_number=4,
    #         fraction=1.0,
    #         sigma=0.03,
    #         index=0,
    #     )

    #     # Al: Q4, Al-O-(Si/Al)
    #     # Loewenstein rule を課す場合だけ、下の Al second neighbor を消して
    #     # second_neighbors=[(1, 1.40, 1.90)] とする。
    #     rmc_dat.set_qn_constraint(
    #         central_type=2,
    #         first_neighbor_type=3,  # O
    #         first_neighbor_minimum=1.55,
    #         first_neighbor_maximum=2.10,
    #         second_neighbors=[
    #             (1, 1.40, 1.90),  # Si
    #             (2, 1.55, 2.10),  # Al
    #         ],
    #         coordination_number=4,
    #         fraction=1.0,
    #         sigma=0.03,
    #         index=1,
    #     )

    # 26 行目：1 回の move で動かす原子数（通常 1）を設定する
    rmc_dat.set_num_atoms_per_move(1)

    return True
