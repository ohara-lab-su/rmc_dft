# JSON 設定ファイル

## 概要

本ライブラリでは、
解析アルゴリズムのほとんどを
JSON ファイルから設定できるようになっている。

これにより、

- 解析対象元素
- Neighbor 判定
- Bond Parameter
- Angle Parameter
- FNC Type

などをプログラムを変更せずに切り替えられる。

現在は SiO₂ 用設定ファイルを利用しているが、
JSON を変更することで他材料へ適用できるよう設計されている。

---

# 設定の流れ

処理全体では

```text
POSCAR

↓

JSON

↓

QnNetworkBuilder

↓

QnNetworkAnalysis

↓

RmcConstraintWriter
```

という流れになる。

Builder は
JSON を各クラスへ渡すだけであり、

解析内容そのものは
JSON に依存する。

---

# network

network は

```
Central

↓

Bridge

↓

Second
```

ネットワークを定義する。

代表的な設定は

```
central_types

bridge_types

second_types
```

である。

SiO₂ では

```
Central = Si

Bridge = O

Second = Si
```

となる。

この三種類の原子が
ネットワーク解析の対象となる。

---

# Neighbor 探索

Neighbor 探索では

```
first
```

と

```
second
```

を別々に定義する。

### First

```
Central

↓

Bridge
```

探索である。

ここでは

```
探索方法

最小距離

最大距離

最近接数
```

などを設定できる。

---

### Second

```
Bridge

↓

Second
```

探索である。

こちらも

```
最小距離

最大距離
```

を設定できる。

---

# second_use_first_network

この設定は
本ライブラリの重要な項目である。

```
false
```

では

```
Bridge

↓

Second
```

を改めて距離探索する。

```
true
```

では

```
Central

↓

Bridge
```

ネットワークを反転して
Second を構成する。

SiO₂ では

```
true
```

の方が
ネットワーク整合性が保たれる。

---

# Bond Parameter

Topology の

```
Bond
```

情報を定義する。

一般には

```
Atom Type

平衡距離

力定数
```

を指定する。

Writer は
この情報を

```
[ bonds ]
```

へ書き出す。

---

# Angle Parameter

Topology の

```
Angle
```

を定義する。

一般には

```
Angle Type

平衡角

力定数
```

を指定する。

Writer は

```
[ angles ]
```

へ変換する。

---

# Atom 情報

Topology の

```
[ atoms ]
```

には

```
Atom Type

Mass

Charge
```

などが必要となる。

これらも
JSON に定義されている。

現在の実装では

```
Si

O
```

用の設定を利用する。

---

# FNC Type

FNC は

```
Type

↓

距離範囲
```

で管理される。

JSON では

```
Type 1

↓

1.55〜1.75 Å
```

などを定義する。

Writer は
これを

```
type_id

↓

(rmin,rmax)
```

へ変換し、

FNC Header を生成する。

---

# JSON の役割

JSON は

```
解析

```

と

```
Writer
```

の両方で利用される。

ただし、
利用内容は異なる。

解析では

```
Neighbor

Qn 判定

元素
```

を利用する。

Writer では

```
Bond

Angle

Mass

Charge

FNC Range
```

を利用する。

---

# SiO₂ に依存する設定

現在の JSON は
SiO₂ を対象としている。

具体的には

```
Central = Si

Bridge = O

Second = Si
```

という前提である。

さらに

```
nearest = 4
```

で

```
SiO₄
```

四面体を構成する。

また

```
O-Si-O
```

角度も
四面体を想定している。

このため、

JSON は変更可能であっても、
その値自体は SiO₂ 固有である。

---

# 他材料への適用

解析アルゴリズム自体は

```
Central

↓

Bridge

↓

Second
```

という一般モデルで設計されている。

したがって、

例えば

```
P-O-P

B-O-B

Ge-O-Ge

Al-O-Si
```

のような
架橋酸素ネットワークには
比較的容易に適用できる。

変更が必要なのは

- 原子種
- Neighbor 距離
- Bond Parameter
- Angle Parameter
- FNC Range

程度である。

---

# 適用が難しい材料

一方で

```
Fe

Ni

Cu
```

などの
金属ガラスや

```
液体

単純結晶
```

では、

```
Central

↓

Bridge

↓

Second
```

という構造そのものが
意味を持たない場合が多い。

このような系では
JSON を変更するだけでは対応できず、
QnNetworkAnalysis の
解析アルゴリズム自体を拡張する必要がある。

---

# 設計思想

本ライブラリでは

```
アルゴリズム

↓

JSON
```

ではなく

```
アルゴリズム

＋

JSON
```

という設計になっている。

つまり、

JSON によって

```
元素

距離

Parameter
```

は変更できるが、

```
Central-Bridge-Second
```

というネットワークモデル自体は
プログラム側が持っている。

このため、

SiO₂ 系や
類似したネットワーク材料では
高い再利用性を持つ一方、

ネットワーク構造の概念が異なる材料では
解析アルゴリズムの拡張が必要となる。

次章では、
現在の SiO₂ 実装を基に、
どこまで他材料へ展開できるか、
また今後の拡張方針について考察する。