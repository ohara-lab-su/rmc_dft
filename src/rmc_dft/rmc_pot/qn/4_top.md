# Topology (`*.top`)

## Topology とは

RMC_POT の `switch = 4` では、
従来の Fixed Neighbour Constraint (FNC) の代わりに
Bonded Potential を利用できる。

このとき使用する入力ファイルが

```
Topology (*.top)
```

である。

RMC_POT の Topology は、
基本的には GROMACS の topology を基に設計されている。

しかし、

**GROMACS の MD を実行するための topology そのものではなく、RMC_POT が Bonded Potential を計算するための入力ファイル**

である点に注意が必要である。

---

# FNC との違い

FNC は

```
距離
```

のみを拘束する。

一方 Topology では

- Bond
- Angle
- Dihedral
- Improper
- Pair

など、
分子内ポテンシャルを利用できる。

したがって

```
Si-O

だけではなく

O-Si-O

Si-O-Si
```

まで拘束できる。

これは
ガラスネットワークを保持する上で
非常に大きな違いとなる。

---

# RMC_POT における Bonded Potential

RMC_POT は
Move を生成した後、

```
実験データへの適合度
```

だけではなく

```
Bond Energy

Angle Energy

...
```

も同時に評価する。

そのため

```
距離だけ合っているが

角度が崩壊している
```

ような構造は
受理されにくくなる。

これは
従来の FNC よりも
物理的な拘束方法である。

---

# Topology の構成

Topology は
GROMACS と同様に

```text
[ moleculetype ]

[ atoms ]

[ bonds ]

[ pairs ]

[ angles ]

[ dihedrals ]

...
```

という Section から構成される。

RMC_POT は
必要な Section のみを利用する。

本ライブラリでは
現在主に

```
atoms

bonds

angles
```

を生成している。

---

# 本ライブラリでの考え方

Topology は

```
分子
```

を書くためのものではない。

ここでいう Molecule は

```
局所ネットワーク
```

を意味する。

つまり

```
巨大な共有結合ネットワーク
```

を

```
RMC_POT が扱える Molecule
```

へ変換することが目的である。

---

# Bond の生成

QnNetworkAnalysis が生成した

```
Central

↓

Bridge
```

情報から

```
Bond List
```

を作成する。

SiO₂ では

```
Si

↓

O
```

だけが Bond となる。

Bridge 同士や

```
Si-Si
```

は Bond としない。

---

# Angle の生成

Bond 情報から

```
O-Si-O

Si-O-Si
```

角度を生成する。

これらは

```
Bond

↓

共有原子探索

↓

Angle
```

という流れで作られる。

例えば

```
O

↓

Si

↓

O
```

なら

```
O-Si-O
```

Angle が生成される。

---

# Bond Parameter

Topology の Bond には

```
平衡距離

力定数
```

が必要となる。

本ライブラリでは
JSON に定義された

```
bond_parameters
```

を利用して出力する。

一般には

```
r0

kb
```

が対応する。

---

# Angle Parameter

Angle も同様に

```
θ0

kθ
```

を利用する。

例えば SiO₂ なら

```
O-Si-O

109.47°
```

などが代表的な値となる。

---

# Atom 情報

Topology の

```
[ atoms ]
```

には

- Atom Type
- Charge
- Mass

などが記述される。

これらも
JSON 設定から取得する。

現在の実装では
SiO₂ 用設定を利用することを前提としている。

---

# Unit Topology

現在のライブラリでは

```
write_unit_topology()
```

によって

```
局所 Unit
```

単位で Topology を生成する。

これは

```
SiO4
```

四面体などを
独立 Unit として扱うことを目的としている。

Unit 内では

```
Bond

Angle
```

を保持するが、

Unit 間には
Bond を張らない。

そのため

```
局所構造は保持しながら

ネットワーク全体には自由度を残す
```

という拘束が可能となる。

---

# Network Topology

一方

```
write_network_topology()
```

では

解析された Network 全体を
一つの Topology として出力する。

つまり

```
Si-O-Si-O-Si
```

というネットワーク全体を
Bonded Potential として扱う。

こちらは

```
ネットワークを維持したまま
RMC を行いたい
```

場合に利用する。

一方で、

局所構造だけを拘束したい場合には
拘束が強すぎる可能性がある。

---

# Unit Topology と Network Topology の違い

| 項目 | Unit Topology | Network Topology |
|------|---------------|------------------|
| 拘束対象 | 局所構造 | ネットワーク全体 |
| Bond | Unit 内のみ | 全 Network |
| Angle | Unit 内のみ | 全 Network |
| 自由度 | 高い | 低い |
| ネットワーク組換え | 起こり得る | 起こりにくい |

どちらを利用すべきかは、
RMC の目的によって異なる。

---

# SiO₂ 実装との関係

現在の実装は

```
Si

↓

O

↓

Si
```

ネットワークを前提としている。

したがって

- Bond
- Angle
- Unit

の作り方も
SiO₂ を想定した実装になっている。

例えば

```
nearest = 4
```

や

```
O-Si-O
```

Angle は
SiO₄ 四面体を前提としている。

そのため、
Topology Writer 自体は汎用であるが、
現在の Network Builder は
SiO₂ 向けアルゴリズムである。

---

# RmcConstraintWriter の役割

Topology Writer は

```
QnNetworkAnalysis
```

が生成した

```
Bond

Angle

Atom 情報
```

を

RMC_POT が理解できる

```
Topology
```

へ変換するだけである。

つまり

```
解析

↓

抽象ネットワーク

↓

Topology
```

という責務分離になっている。

この設計により、

Topology の書式変更や
RMC_POT の拡張があっても、
ネットワーク解析アルゴリズムを変更せずに対応できる。

次章では、
JSON 設定ファイルと各クラスの対応、
および現在の SiO₂ 実装と他材料への展開について解説する。