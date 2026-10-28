# リファレンス

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/reference.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/reference.html)

このページは主要コンポーネントの役割を人間向けに整理したものです。

クラス、メソッド、引数、型注釈、docstring の完全な一覧は {doc}`api/modules` に自動生成されます。

## `AmorphousBuilder`

構造生成全体をまとめる高レベル I/F です。

主な役割:

- 元素と組成比の保持
- 総原子数と組成比の整合
- 組成単位倍率の決定
- 質量密度または数密度からセルサイズを決定
- Packmol template の登録
- Packmol 入力生成
- Packmol 実行
- POSCAR 変換

通常の利用ではこのクラスを入口にします。

## `Packmol`

Packmol の実行と、その周辺の数値処理を担当します。

主な役割:

- 原子量・平均原子量
- 質量密度と数密度の変換
- 原子数と数密度からセルサイズを計算
- Packmol 実行
- XYZ から POSCAR への変換

## `PackmolInp`

Packmol 入力ファイルの構築を担当します。

構造 template、配置数、配置領域、packing radius などを Packmol の入力文法へ変換します。

## `model`

Packmol に渡す構造 template と recipe を扱います。

単原子 template のほか、複数原子からなる構造ユニットの XYZ template を生成できます。

## `Config`

設定ファイルから `packmol_util` の設定値を読み込むためのクラスです。

## `param`

原子量など、密度・セルサイズ計算に利用する定数を保持します。

## API Reference

```{toctree}
:maxdepth: 2

api/modules
```

この部分は手書きではありません。`docs/build.sh` が `src/packmol_util` を走査してビルド時に生成します。


## 公開 API の使用上の区別

| コンポーネント | 主要 API | 役割 |
| --- | --- | --- |
| `AmorphousBuilder` | `__init__`, `multiplier`, `add_template`, `build` | 組成・密度・テンプレートから構造を生成 |
| `PackmolInp` | `__init__`, `add_structure`, `write` | `.inp` を生成 |
| `Packmol` | `number_density_from_mass_density`, `mass_density_from_number_density`, `cell_length_from_number_density` | 密度とセル長の計算 |
| `Packmol` | `compute_element_counts`, `compute_cell_sizes`, `get_unit_atom_count` | 原子数と組成比 |
| `Packmol` | `run_packmol`, `xyz_to_poscar`, `write_fnc_file`, `count_atoms_in_xyz` | 実行、変換、FNC 出力 |
| `model` | `write_xyz_template`, `write_single_atom_xyz`, `write_tetrahedral_unit_xyz` | XYZ テンプレート作成 |
| `model` | `StructureSpec`, `MaterialRecipe`, `make_material_recipe`, `make_atomic_mixture_recipe` | 配置レシピ |
| `model` | `make_tetrahedral_unit_fnc_pairs`, `make_tetrahedral_unit_fnc_spec_from_ranges`, `TetrahedralUnitFncSpec` | 正四面体 FNC |
| `model` | `solve_packing_radii_from_pair_distances` | 元素ペア距離から配置半径を近似 |
| `Config` | `__init__(yaml_path=...)`, `load_yaml()` | YAML 設定の読込 |

### `AmorphousBuilder` の引数

`symbols` と `ratios` は対応する元素と整数比です。`total_atom_count` は希望原子数、`minimum_separation` は Packmol の `tolerance`、`mass_density` は g/cm³、`number_density` は Å⁻³、`packmol_bin` は実行ファイル名またはパスです。密度を両方指定した場合、**数密度が優先**されます。`add_template(xyz_file, number, packing_radii=None, fnc_pairs_in_template=None, fnc_distance_ranges=None, fnc_output_constraint_types=None)` の `number` はテンプレートの**複製個数**であり、原子数ではありません。

### `PackmolInp` の引数

`PackmolInp(minimum_separation_distance, output_xyz, box_length, use_pbc=False)` は立方体セルを使用します。`add_structure(xyz_file, number, packing_radii_by_atom_symbol=None)` の半径辞書は元素記号をキーとします。`write(inp_file)` はテンプレート内の元素記号を 1 始まりの Packmol atom index に変換し、必要に応じて `atoms ... radius ... end atoms` を出力します。

### `Config` の読み込み

`Config(yaml_path="settings.yaml")` はインスタンス属性を、`Config.load_yaml("settings.yaml")` はクラス属性を YAML のキーで上書きします。存在しないキーは `NO SUCH VAR:` と表示されます。`load_yaml()` の引数省略時は環境変数 `PACKMOL_UTIL_CONFIG_YAML` を参照します。インスタンス生成時の `yaml_path` 省略は YAML を読み込みません。`Config` の初期値は Fe–Si–B 系の例示設定であり、`AmorphousBuilder` が自動的に参照するものではありません。

### 制約

`Packmol.write_fnc_file()` は type 1 から連続する拘束種を要求します。`Packmol.xyz_to_poscar()` は Packmol 入力内の最初の `inside box` 行から立方セルの長さを取得します。`PackmolInp` の `pbc` と `inside box` は同じセル長を使用します。入力ファイルを直接変更する場合、セル長の解釈との整合を保ってください。
