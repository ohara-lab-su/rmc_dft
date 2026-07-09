# SiO₂ 実装と他材料への展開

## 概要

本ライブラリは

```
Central

↓

Bridge

↓

Second
```

というネットワークモデルを基本として設計されている。

そのため、
現在の実装は SiO₂ を対象としているものの、
アルゴリズム自体はある程度一般化されている。

一方で、

Qn の定義

Topology の作り方

Bond Parameter

などは SiO₂ の構造を強く反映している。

ここでは、
どこまでが汎用実装であり、
どこからが SiO₂ 専用実装なのかを整理する。

---

# SiO₂ 固有となる部分

現在の実装で
SiO₂ 固有となる部分は
主に次の四点である。

```
Qn の定義

SiO4 四面体

Bond Parameter

Angle Parameter
```

これらは
単純に元素名を書き換えただけでは
利用できない。

---

# 1. Qn の定義

Qn は本来

```
SiO4 四面体が

何本の Bridge Oxygen を持つか
```

というケイ酸塩で用いられる概念である。

例えば

```
Q4
```

は

```
4 本すべてが Bridge Oxygen
```

である。

```
Q3
```

なら

```
Non Bridging Oxygen

1 本
```

を持つ。

つまり

```
Qn
```

という名称自体は
ケイ酸塩特有の用語である。

そのため、

ライブラリ内部では
Qn と呼んでいるが、

実際には

```
Bridge 数解析
```

を行っていると考える方が一般化しやすい。

---

# 2. SiO4 四面体

Neighbor 探索では

```
nearest = 4
```

が標準となっている。

これは

```
SiO4
```

四面体を前提としている。

例えば

```
PO4
```

四面体なら
同じ設定で利用できる。

しかし

```
TiO6

AlO6
```

八面体では

```
nearest = 6
```

へ変更する必要がある。

つまり、

Neighbor アルゴリズムは汎用であるが、

既定値は SiO₂ 向けである。

---

# 3. Bond Parameter

Topology の

```
Bond
```

は

```
Si-O
```

を前提としている。

平衡距離も

```
Si-O
```

で設定されている。

他材料では

```
P-O

Ge-O

Al-O
```

などへ変更する必要がある。

これは
JSON で対応可能である。

---

# 4. Angle Parameter

現在は

```
O-Si-O

Si-O-Si
```

が中心である。

これも

```
PO4

BO3

GeO4
```

などでは
変更が必要となる。

---

# 汎用化されている部分

逆に、
次の部分は材料に依存しない。

---

## Structure

```
VaspStructure
```

は
完全に汎用である。

元素にも
ネットワークにも依存しない。

POSCAR を扱うだけである。

---

## Neighbor Search

Neighbor 探索も
材料依存ではない。

距離と

```
nearest
```

だけで探索している。

---

## Network Model

```
Central

↓

Bridge

↓

Second
```

というモデル自体も
比較的汎用である。

例えば

```
P-O-P

Ge-O-Ge

Al-O-Si

B-O-B
```

などにも利用できる。

---

## Writer

Writer は

```
解析結果
```

しか見ていない。

したがって

```
Si

O
```

という情報は持っていない。

Writer 自体は
RMC_POT の書式へ変換するだけなので、
最も汎用性が高い。

---

# どの材料まで利用できるか

## そのまま利用しやすい材料

比較的容易に利用できるもの

```
SiO2

GeO2

P2O5

B2O3

AlPO4

Al-Si-O 系
```

これらは

```
架橋酸素
```

という概念が存在する。

そのため、

Bridge Network

という考え方を
そのまま利用できる。

---

## 少し修正が必要な材料

例えば

```
Li2SiO3

Li2Si2O5

Na2SiO3
```

などでは

```
Modifier Cation
```

が存在する。

この場合

```
Li

Na
```

は

Bridge

にはならない。

Qn 判定では

```
Si

↓

O

↓

Si
```

だけを見る必要がある。

Neighbor 探索はそのまま使えるが、

解析条件は
JSON を調整する必要がある。

---

## アルゴリズム変更が必要な材料

例えば

```
Li3PO4

Li3PS4

NASICON
```

では

```
Li
```

がネットワーク形成原子ではない。

目的も

```
Li 拡散

Li Site
```

解析となる。

この場合

```
Bridge Network
```

という考え方そのものが
解析目的と一致しない。

したがって

QnNetworkAnalysis を
そのまま利用することは難しい。

---

## 適用が困難な材料

例えば

```
Fe

Ni

Cu

Pd

Pt
```

などの
金属ガラスでは

```
Bridge Oxygen
```

が存在しない。

Qn の概念自体がない。

この場合は

Neighbor Graph

Voronoi

CN

Delaunay
```

など、
全く異なる解析アルゴリズムが必要となる。

---

# 今後の拡張

現在の実装は

```
QnNetworkAnalysis
```

という名前になっている。

しかし、
実際に行っている処理は

```
Bridge Network Analysis
```

である。

将来的には

```
NetworkAnalysis
```

という抽象クラスを用意し、

```
QnNetworkAnalysis

PO4NetworkAnalysis

OctahedralNetworkAnalysis

MetalNetworkAnalysis
```

などへ派生させる構成が考えられる。

Builder は

```
JSON

↓

解析クラス選択
```

だけを行えばよい。

これにより、

Writer は変更せずに
解析アルゴリズムだけを差し替えられる。

---

# 本ライブラリの位置付け

本ライブラリは

```
Qn を解析するライブラリ
```

というよりも、

```
局所ネットワークを解析し、

RMC_POT の拘束入力へ変換するライブラリ
```

として設計されている。

現在は SiO₂ を対象としているため、
Qn 解析が中心となっているが、

設計そのものは

```
構造解析

↓

抽象ネットワーク

↓

RMC_POT 入力
```

という三段階構成になっている。

この責務分離により、

- 新しい解析アルゴリズム
- 新しい材料
- 新しい拘束形式

を比較的容易に追加できる構成となっている。

以上で、本ライブラリの設計思想、解析アルゴリズム、RMC_POT の FNC/Topology 生成、および SiO₂ を中心とした適用範囲についての解説を終える。