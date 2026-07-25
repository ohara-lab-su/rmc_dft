# RMC_POT の TOP／ITP と FNC

このページでは、次の2クラスが実装している機能を説明します。

- `RmcPotDatTop`: RMC_POT用のGROMACS型`*.top`／`*.itp`を生成・編集する
- `RmcPotDatFnc`: RMC_POT用のFixed Neighbour Constraint `*.fnc`を生成・編集する

TOPとFNCは同じものではありません。

- TOP／ITPは、分子トポロジー、結合、角度、二面角、1–4 pair、明示的除外、仮想サイトなどを記述します。
- FNCは、最終的なRMC原子index同士について、距離を指定範囲内に保つ固定近接制約を記述します。

RMC_POTでは、通常FNCの`fnc=1/2/3`と、TOPを用いる柔軟分子の`fnc=4`は別の機能です。通常FNCと柔軟分子は同時には使用しません。

---

# 1. `RmcPotDatTop`

## 1.1 対応するTOPセクション

`RmcPotDatTop`は、RMC_POTが認識する次のセクションを扱います。

```text
[ moleculetype ]
[ atoms ]
[ pairs ]
[ bonds ]
[ angles ]
[ dihedrals ]
[ exclusions ]
[ virtual_sites2 ]
[ virtual_sites3 ]
[ virtual_sites4 ]
[ system ]
[ molecules ]
```

また、RMC_POTが認識するプリプロセッサ行も扱います。

```text
#include
#ifdef
#ifndef
#else
#endif
```

## 1.2 ファイルの読み書き

```python
from rmc_pot_dat_top import RmcPotDatTop


top = RmcPotDatTop("sample", auto_write=False)
```

拡張子を省略した場合は`sample.top`になります。既存ファイルが存在する場合は初期化時に読み込みます。

主なファイル操作は次のとおりです。

| メソッド | 機能 |
|---|---|
| `path` | 現在のTOP／ITPパスを返す |
| `load()` | 既存TOP／ITPを読み込む |
| `write()` | 検証後に現在の内容を書き出す |
| `write(out_name)` | 別名で書き出す |
| `clear()` | 保持している全内容を消去する |

`write()`は保存前に`validate()`を実行します。

## 1.3 自動保存

`auto_write=True`では、各setter／追加メソッドの実行後に書き込みます。

```python
top = RmcPotDatTop("sample", auto_write=True)
top.add_comment("comment")
```

複数項目をまとめて作る場合は、途中状態を保存しないように`auto_write=False`を使用します。

```python
top = RmcPotDatTop("sample", auto_write=False)
top.add_comment("comment", auto_write=False)
top.set_system("sample system", auto_write=False)
top.write()
```

## 1.4 低水準の行・セクション操作

TOPを直接組み立てるための低水準メソッドがあります。

| メソッド | 機能 |
|---|---|
| `add_raw_line(line)` | セクション外の任意行を追加する |
| `add_comment(comment)` | `;`で始まるコメント行を追加する |
| `add_section(name)` | 新しいセクションを追加する |
| `add_section_line(section_name, line)` | 指定セクションへ任意行を追加する |
| `get_sections()` | 全セクションを取得する |
| `get_sections(name)` | 指定名のセクションを取得する |
| `get_last_section(name)` | 最後の同名セクションを取得する |
| `remove_sections(name)` | 指定名の全セクションを削除する |

既知の専用メソッドで表現できないTOP行を保持したい場合は、`add_section_line()`を使用します。

## 1.5 includeと条件分岐

```python
top.add_include("molecule.itp", auto_write=False)
top.add_ifdef("_DEUTERIUM", auto_write=False)
top.add_raw_line("; deuterium definition", auto_write=False)
top.add_else(auto_write=False)
top.add_raw_line("; hydrogen definition", auto_write=False)
top.add_endif(auto_write=False)
```

対応メソッドは次のとおりです。

| メソッド | 出力 |
|---|---|
| `add_include(filename)` | `#include "filename"` |
| `add_ifdef(symbol)` | `#ifdef symbol` |
| `add_ifndef(symbol)` | `#ifndef symbol` |
| `add_else()` | `#else` |
| `add_endif()` | `#endif` |

`validate()`は、`#ifdef`／`#ifndef`と`#endif`の対応、および`#else`の位置を検証します。

---

# 2. TOPの分子タイプと原子

## 2.1 `[ moleculetype ]`

```python
top.begin_molecule_type(
    name="SnI4",
    exclusions=3,
    auto_write=False,
)
```

`exclusions`はGROMACSの`nrexcl`です。必要な場合はRMC_POT用の`index_offset`も指定できます。

```python
top.begin_molecule_type(
    name="MOL2",
    exclusions=3,
    index_offset=5000,
    auto_write=False,
)
```

## 2.2 `[ atoms ]`

```python
top.add_atom(
    serial=1,
    atom_type="Sn",
    residue_number=1,
    residue_name="SnI4",
    atom_name="Sn",
    charge_group=1,
    charge=0.0,
    mass=None,
    first_rmc_index=1,
    second_rmc_index=2,
    auto_write=False,
)
```

このメソッドが生成する行は次の形式です。

```text
serial type resnr residue atom cgnr charge [mass] ; first_rmc_index second_rmc_index
```

セミコロン後の2個の値はRMC_POT固有です。

- `first_rmc_index`: 同じ分子タイプの1個目の分子における、そのローカル原子のRMC index
- `second_rmc_index`: 同じ分子タイプの2個目の分子における、そのローカル原子のRMC index

これらは「分子番号」ではありません。各ローカル原子について、1個目と2個目の分子インスタンスに対応するRMC原子indexを記録します。

### SnI4のindex対応例

RMC_POTマニュアルのSnI4第1表現では、対応は次のようになります。

| ローカル原子 | 1個目の分子 | 2個目の分子 |
|---|---:|---:|
| Sn | 1 | 2 |
| I1 | 1001 | 1005 |
| I2 | 1002 | 1006 |
| I3 | 1003 | 1007 |
| I4 | 1004 | 1008 |

`[ atoms ]`では次のように記述されます。

```text
1 Sn 1 SnI4 Sn 1 0 ; 1 2
2 I  1 SnI4 I1 1 0 ; 1001 1005
3 I  1 SnI4 I2 1 0 ; 1002 1006
4 I  1 SnI4 I3 1 0 ; 1003 1007
5 I  1 SnI4 I4 1 0 ; 1004 1008
```

## 2.3 仮想原子

```python
top.add_virtual_atom(
    serial=4,
    atom_type="VS",
    residue_number=1,
    residue_name="MOL",
    atom_name="VS",
    charge_group=1,
    charge=-1.0,
    mass=0.0,
    auto_write=False,
)
```

`add_virtual_atom()`は、RMC indexを`0 0`として`[ atoms ]`に追加します。これはRMC_POTに対し、実原子ではない仮想サイトであることを示します。

---

# 3. TOPの相互作用

以下の原子番号は、RMC原子indexではなく、1分子内のGROMACSローカル原子番号です。

## 3.1 `[ pairs ]`

```python
top.add_pair(
    atom_i=1,
    atom_j=4,
    function_type=1,
    auto_write=False,
)
```

必要な力場では、V/Wパラメータも明示できます。

```python
top.add_pair(
    atom_i=1,
    atom_j=4,
    function_type=1,
    v_parameter=V_VALUE,
    w_parameter=W_VALUE,
    auto_write=False,
)
```

`v_parameter`と`w_parameter`は、両方指定するか、両方省略します。

## 3.2 `[ bonds ]`

```python
top.add_bond(
    atom_i=1,
    atom_j=2,
    equilibrium_nm=B0_NM,
    force_constant=KB,
    sigma=SIGMA_BOND,
    auto_write=False,
)
```

- `equilibrium_nm`: 平衡結合距離、単位nm
- `force_constant`: 調和結合ポテンシャルの力定数
- `sigma`: RMC_POTの重み。必要な結合タイプの最初の出現で指定する

`B0_NM`、`KB`、`SIGMA_BOND`は、採用する力場または別途決定したRMC_POTパラメータに置き換えます。本クラスは値を推定しません。

RMC用パラメータをセミコロン後へ置く場合は、次を指定します。

```python
rmc_parameters_after_semicolon=True
```

## 3.3 `[ angles ]`

```python
top.add_angle(
    atom_i=1,
    atom_j=2,
    atom_k=3,
    equilibrium_degree=THETA0_DEG,
    force_constant=KA,
    sigma=SIGMA_ANGLE,
    auto_write=False,
)
```

中央原子は`atom_j`です。

## 3.4 周期型dihedral

```python
top.add_periodic_dihedral(
    atom_i=1,
    atom_j=2,
    atom_k=3,
    atom_l=4,
    equilibrium_degree=PHI0_DEG,
    force_constant=KPHI,
    multiplicity=N,
    sigma=SIGMA_DIHEDRAL,
    auto_write=False,
)
```

## 3.5 調和型dihedral

```python
top.add_harmonic_dihedral(
    atom_i=1,
    atom_j=2,
    atom_k=3,
    atom_l=4,
    equilibrium_degree=XI0_DEG,
    force_constant=KXI,
    sigma=SIGMA_DIHEDRAL,
    auto_write=False,
)
```

## 3.6 Ryckaert–Bellemans dihedral

```python
top.add_rb_dihedral(
    atom_i=1,
    atom_j=2,
    atom_k=3,
    atom_l=4,
    coefficients=[C0, C1, C2, C3, C4, C5],
    sigma=SIGMA_DIHEDRAL,
    auto_write=False,
)
```

`coefficients`は必ず6個です。

## 3.7 明示的除外

```python
top.add_exclusion(
    centre_atom=1,
    excluded_atoms=[2, 3, 4],
    auto_write=False,
)
```

`[ exclusions ]`に、中心原子と除外対象を追加します。

---

# 4. 仮想サイト

## 4.1 2原子から作る仮想サイト

```python
top.add_virtual_site2(
    site=4,
    atom_i=1,
    atom_j=2,
    a=A,
    host_atom=1,
    auto_write=False,
)
```

## 4.2 3原子から作る仮想サイト

```python
top.add_virtual_site3(
    site=5,
    atom_i=1,
    atom_j=2,
    atom_k=3,
    function_type=1,
    parameters=[A, B],
    host_atom=1,
    auto_write=False,
)
```

`function_type`ごとに必要な`parameters`数が異なります。

| function type | RMC_POT上の種類 | parameters |
|---:|---|---|
| 1 | 3 | `a, b` |
| 2 | 3fd | `a, d_nm` |
| 3 | 3fad | `theta_degree, d_nm` |
| 4 | 3out | `a, b, c_nm_inverse` |

## 4.3 4原子から作る仮想サイト

```python
top.add_virtual_site4(
    site=6,
    atom_i=1,
    atom_j=2,
    atom_k=3,
    atom_l=4,
    a=A,
    b=B,
    c_nm=C_NM,
    host_atom=1,
    auto_write=False,
)
```

---

# 5. `[ system ]`と`[ molecules ]`

```python
top.set_system("SnI4 index mapping example", auto_write=False)
top.set_molecules([
    ("SnI4", 2),
], auto_write=False)
```

`set_system()`と`set_molecules()`は既存の同名セクションを置き換えます。

`[ molecules ]`の分子名は、`[ moleculetype ]`で定義済みでなければなりません。

---

# 6. 高水準TOP生成メソッド

## 6.1 `add_molecule_template()`

同じ分子タイプが複数存在し、RMC原子indexの並びに規則性がある場合に使用します。

```python
atoms = [
    {
        "serial": 1,
        "atom_type": "Sn",
        "residue_name": "SnI4",
        "atom_name": "Sn",
        "charge": 0.0,
        "mass": None,
    },
    {
        "serial": 2,
        "atom_type": "I",
        "residue_name": "SnI4",
        "atom_name": "I1",
        "charge": 0.0,
        "mass": None,
    },
    {
        "serial": 3,
        "atom_type": "I",
        "residue_name": "SnI4",
        "atom_name": "I2",
        "charge": 0.0,
        "mass": None,
    },
    {
        "serial": 4,
        "atom_type": "I",
        "residue_name": "SnI4",
        "atom_name": "I3",
        "charge": 0.0,
        "mass": None,
    },
    {
        "serial": 5,
        "atom_type": "I",
        "residue_name": "SnI4",
        "atom_name": "I4",
        "charge": 0.0,
        "mass": None,
    },
]

first_instance_indices = {
    1: 1,
    2: 1001,
    3: 1002,
    4: 1003,
    5: 1004,
}

second_instance_indices = {
    1: 2,
    2: 1005,
    3: 1006,
    4: 1007,
    5: 1008,
}

top.add_molecule_template(
    molecule_name="SnI4",
    atoms=atoms,
    first_instance_indices=first_instance_indices,
    second_instance_indices=second_instance_indices,
    exclusions=3,
    auto_write=False,
)
```

この例はindex対応の記述方法だけを示しています。結合、電荷、非結合パラメータの妥当性を示す例ではありません。

### `first_instance_indices`と`second_instance_indices`

各辞書のキーは分子内ローカル原子番号、値はRMC原子indexです。

```text
local serial -> RMC atom index
```

辞書は、それぞれ1個目と2個目の分子インスタンス全体について、全ローカル原子の対応を保持します。

### 一括追加できる内容

`add_molecule_template()`は次の引数を受け取ります。

- `atoms`
- `pairs`
- `bonds`
- `angles`
- `periodic_dihedrals`
- `harmonic_dihedrals`
- `rb_dihedrals`
- `explicit_exclusions`

各相互作用要素は、対応する低水準メソッドへ渡すキーワード辞書です。

```python
bonds = [
    {
        "atom_i": 1,
        "atom_j": 2,
        "equilibrium_nm": B0_NM,
        "force_constant": KB,
        "sigma": SIGMA_BOND,
    },
]
```

## 6.2 `validate_rmc_index_progression()`

1個目と2個目から得られるindex差が、3個目以降でも一定であるかを検証します。

```python
RmcPotDatTop.validate_rmc_index_progression(
    first_instance=first_instance_indices,
    second_instance=second_instance_indices,
    all_instances=[
        first_instance_indices,
        second_instance_indices,
        third_instance_indices,
    ],
)
```

各ローカル原子について、次の関係を検証します。

```text
instance n の index
= first index + (n - 1) * (second index - first index)
```

この条件を満たさない配置に`add_molecule_template()`を使用しても、RMC_POT側で後続分子のindex対応を一意に再現できません。

## 6.3 `add_explicit_network_molecule()`

不規則な連続ネットワークを、セル全体で1個のトポロジー単位として列挙するためのメソッドです。

```python
top.add_explicit_network_molecule(
    molecule_name="NETWORK",
    atoms=atoms,
    exclusions=2,
    bonds=bonds,
    angles=angles,
    auto_write=False,
)
```

各`atoms`要素には、必要に応じて最終RMC indexを`rmc_index`で与えます。

```python
{
    "serial": 1,
    "rmc_index": 1,
    "atom_type": "Si",
    "residue_name": "NETWORK",
    "atom_name": "Si1",
    "charge": 0.0,
    "mass": None,
}
```

`rmc_index`を省略した場合は`serial`を使用します。

このメソッドは次を自動設定します。

```text
first_rmc_index  = rmc_index
second_rmc_index = rmc_index
[ system ]       = molecule_name
[ molecules ]    = molecule_name 1
```

この方法ではセル内の全原子、および必要な全結合・角度・二面角を明示的に与えます。SiO2ガラスのような連続ネットワークを、根拠なく独立した小分子へ分割する機能ではありません。

---

# 7. TOPの検証

`validate()`は主に次を検証します。

- プリプロセッサ条件分岐の対応
- `[ moleculetype ]`の行数と形式
- `[ atoms ]`が`[ moleculetype ]`の後にあること
- `[ atoms ]`にfirst／second RMC indexがあること
- 分子内serialの重複
- bonds、angles、dihedrals等が存在するローカルserialを参照していること
- `[ system ]`が重複していないこと
- `[ molecules ]`の分子名が定義済みであること
- molecule countが1以上であること

検証はTOPの構文と内部参照を確認します。力場パラメータの物理的妥当性までは検証しません。

---

# 8. `RmcPotDatFnc`

## 8.1 FNCが保持する情報

FNCは次の2種類の情報を保持します。

1. 制約タイプごとの`rmin`–`rmax`
2. 各RMC原子indexについて、制約対象となる相手原子indexと制約タイプ

FNC内の原子番号は、分子内ローカル番号ではありません。最終的な`*.cfg`に対応する1始まりのRMC原子indexです。

## 8.2 初期化

```python
from rmc_pot_dat_fnc import RmcPotDatFnc


fnc = RmcPotDatFnc(
    "sample",
    atom_count=TOTAL_ATOM_COUNT,
    auto_write=False,
)
```

`atom_count`はRMC構造の全原子数です。初期化時に、1から`atom_count`までの全原子について空の近接リストを作ります。

既存FNCを読み込む場合は、ファイル名だけを指定します。

```python
fnc = RmcPotDatFnc("existing.fnc", auto_write=False)
```

## 8.3 ファイル操作

| メソッド | 機能 |
|---|---|
| `path` | 現在のFNCパスを返す |
| `initialize(atom_count)` | 全内部状態を初期化する |
| `load()` | 既存FNCを読み込む |
| `write()` | 検証後にFNCを書き出す |
| `write(out_name)` | 別名で書き出す |
| `set_title(title)` | 先頭タイトルを設定する |
| `get_title()` | タイトルを返す |
| `get_atom_count()` | 全原子数を返す |

---

# 9. FNC距離制約タイプ

## 9.1 1種類ずつ設定する

```python
fnc.set_distance_range(
    constraint_type=1,
    rmin=RMIN_1,
    rmax=RMAX_1,
    auto_write=False,
)
```

`constraint_type`は1から連番で追加します。

## 9.2 複数種類を一括設定する

辞書形式:

```python
fnc.set_distance_ranges(
    {
        1: (RMIN_1, RMAX_1),
        2: (RMIN_2, RMAX_2),
    },
    auto_write=False,
)
```

リスト形式:

```python
fnc.set_distance_ranges(
    [
        (RMIN_1, RMAX_1),
        (RMIN_2, RMAX_2),
    ],
    auto_write=False,
)
```

リストの1番目がconstraint type 1、2番目がtype 2になります。

取得:

```python
ranges = fnc.get_distance_ranges()
```

このクラスは、距離範囲を構造や元素名から推定しません。`rmin`と`rmax`は、対象系の定義に基づいて明示的に設定します。

---

# 10. FNC原子ペアの操作

## 10.1 相互ペアを1組追加する

```python
fnc.add_pair(
    atom_index1=ATOM_I,
    atom_index2=ATOM_J,
    constraint_type=1,
    auto_write=False,
)
```

`add_pair()`は、両方向を同時に登録します。

```text
ATOM_I -> ATOM_J
ATOM_J -> ATOM_I
```

## 10.2 複数ペアを一括追加する

```python
fnc.add_pairs(
    [
        (ATOM_I, ATOM_J, 1),
        (ATOM_K, ATOM_L, 2),
    ],
    auto_write=False,
)
```

各タプルは次の順です。

```text
(atom_index1, atom_index2, constraint_type)
```

## 10.3 一方向の近接だけを追加する

```python
fnc.add_neighbour(
    atom_index=ATOM_I,
    neighbour_index=ATOM_J,
    constraint_type=1,
    reciprocal=False,
    auto_write=False,
)
```

通常の相互FNCペアには`add_pair()`を使用します。`add_neighbour()`は低水準操作です。

`reciprocal=True`にすると両方向を登録します。

## 10.4 1原子の近接リストを置き換える

```python
fnc.set_atom_neighbours(
    atom_index=ATOM_I,
    neighbours=[
        (ATOM_J, 1),
        (ATOM_K, 2),
    ],
    auto_write=False,
)
```

各要素は次の形式です。

```text
(neighbour_atom_index, constraint_type)
```

このメソッドは指定原子側のリストを置き換えます。相手側を自動更新しません。相互登録が必要な通常用途では、`add_pair()`または`add_pairs()`を優先します。

取得:

```python
neighbours = fnc.get_atom_neighbours(ATOM_I)
```

戻り値は`FncNeighbour`のリストです。

## 10.5 ペアを削除する

```python
fnc.remove_pair(
    ATOM_I,
    ATOM_J,
    reciprocal=True,
    auto_write=False,
)
```

`reciprocal=True`では両方向から削除します。

## 10.6 1原子の全ペアを削除する

```python
fnc.clear_atom_neighbours(
    ATOM_I,
    reciprocal=True,
    auto_write=False,
)
```

`reciprocal=True`では、相手原子側に登録された逆向きの参照も削除します。

---

# 11. FNCテンプレート展開

## 11.1 1インスタンスを展開する

分子内ローカルペアを、実際のRMC原子indexへ展開します。

```python
local_pairs = [
    (1, 2, 1),
    (1, 3, 1),
]

local_to_rmc = {
    1: RMC_INDEX_1,
    2: RMC_INDEX_2,
    3: RMC_INDEX_3,
}

fnc.add_template_instance(
    local_pairs=local_pairs,
    local_to_rmc=local_to_rmc,
    auto_write=False,
)
```

`local_pairs`の形式は次のとおりです。

```text
(local_atom_1, local_atom_2, constraint_type)
```

`local_to_rmc`は次の対応です。

```text
local atom serial -> final RMC atom index
```

このメソッドは元素名、座標、距離からペアを生成しません。与えられたローカルペアを、与えられたRMC index対応で置き換えるだけです。

## 11.2 複数インスタンスを展開する

```python
fnc.add_template_instances(
    local_pairs=local_pairs,
    instances=[
        {
            1: RMC_INDEX_A1,
            2: RMC_INDEX_A2,
            3: RMC_INDEX_A3,
        },
        {
            1: RMC_INDEX_B1,
            2: RMC_INDEX_B2,
            3: RMC_INDEX_B3,
        },
    ],
    auto_write=False,
)
```

TOPの`first_instance_indices`／`second_instance_indices`とは異なり、FNCの`add_template_instances()`には必要な全インスタンスの対応を明示的に渡します。FNCファイル自体は、最終RMC indexを全原子について直接保持するためです。

---

# 12. 完全グラフ型のFNC

```python
fnc.add_group_complete_graph(
    atom_indices=[ATOM_1, ATOM_2, ATOM_3, ATOM_4],
    constraint_type=1,
    auto_write=False,
)
```

指定したグループ内の全組合せをFNCペアとして登録します。

4原子なら、次の6ペアが追加されます。

```text
1-2
1-3
1-4
2-3
2-4
3-4
```

これは「中心原子と周囲原子を結ぶ」操作ではありません。グループ内の全原子対を距離制約するため、用途を限定して使用します。

---

# 13. FNCの検証と取得

## 13.1 `validate()`

```python
fnc.validate()
```

標準では相互登録も検証します。

主な検証内容は次のとおりです。

- `atom_count`が1以上である
- constraint typeが1から連番である
- 原子エントリが1から`atom_count`まで存在する
- 相手原子indexが範囲内である
- constraint typeが定義済みである
- 同一原子の同一近接が重複していない
- 各FNCペアが逆方向にも同じtypeで登録されている

一方向の特殊データを検証する場合だけ、次を使用します。

```python
fnc.validate(require_reciprocal=False)
```

## 13.2 ペア一覧を取得する

```python
pairs = fnc.as_pairs(unique=True)
```

`unique=True`では、相互登録されたペアを1回だけ返します。

```text
(i, j, constraint_type)
```

両方向を取得する場合:

```python
pairs = fnc.as_pairs(unique=False)
```

---

# 14. FNC作成の基本形

具体的な距離範囲と原子indexは、対象構造に合わせて置き換えます。

```python
from rmc_pot_dat_fnc import RmcPotDatFnc


fnc = RmcPotDatFnc(
    "sample",
    atom_count=TOTAL_ATOM_COUNT,
    auto_write=False,
)

fnc.set_title("Fixed neighbours constraints (.FNC) file", auto_write=False)

fnc.set_distance_ranges(
    [
        (RMIN_1, RMAX_1),
        (RMIN_2, RMAX_2),
    ],
    auto_write=False,
)

fnc.add_pairs(
    [
        (ATOM_I, ATOM_J, 1),
        (ATOM_K, ATOM_L, 2),
    ],
    auto_write=False,
)

fnc.validate()
fnc.write()
```

---

# 15. TOPとFNCの使い分け

| 目的 | 使用するもの |
|---|---|
| 原子対を指定距離範囲内に保つ通常FNC | `RmcPotDatFnc` |
| `fnc=1/2/3`用の`*.fnc`を作る | `RmcPotDatFnc` |
| 柔軟分子の結合・角度・二面角ポテンシャル | `RmcPotDatTop` |
| `fnc=4`で分子トポロジーを与える | `RmcPotDatTop` |
| 非結合ポテンシャル用のGROMACS型トポロジー | `RmcPotDatTop` |
| 1–4 pair、除外、仮想サイト | `RmcPotDatTop` |
| 同じ分子を規則的index配置で複数扱う | `add_molecule_template()` |
| セル全体の不規則ネットワークを1単位として列挙する | `add_explicit_network_molecule()` |
| 同じローカルFNCペアを複数実体へ展開する | `add_template_instances()` |

通常FNCとTOPによる柔軟分子を混同しないことが重要です。

---

# 16. 実装上の注意

## TOP

- `add_bond()`等の原子番号は分子内ローカルserialです。
- `[ atoms ]`末尾のfirst／second indexだけがRMC原子indexです。
- 結合距離、力定数、電荷、sigmaは自動決定されません。
- `validate()`は構文と参照整合性を検証しますが、物理パラメータの妥当性は検証しません。
- `add_molecule_template()`はRMC index配置に規則性がある場合に限って使用します。
- 不規則ネットワークに、存在しない小分子テンプレートを仮定してはいけません。

## FNC

- 原子番号はすべて最終RMC原子indexです。
- `set_atom_neighbours()`は逆向き参照を自動生成しません。
- 通常の相互ペア追加には`add_pair()`／`add_pairs()`を使用します。
- `add_group_complete_graph()`はグループ内の全原子対を拘束します。
- 距離範囲とペアは自動推定されません。
- `write()`前に相互登録を含む検証が行われます。
