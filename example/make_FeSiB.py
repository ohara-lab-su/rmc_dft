#!/usr/bin/env python
"""
FeSiB の Packmol 初期構造を作るサンプルである。

このスクリプトは、分子ユニットを使わない【単原子混合系】の例である。
Fe.xyz、Si.xyz、B.xyz という 1 原子テンプレートを作り、それぞれを指定個数だけ
Packmol に配置させる。

【ユニット構造の明示による整理】
FeSiB では、すべての構成要素が単一の原子（粒）として独立している。
そのため、登録すべきユニットは [Fe, Si, B] の3つの単原子ユニットとなり、
1式単位（Formula Unit）あたりの構成比は、そのまま全体の化学量論比 [80, 9, 11] と
ダイレクトに一致するデータ構造として整理・峻別される。
"""

import shutil

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz


def main() -> None:
    """
    Fe80Si9B11 の単原子混合初期構造を Packmol で作る。
    """
    # ------------------------------------------------------------
    # FeSiB の物質固有条件を指定する。
    # total_atom_count はセル内に入れる総原子数である。
    # ratios=[80, 9, 11] により、Fe 80 個、Si 9 個、B 11 個を配置する。
    # ------------------------------------------------------------
    total_atom_count: int = 500
    mass_density_g_cm3: float = 7.0

    symbols = ["Fe", "Si", "B"]
    ratios = [80, 9, 11]

    # ------------------------------------------------------------
    # 【ユニットベースのデータ定義】
    # この系を構成する「ユニット」のテンプレートファイルと比率を明示する。
    #
    # FeSiB では、各ユニットは 1 原子だけを含む Fe.xyz / Si.xyz / B.xyz である。
    # unit_ratio は Fe80Si9B11 の組成比そのものであり、builder.multiplier を掛けることで
    # Packmol に渡す実際の配置個数になる。
    #
    # radii は、必要な場合にだけ Packmol 配置用の元素記号別 packing 半径を与える欄である。
    # このサンプルでは全体の minimum_separation_distance だけを使うため None とする。
    # ------------------------------------------------------------
    fe_si_b_units = {
        "Fe": {"xyz": "Fe.xyz", "unit_ratio": 80, "radii": None},
        "Si": {"xyz": "Si.xyz", "unit_ratio": 9, "radii": None},
        "B": {"xyz": "B.xyz", "unit_ratio": 11, "radii": None},
    }

    # ------------------------------------------------------------
    # Packmol が単原子テンプレート同士を配置するときの全体的な近接回避距離である。
    # FeSiB では分子ユニットを作らないため、PO4 のような分子内距離指定は存在しない。
    # ------------------------------------------------------------
    minimum_separation_distance: float = 2.3

    # ============================================================
    # 2. ユニットテンプレート（XYZ）の自動生成
    # ============================================================
    # 各元素を「1原子だけが含まれる最小のユニット」として出力
    for sym in symbols:
        write_single_atom_xyz(f"{sym}.xyz", sym)

    # ============================================================
    # 3. 汎用ビルダーの実行 (既存の AmorphousBuilder をそのまま使用)
    # ============================================================
    # 物質固有の組成比、目標の総原子数、質量密度から、必要なセル一辺長 L を自動計算し、
    # 総原子数が組成比の整数倍にならない場合は自動補正を行う。
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        mass_density=mass_density_g_cm3,  # 質量密度 [g/cm^3] での指定
        total_atom_count=total_atom_count,  # 希望するベースの総原子数
        minimum_separation=minimum_separation_distance,  # 配置時の全体的な近接回避距離
    )

    # ============================================================
    # 4. 整理されたユニットをビルダーに引き渡す（共通ループ処理）
    # ============================================================
    # add_template メソッドの引数の仕様（xyz_file, number, packing_radii）に従い、
    # 1式単位あたりのユニット数 (unit_ratio) に、ビルダーが内部で計算した
    # 全体のスケール倍率 (builder.multiplier) を乗算して、正確なパッキング個数 (number) を算出する。
    #
    # メソッド引数の説明：
    #   xyz_file: Packmol に渡す1個の単原子テンプレートの座標ファイル名 (.xyz)
    #   number: そのテンプレートを Packmol がセル内に何個配置するかを表す実際の複製個数
    #   packing_radii: Packmol 配置時に使う元素記号別の排除半径である。
    #                  FeSiB サンプルでは全体条件だけを使うため None とする。
    # ============================================================
    for unit_name, cfg in fe_si_b_units.items():
        calculated_number = cfg["unit_ratio"] * builder.multiplier
        builder.add_template(
            xyz_file=cfg["xyz"],
            number=calculated_number,  # 同期された引数名 'number' で配置個数を引き渡す
            packing_radii=cfg["radii"],
        )

    # 5. 構築実行
    builder.build(output_prefix="FeSiB")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
