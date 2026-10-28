# チュートリアル

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/tutorial.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)

## 単原子 template から構造を作る

Fe–Si–B のように、各元素を独立した単原子 template として配置する例です。

### template を作る

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Fe.xyz", "Fe")
write_single_atom_xyz("Si.xyz", "Si")
write_single_atom_xyz("B.xyz", "B")
```

それぞれ 1 原子だけを含む XYZ template が生成されます。

### Builder を作る

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    mass_density=7.0,
)
```

組成比の和は 100 なので、この場合の組成単位の倍率は、

```python
builder.multiplier
```

から取得できます。

### template を登録する

```python
builder.add_template(
    "Fe.xyz",
    80 * builder.multiplier,
)

builder.add_template(
    "Si.xyz",
    9 * builder.multiplier,
)

builder.add_template(
    "B.xyz",
    11 * builder.multiplier,
)
```

### 構造を生成する

```python
builder.build("FeSiB")
```

`build()` により Packmol 入力生成、Packmol 実行、出力構造の変換が行われます。

## 数密度を指定する

質量密度の代わりに数密度を指定できます。

```python
builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    number_density=0.08,
)
```

計算されたセル一辺長は、

```python
print(builder.box_length)
```

で確認できます。

## 分子ユニットを配置する

Li3PO4 のように PO4 を 1 個の構造ユニットとして配置する場合は、PO4 の XYZ template を作ります。

### Li template

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Li.xyz", "Li")
```

### PO4 template

```python
from packmol_util.model import write_tetrahedral_unit_xyz

write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.51,
)
```

ここで指定している距離は PO4 内部の幾何です。

### Builder

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
```

Li3PO4 は 1 組成単位あたり 8 原子なので、512 原子では 64 組成単位です。

### template を登録する

```python
builder.add_template(
    xyz_file="Li.xyz",
    number=3 * builder.multiplier,
)

builder.add_template(
    xyz_file="PO4.xyz",
    number=builder.multiplier,
    packing_radii={
        "P": 0.25,
        "O": 1.05,
    },
)
```

`packing_radii` は PO4 内部の結合距離ではなく、Packmol が template を配置するときの排除距離に使われます。

### 構造を生成する

```python
builder.build("Li3PO4")
```

## 低レベル API

高レベルの `AmorphousBuilder` を使わず、下位 API を個別に利用することもできます。

たとえば Packmol 入力だけを組み立てたい場合は `PackmolInp`、密度やセルサイズの計算、Packmol 実行、XYZ → POSCAR 変換などを個別に扱いたい場合は `Packmol` を利用します。

各クラスとメソッドの最新のシグネチャは {doc}`api/modules` を参照してください。


## Packmol のインストール

`packmol_util` は Packmol 実行ファイルを同梱しません。Packmol を別途インストールし、`packmol` コマンドを実行できる状態にします。実行ファイルを別の場所に置く場合は `AmorphousBuilder(packmol_bin="...")` にパスを指定します。

- [Packmol 公式サイト](https://m3g.iqm.unicamp.br/packmol/)
- [Packmol ソースコード](https://github.com/m3g/packmol)
- [Packmol ソースアーカイブ](https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz)

Linux でソースからビルドする例：

```sh
wget https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz
tar xzf packmol.tar.gz
cd packmol
make
```

macOS で GNU Fortran を使用する例：

```sh
brew install gcc
tar xzf packmol.tar.gz
cd packmol
FC=gfortran-14 F77=gfortran-14 ./configure
make
```

`gfortran-14` はインストール済みのコンパイラ名に合わせて変更します。ビルド手順は Packmol のバージョンにより異なるため、配布元の手順も確認してください。実行ファイルの場所を `PATH` に追加するか、`packmol_bin` で指定します。

## Packmol 入力ファイルと低レベル API

Packmol は XYZ テンプレート、配置個数、配置領域を入力ファイルで指定します。以下は Fe、Si、B の単原子テンプレートを配置する入力例です。

```text
tolerance 2.0
pbc 20.0 20.0 20.0
filetype xyz
output FeSiB_packmol.xyz

structure Fe.xyz
  number 80
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure Si.xyz
  number 9
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure B.xyz
  number 11
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure
```

`PackmolInp` を使うと同じ構造を Python から記述できます。ここではセル長を例示値の 20 Å とし、密度から計算しません。

```python
from packmol_util.model import write_single_atom_xyz
from packmol_util.packmol_inp import PackmolInp
from packmol_util.packmol import Packmol

for symbol in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{symbol}.xyz", symbol)

inp = PackmolInp(
    minimum_separation_distance=2.0,
    output_xyz="FeSiB_packmol.xyz",
    box_length=20.0,
    use_pbc=True,
)
for symbol, count in (("Fe", 80), ("Si", 9), ("B", 11)):
    inp.add_structure(f"{symbol}.xyz", count)
inp.write("FeSiB_packmol.inp")

runner = Packmol()
runner.run_packmol("FeSiB_packmol.inp", "FeSiB_packmol.log")
index_map = runner.xyz_to_poscar(
    xyz_file="FeSiB_packmol.xyz",
    poscar_file="POSCAR",
    packmol_inp="FeSiB_packmol.inp",
    elements=["Fe", "Si", "B"],
)
```

`run_packmol()` は入力ファイルを Packmol の標準入力に渡し、標準出力と標準エラーをログに保存します。`xyz_to_poscar()` は `inside box` からセル長を読み取り、Cartesian 座標を Direct 座標へ変換し、元素ごとに並べ替えます。戻り値 `index_map` は Packmol XYZ の 1 始まり原子番号から POSCAR の 1 始まり原子番号への辞書です。

## 密度、組成比、総原子数

`AmorphousBuilder` は数密度を直接指定するか、質量密度と組成比から数密度を求めます。数密度を \(n\) [Å\(^{-3}\)]、総原子数を \(N\) とすると、立方セルの一辺は \(L=(N/n)^{1/3}\) [Å] です。質量密度 \(\rho\) [g cm\(^{-3}\)]、平均原子量 \(\bar M\) [g mol\(^{-1}\)] の場合、\(n=\rho N_A 10^{-24}/\bar M\) です。

```python
from packmol_util.packmol import Packmol
pm = Packmol()
counts = pm.compute_element_counts(["Fe", "Si", "B"], [80, 9, 11], 503)
number_density = pm.number_density_from_mass_density(
    ["Fe", "Si", "B"], [80, 9, 11], 7.35
)
length = pm.cell_length_from_number_density(500, number_density)
print(counts, length)
```

`Packmol.compute_element_counts()` は総原子数を固定し、端数の大きい元素に残余を配分するため、厳密な組成比にならない場合があります。一方 `AmorphousBuilder` は `total_atom_count` を `sum(ratios)` の最も近い整数倍に補正し、組成比を維持します。補正後の原子数は `builder.total_atom_count`、倍率は `builder.multiplier` で確認します。`model.make_atomic_mixture_recipe()` は整数倍でない原子数を受け付けず `ValueError` を送出します。これらの動作は異なります。

## 構造レシピとテンプレート

`model` は XYZ テンプレートの作成と、配置数をまとめるデータ構造を提供します。`StructureSpec` はテンプレートファイル、配置数、元素別 packing 半径を保持します。`make_material_recipe()` は各 XYZ の先頭行からテンプレート内原子数を読み、`number × テンプレート原子数` の合計を `MaterialRecipe.total_atom_count` に設定します。`make_atomic_mixture_recipe()` は単原子 XYZ の生成とレシピ作成を同時に行います。

```python
from packmol_util.model import make_atomic_mixture_recipe
recipe = make_atomic_mixture_recipe(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=500,
)
assert recipe.total_atom_count == 500
```

`StructureSpec` や `MaterialRecipe` を作成するだけでは Packmol は実行されません。`AmorphousBuilder` に渡す場合は `recipe.structures` を順に `builder.add_template()` へ登録します。

## 正四面体テンプレートと RMC_POT FNC

PO4 の場合、テンプレートの局所原子番号は P=1、O=2–5 です。FNC の原子ペアは局所番号で登録し、Packmol 実行後に POSCAR の原子番号へ変換されます。`make_tetrahedral_unit_fnc_pairs()` は P–O の 4 ペア（type 1）と O–O の 6 ペア（type 2）を返します。

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import (
    write_single_atom_xyz,
    write_tetrahedral_unit_xyz,
    make_tetrahedral_unit_fnc_pairs,
)

write_single_atom_xyz("Li.xyz", "Li")
write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.515,
)

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
builder.add_template("Li.xyz", 3 * builder.multiplier)
builder.add_template(
    "PO4.xyz",
    builder.multiplier,
    packing_radii={"P": 0.25, "O": 1.05},
    fnc_pairs_in_template=make_tetrahedral_unit_fnc_pairs(),
    fnc_distance_ranges={1: (1.45, 1.65), 2: (2.40, 2.65)},
    fnc_output_constraint_types=[1, 2],
)
builder.build("Li3PO4")
```

`fnc_output_constraint_types=None` は全 type を出力します。`[1]` は type 1 のみを出力します。FNC の選択は Packmol に渡す XYZ の形状や配置条件には影響しません。`Packmol.write_fnc_file()` は FNC type が **1 から始まる連続整数**であることを要求するため、type 2 のみを指定する `[2]` は現行実装ではエラーになります。

`make_tetrahedral_unit_fnc_spec_from_ranges()` は FNC の距離範囲から各中央値を計算し、正四面体としての整合性を検査してテンプレート用代表距離と FNC ペアを返します。中心–頂点距離 \(d\) と頂点–頂点距離 \(a\) は \(a=d\sqrt{8/3}\) を満たす必要があります。`geometry_distance_tolerance` は幾何検査の許容差であり、FNC 距離範囲の幅ではありません。

`solve_packing_radii_from_pair_distances()` は元素ペアの希望最小距離を半径和で近似します。全元素の自己ペアと異種ペアの距離が必要です。`pair_distance_tolerance` は距離表の近似誤差の許容値であり、Packmol の `tolerance` とは異なります。探索は離散的であり、任意の距離表に対する解の存在を保証しません。

## 出力ファイルと実装上の条件

`builder.build("FeSiB")` の出力は `FeSiB_packmol.inp`、`FeSiB_packmol.xyz`、`FeSiB_packmol.log`、`POSCAR`、`POSCAR.vasp` です。FNC ペアが登録されている場合に限り、既定で `FeSiB.fnc` が出力されます。FNC 出力先は `build(output_prefix, fnc_file=...)` で変更できます。`POSCAR` と `POSCAR.vasp` は接頭辞にかかわらず固定名のため、同じ作業ディレクトリで複数回実行すると上書きされます。

`add_template(number=...)` の配置数と各テンプレート内の原子数の積の合計は、補正後の `builder.total_atom_count` に一致させてください。現行 `AmorphousBuilder` はこの一致を `build()` の開始時に検査しません。FNC は Packmol XYZ のテンプレート配置順と POSCAR の元素別並べ替えに依存します。FNC 原子番号は **1 始まり**です。
