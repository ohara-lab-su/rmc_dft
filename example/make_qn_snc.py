#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

SiO2 の Q4/Q3/Q2 割合を指定した自由形式 RMC_POT *.dat 作成例。
"""

# from rmc_dft.rmc_pot.rmc_pot_dat_free import RmcPotDatFree
from rmc_util.rmc_pot_dat_free import RmcPotDatFree

OUTPUT_NAME = "sio2_qn"

# RMC の原子タイプ番号です。
# この例では *.cfg 内のタイプ順を Si=1、O=2 と仮定します。
SI_TYPE = 1
O_TYPE = 2

# Si の Qn 分率を百分率で指定します。
# 合計は必ず 100.0 % にしてください。
Q4_PERCENT = 80.0
Q3_PERCENT = 15.0
Q2_PERCENT = 5.0

# Si-O の第一近接距離範囲 [Å]。
SI_O_MIN = 1.40
SI_O_MAX = 1.90

# O-Si の第二近接距離範囲 [Å]。
# SNC の STYPE_FROM_TO は、第一近接 O から第二近接 Si までの距離です。
O_SI_MIN = 1.40
O_SI_MAX = 1.90

# 各 Qn 制約の重みパラメータです。
Q4_SIGMA = 1.0
Q3_SIGMA = 1.0
Q2_SIGMA = 1.0


def validate_percentages() -> None:
    """Q4/Q3/Q2 の百分率指定を検証する。

    Raises:
        ValueError: いずれかの割合が範囲外、または合計が 100 % でない場合。
    """
    percentages = [
        Q4_PERCENT,
        Q3_PERCENT,
        Q2_PERCENT,
    ]

    for percentage in percentages:
        if percentage < 0.0:
            raise ValueError("Qn の割合は 0 % 以上で指定してください。")
        if percentage > 100.0:
            raise ValueError("Qn の割合は 100 % 以下で指定してください。")

    total = sum(percentages)
    tolerance = 1.0e-10
    if abs(total - 100.0) > tolerance:
        raise ValueError(
            "Q4_PERCENT、Q3_PERCENT、Q2_PERCENT の合計は "
            f"100 % にしてください。現在値は {total} % です。"
        )


def percent_to_fraction(percent: float) -> float:
    """百分率を RMC_POT の SNC で使用する分率へ変換する。

    Args:
        percent: 0 から 100 までの百分率。

    Returns:
        0 から 1 までの分率。
    """
    return percent / 100.0


def add_sio2_qn_constraints(dat: RmcPotDatFree) -> None:
    """SiO2 の Q4/Q3/Q2 制約を ``[ SNC ]`` セクションへ追加する。

    Args:
        dat: 更新対象の自由形式 ``*.dat`` クラス。

    Notes:
        各制約は、中心 Si が指定数の第一近接 O を持ち、その O が
        第二近接 Si を持つ状態を対象にします。Q4、Q3、Q2 の割合は、
        全中心 Si に対する分率として設定します。
    """
    dat.clear_qn_constraints(auto_write=False)

    dat.add_qn_constraint(
        central_type=SI_TYPE,
        first_neighbor_type=O_TYPE,
        first_neighbor_minimum=SI_O_MIN,
        first_neighbor_maximum=SI_O_MAX,
        second_neighbors=[
            (
                SI_TYPE,
                O_SI_MIN,
                O_SI_MAX,
            ),
        ],
        coordination_number=4,
        fraction=percent_to_fraction(Q4_PERCENT),
        sigma=Q4_SIGMA,
        auto_write=False,
    )

    dat.add_qn_constraint(
        central_type=SI_TYPE,
        first_neighbor_type=O_TYPE,
        first_neighbor_minimum=SI_O_MIN,
        first_neighbor_maximum=SI_O_MAX,
        second_neighbors=[
            (
                SI_TYPE,
                O_SI_MIN,
                O_SI_MAX,
            ),
        ],
        coordination_number=3,
        fraction=percent_to_fraction(Q3_PERCENT),
        sigma=Q3_SIGMA,
        auto_write=False,
    )

    dat.add_qn_constraint(
        central_type=SI_TYPE,
        first_neighbor_type=O_TYPE,
        first_neighbor_minimum=SI_O_MIN,
        first_neighbor_maximum=SI_O_MAX,
        second_neighbors=[
            (
                SI_TYPE,
                O_SI_MIN,
                O_SI_MAX,
            ),
        ],
        coordination_number=2,
        fraction=percent_to_fraction(Q2_PERCENT),
        sigma=Q2_SIGMA,
        auto_write=False,
    )


def main() -> None:
    """SiO2 用の自由形式 ``sio2_qn.dat`` を作成する。"""
    validate_percentages()

    # auto_write=False とし、すべての設定後に一度だけファイルへ書き込みます。
    dat = RmcPotDatFree(
        cfg_name=OUTPUT_NAME,
        auto_write=False,
        version="#003",
    )

    dat.set_comment(
        "SiO2 Q4/Q3/Q2 constrained RMC",
        auto_write=False,
    )

    # この例では既存の一般設定を残し、Qn 制約だけを明示的に設定します。
    # 数密度、cutoff、最大移動量、実験データ指定などは、
    # 実際の *.cfg と RMC 条件に合わせて別途設定してください。
    add_sio2_qn_constraints(dat)

    dat.write()

    print(f"{OUTPUT_NAME}.dat を作成しました。")
    print(
        "Q4={:.3f} %, Q3={:.3f} %, Q2={:.3f} %".format(
            Q4_PERCENT,
            Q3_PERCENT,
            Q2_PERCENT,
        )
    )


if __name__ == "__main__":
    main()
