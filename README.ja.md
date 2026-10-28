# packmol_util

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fpackmol_util-181717?logo=github)](https://github.com/ohara-lab-su/packmol_util/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/packmol_util/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/)

Packmol を用いて、第一原理計算（VASP）や分子動力学（MD）シミュレーションのためのアモルファス初期構造（POSCAR）を生成する Python ライブラリです。

組成比、総原子数、質量密度または数密度を入力し、Packmol 入力ファイルの作成、実行、XYZ から POSCAR（Direct 座標）への変換を行います。単原子テンプレートと分子ユニットの両方を扱い、RMC_POT の FNC ファイルも生成できます。

## 特徴

- 組成と質量密度または数密度から立方セルの一辺長を計算します。
- 元素記号別の packing radius を XYZ の原子番号指定に変換します。
- PO4 などの構造ユニットを XYZ テンプレートとして配置します。
- `AmorphousBuilder` が入力作成、Packmol 実行、POSCAR 変換を連続して処理します。

## ディレクトリ構成

```text
src/
├── packmol_util/
│   ├── __init__.py
│   ├── builder.py
│   ├── model.py
│   ├── packmol.py
│   ├── packmol_inp.py
│   └── param.py
└── example/
    ├── Li3PO4/
    │   └── make_Li3PO4.py
    └── FeSiB/
        └── make_FeSiB.py
```

## インストール

```sh
pip install packmol-util
```

Packmol 本体は別途導入が必要です。[Packmol 公式リポジトリ](https://github.com/m3g/packmol)を参照し、実行ファイルを PATH に置くか `packmol_bin` で指定してください。ビルド手順と入力形式は[チュートリアル](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)に記載しています。

## 使用例：Fe–Si–B

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz

for element in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{element}.xyz", element)

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"], ratios=[80, 9, 11],
    total_atom_count=500, minimum_separation=2.0, mass_density=7.35,
)
for element, ratio in zip(builder.symbols, builder.ratios):
    builder.add_template(f"{element}.xyz", ratio * builder.multiplier)
builder.build("FeSiB")
```

Packmol 入力・XYZ・ログと `POSCAR`、`POSCAR.vasp` が生成されます。総原子数が組成比の合計で割り切れない場合は自動調整されます。POSCAR のファイル名は現行実装では固定です。

## 分子ユニットと RMC 用 FNC

`write_tetrahedral_unit_xyz()` で PO4 などの構造テンプレートを生成できます。`add_template()` に `fnc_pairs_in_template`、`fnc_distance_ranges`、`fnc_output_constraint_types` を指定すると、テンプレート内局所番号を最終 POSCAR の原子番号に対応付け、FNC 拘束を出力できます。分子内の幾何と Packmol の配置用排除半径は別の設定です。

詳細は[チュートリアル](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)、[設計思想](https://ohara-lab-su.github.io/packmol_util/ja/philosophy.html)、[リファレンス](https://ohara-lab-su.github.io/packmol_util/ja/reference.html)を参照してください。


