# 基本的な思想

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/philosophy.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/philosophy.html)

## Packmol より一段上の入力を扱う

Packmol が直接扱うのは、構造テンプレート、配置数、配置領域、最小分離距離などです。

一方、構造作成時に利用者が考えたいのは、組成比、総原子数、質量密度または数密度、分子ユニットなどです。

`packmol_util` は、この二つの層を分離します。

```text
組成・総原子数・密度・構造ユニット
                │
                ▼
           packmol_util
                │
                ▼
 structure / number / inside box / radius
                │
                ▼
              Packmol
```

利用側では Packmol の入力ファイルを直接文字列として組み立てるのではなく、Python のデータとして条件を与えることを基本とします。

## 高レベル I/F と低レベル I/F

通常の構造作成では `AmorphousBuilder` を入口として使います。

一方、セルサイズ計算、Packmol 入力生成、Packmol 実行、XYZ から POSCAR への変換などは下位のクラスから個別に利用できます。

```text
AmorphousBuilder
      │
      ├── model
      ├── PackmolInp
      └── Packmol
```

高レベル I/F に処理を閉じ込めず、必要な層だけを利用できる構造にしています。

## `builder`

`AmorphousBuilder` は全体を統合する層です。

主に、

- 組成比
- 総原子数
- 質量密度または数密度
- 最小分離距離
- Packmol に配置する template

をまとめて扱います。

組成比と総原子数から組成単位の倍率を決め、密度からセルサイズを決定し、登録された template を Packmol の入力へ渡します。

## `packmol`

`Packmol` は Packmol 実行とその周辺処理を担当します。

密度とセルサイズに関する計算、Packmol の実行、XYZ から POSCAR への変換などを担当し、構造 template 自体の定義とは分離されています。

## `packmol_inp`

`PackmolInp` は Python 側の設定を Packmol の入力形式へ変換します。

たとえば Python 側で登録した構造は、

```text
structure ...
    number ...
    inside box ...
end structure
```

という Packmol の入力へ変換されます。

packing radius を元素記号で与えた場合は、XYZ 内の原子順をもとに Packmol の atom index に変換します。

## `model`

`model` は Packmol に渡す構造 template を扱います。

単原子だけでなく、PO4 のような複数原子からなる構造ユニットも 1 個の template として作成できます。

ここで重要なのは、

- 分子・構造ユニット内部の幾何
- Packmol 配置時の排除距離

を別のものとして扱うことです。

たとえば PO4 内部の P–O 距離は XYZ template の幾何であり、packing radius ではありません。

## 組成比と総原子数

組成比 `[3, 1, 4]` は 1 組成単位あたり 8 原子を意味します。

総原子数はこの組成単位を壊さない値である必要があります。

`AmorphousBuilder` は組成比との整合を取り、実際に使用する総原子数と倍率を保持します。

この倍率は `builder.multiplier` から参照でき、template の配置数を決める基準として利用できます。

## 密度からセルサイズを決める

数密度 \(\rho_N\)、総原子数 \(N\)、立方セル一辺長 \(L\) の関係は、

\[
L = \left(\frac{N}{\rho_N}\right)^{1/3}
\]

です。

質量密度を指定する場合は、組成から平均原子量を求め、数密度へ変換してセルサイズを決定します。

Packmol 自体に密度を解釈させるのではなく、Packmol に渡す前に Python 側で配置領域へ変換します。
