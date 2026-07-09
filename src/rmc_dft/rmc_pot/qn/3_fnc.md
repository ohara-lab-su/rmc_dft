# FNC (Fixed Neighbour Constraint)

## FNC とは

FNC (Fixed Neighbour Constraint) は、
RMC_POT が持つ局所構造拘束機能である。

通常の Reverse Monte Carlo では、
実験データとの一致のみを評価するため、

- 化学結合が切れる
- 配位数が大きく変化する
- ネットワークが崩壊する

といった構造が生成されることがある。

FNC はこれを防ぐために導入された拘束であり、
指定した近接原子間の距離が一定範囲内に保たれるよう
Monte Carlo の受理判定へ拘束条件を加える。

---

# RMC_POT における FNC の位置付け

RMC_POT では

```
switch = 1
switch = 2
switch = 3
```

で FNC が利用される。

一方、

```
switch = 4
```

では GROMACS 形式 Topology を利用した
Bonded Potential が使用される。

そのため、

```
switch = 4
```

では FNC と Topology は
役割が一部重複するが、
拘束方法は全く異なる。

---

# FNC の考え方

FNC は

```
距離拘束
```

のみを扱う。

例えば

```
Si ----- O
```

が

```
1.55 Å

～

1.75 Å
```

の範囲内であることを要求する。

距離がこの範囲を外れる Move は
受理されない、
あるいは受理確率が低下する。

つまり

```
Bond Potential
```

ではなく

```
Allowed Distance Range
```

を与える拘束である。

---

# 本ライブラリでの FNC 生成

本ライブラリでは、
Qn ネットワーク解析から得られた

```
Central

↓

Bridge
```

の結合情報を利用して
FNC を生成する。

解析段階では

```
(atom_i,
 atom_j,
 type_id)
```

という情報のみを保持している。

ここで

```
type_id
```

は

```
距離範囲
```

を表す番号である。

Writer は
この type_id を
RMC_POT の FNC 定義へ変換する。

---

# FNC Type

RMC_POT の FNC では

```
Type 1

↓

1.55〜1.75 Å
```

```
Type 2

↓

2.45〜2.70 Å
```

のように、

距離範囲を

```
type_id
```

で管理する。

本ライブラリでも
JSON に定義された

```
fnc_ranges
```

を読み込み、

```
type_id

↓

(rmin, rmax)
```

へ変換する。

これにより
同じ距離拘束を持つ Pair を
一つの Type として共有できる。

---

# FNC Pair

解析結果から生成される Pair は

```
(atom_i,
 atom_j,
 type_id)
```

である。

Writer はこれを

```
各 atom が

どの atom と

どの Type の拘束を持つか
```

という RMC_POT の入力形式へ並べ替える。

つまり

```
Pair List
```

ではなく

```
Atom List
```

へ変換して出力している。

---

# FNC ファイル構成

本ライブラリが生成する FNC は
概ね次の構成となる。

```text
FNC Type 数

各 Type の最小距離

各 Type の最大距離

原子数

Atom 1

拘束数

相手 atom

Type

Atom 2

...
```

実際には
各原子ごとに

```
拘束数

↓

拘束相手

↓

拘束 Type
```

が並ぶ。

この形式は
RMC_POT が要求する
固定近接拘束入力形式に対応している。

---

# Pair の対称性

本ライブラリでは

```
Si ----- O
```

という拘束は

```
Si

↓

O
```

だけではなく

```
O

↓

Si
```

としても保持する。

これは
RMC_POT の入力が

```
各 atom の拘束一覧
```

という形式だからである。

そのため、
内部では Pair を対称化してから
出力を行う。

---

# Type 管理

Writer は
Type 番号が

```
1

↓

2

↓

3

↓

...
```

と連番になっていることを確認する。

これは
RMC_POT が

```
Type 番号

↓

距離範囲
```

を
番号順で読み込むためである。

途中の番号が欠落している場合は
設定ミスと判断し、
エラーとして処理する。

---

# FNC の特徴

FNC は

```
距離
```

しか拘束しない。

そのため、

- Bond Angle
- Dihedral
- 剛性

などは表現できない。

SiO₂ のような
四面体ネットワークでは

```
Si-O
```

距離だけでは

```
O-Si-O

Si-O-Si
```

角度は保持されない。

そのため
局所構造をより厳密に保持したい場合は

```
switch = 4
```

を利用し、

Topology による Bonded Potential を
利用する方が適している。

---

# 本ライブラリでの位置付け

FNC は

```
QnNetworkAnalysis
```

が生成した

```
抽象ネットワーク情報
```

から

```
RmcConstraintWriter
```

が生成する。

解析アルゴリズムは
FNC の書式を知らず、

Writer は
Qn 判定を知らない。

この責務分離により、

- 解析アルゴリズム

と

- RMC_POT の書式

を独立して保守できる設計となっている。

次章では、
Bond・Angle・Molecule を扱う
Topology (`*.top`) の生成方法について解説する。