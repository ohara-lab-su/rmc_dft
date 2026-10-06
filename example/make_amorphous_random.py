#!/usr/bin/env python3
"""
Packmol を用いて、多元素系の完全ランダムなアモルファス初期構造を作成する。

各元素を単原子テンプレートとして独立に配置するため、分子ユニット、結合、
配位構造、FNC 拘束は一切与えない。

物質固有の条件は main() 冒頭の symbols、ratios、密度、総原子数、
minimum_separation_distance、output_prefix で指定する。
コマンドライン引数は使用しない。
"""

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz


def main() -> None:
    """単原子テンプレートを用いて完全ランダムな初期構造を生成する。"""
    # ============================================================
    # 材料条件
    # ============================================================
    symbols = ["Li", "S", "P", "C"]
    ratios = [43, 39, 5, 13]

    # 今回は ratios の合計が 100 なので、total_atom_count=100 とすると
    # Li:43, S:39, P:5, C:13 の構造になる。
    total_atom_count: int = 100

    # 密度情報
    # AmorphousBuilder には質量密度または数密度のどちらか一方を渡す。
    # 今回は指定された数密度を使用する。
    # mass_density_g_cm3: float = 1.4000000000
    number_density_A3: float = 0.0453277972

    # Packmol の tolerance に対応する全原子共通の最小分離距離 [Å]。
    # 完全ランダム配置だが、非物理的な原子重なりだけは避ける。
    minimum_separation_distance: float = 1.8

    output_prefix: str = "LiSPC_random"

    # mass_density_g_cm3 は、数密度との対応を記録するために残している。
    # 実際のセル長計算には number_density_A3 を使用する。
    # print(f"mass density   : {mass_density_g_cm3:.10f} g/cm^3")
    print(f"number density : {number_density_A3:.10f} 1/A^3")

    # ============================================================
    # 単原子テンプレートの作成
    # ============================================================
    # 各元素について 1 原子だけを含む XYZ を作る。
    # 分子ユニットを作らないため、全元素が独立な原子として配置される。
    for symbol in symbols:
        write_single_atom_xyz(
            filename=f"{symbol}.xyz",
            element=symbol,
        )

    # ============================================================
    # Packmol によるランダム配置
    # ============================================================
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        total_atom_count=total_atom_count,
        number_density=number_density_A3,
        minimum_separation=minimum_separation_distance,
    )

    # builder.multiplier は、ratios 全体を何倍するかを表す。
    # 今回は ratios の合計と total_atom_count がともに 100 なので 1 となる。
    for symbol, ratio in zip(symbols, ratios):
        builder.add_template(
            xyz_file=f"{symbol}.xyz",
            number=ratio * builder.multiplier,
            packing_radii=None,
            fnc_pairs_in_template=None,
            fnc_distance_ranges=None,
            fnc_output_constraint_types=None,
        )

    # FNC 定義を与えていないため、拘束ファイルは生成されない。
    # POSCAR、POSCAR.vasp、Packmol 入力、XYZ、ログが出力される。
    builder.build(output_prefix=output_prefix)

    print(f"total atoms    : {builder.total_atom_count}")
    print(f"box length     : {builder.box_length:.10f} A")
    for symbol, ratio in zip(symbols, ratios):
        atom_count = ratio * builder.multiplier
        print(f"{symbol:>2s} atoms       : {atom_count}")


if __name__ == "__main__":
    main()
