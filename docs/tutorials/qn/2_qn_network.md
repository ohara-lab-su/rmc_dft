# Qn ネットワーク解析

## 目的

RMC_POT の FNC や Topology を作成するためには、

「どの原子同士が局所構造を構成しているか」

を決定する必要がある。

本ライブラリでは、この局所構造を

```
Central
      │
   Bridge
      │
Second
```

という三層構造として定義する。

SiO₂ の場合は

```
Si
 │
 O
 │
Si
```

となる。

この構造をネットワークとして解析し、
Qn 値や Bond 情報を生成する。

---

# ネットワークモデル

本ライブラリでは
ネットワークを

```
Central ----- Bridge ----- Second
```

という一般形で表現する。

各原子種は JSON から指定される。

例えば SiO₂ では

```
Central : Si
Bridge  : O
Second  : Si
```

である。

この設計により、
解析アルゴリズム自体は
SiO₂ 固有ではない。

---

# Qn の定義

Qn は

「Central に結合している Bridge のうち、
別の Central とも結合している Bridge の本数」

として定義される。

例えば

```
      Si
      │
O─────┼─────O
│           │
Si         Si
```

では

```
Q2
```

となる。

Bridge が他の Central に接続していない場合は
Non-bridging Oxygen (NBO) とみなされる。

---

# 解析手順

解析は概ね次の順で行われる。

```
POSCAR

↓

原子種抽出

↓

Central 抽出

↓

Bridge 抽出

↓

Second 抽出

↓

Central-Bridge 探索

↓

Bridge-Second 探索

↓

Bridge 判定

↓

Qn 判定

↓

Bond 情報生成

↓

Angle 情報生成

↓

FNC Pair 生成
```

---

# 1. 原子種抽出

POSCAR に含まれる原子種を読み込み、

JSON に定義された

- central_types
- bridge_types
- second_types

へ分類する。

この段階では距離判定は行わない。

---

# 2. Central–Bridge 探索

Central と Bridge の近傍探索を行う。

探索方法は

```
cutoff
```

または

```
nearest
```

の二種類である。

### cutoff

距離範囲内のすべてを採用する。

```
first_min
～

first_max
```

の範囲で判定する。

### nearest

距離条件を満たした候補から

```
N 個
```

だけ採用する。

SiO₂ では

```
nearest = 4
```

を利用することが多い。

これにより

```
SiO4
```

四面体が安定して得られる。

---

# 3. Bridge–Second 探索

Bridge から見た
Second 原子を探索する。

方法は二種類ある。

## second_use_first_network = false

Bridge を中心に
改めて距離探索を行う。

```
O

↓

Si
```

を距離だけで探索する。

最も単純な方法である。

---

## second_use_first_network = true

Bridge–Second を
新たに探索しない。

すでに求めた

```
Central

↓

Bridge
```

のネットワークを反転し、

```
Bridge

↓

Second
```

を構成する。

こちらの方が

Central–Bridge

と

Bridge–Second

の整合性が保たれるため、
SiO₂ ではこちらを推奨する。

---

# 4. Bridge 判定

Bridge ごとに

```
Bridge

↓

Second
```

が何個存在するか調べる。

Central 自身は除外し、

```
別の Central
```

へ接続しているものだけを

```
Bridge
```

とみなす。

---

# 5. Qn 判定

Central ごとに

```
Bridge

↓

別 Central
```

となっている Bridge を数える。

例えば

```
4 本

↓

Q4
```

```
3 本

↓

Q3
```

```
2 本

↓

Q2
```

となる。

Qn は
Bridge の本数ではなく、

Bridge のうち

「他の Central と共有されているもの」

だけを数える。

---

# 解析結果

解析後には
次の情報が生成される。

```
Central ごとの Qn

Bridge 情報

Bond 情報

Angle 情報

FNC Pair
```

これらは
RMC の書式とは独立した
抽象ネットワーク情報である。

以降の Writer は
この情報だけを利用して
RMC_POT の

- FNC

- Topology

を書き出す。

つまり

```
解析

↓

抽象ネットワーク

↓

RMC ファイル
```

という三段階構成になっている。

これにより、

解析アルゴリズム

と

出力フォーマット

を完全に独立させている。