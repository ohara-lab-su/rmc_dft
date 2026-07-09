# README0
# RMC Topology / FNC Generator

## 概要

本モジュールは、VASP/POSCAR 構造から局所ネットワーク構造を解析し、
RMC_POT の構造拘束入力である **FNC (`*.fnc`)** および
**Topology (`*.top`)** を自動生成するためのライブラリである。

もともとは `qn_network.py` という単一スクリプトとして実装されていたが、
RMC-DFT ワークフローへ組み込むためにライブラリ化され、
役割ごとにクラスへ分割された。

本ライブラリの目的は、

- VASP 構造から局所ネットワークを抽出する
- Qn 構造を解析する
- RMC_POT が理解できる拘束形式へ変換する
- RMC-DFT ワークフロー中で自動生成できるようにする

ことである。

本ライブラリは **一般的な構造解析ライブラリではない**。
RMC_POT の入力生成を目的とした専用ライブラリであり、
RMC_POT の FNC および Topology の考え方に沿って設計されている。

---

# 設計方針

本ライブラリでは、一つの巨大なクラスへ全処理を書くことを避け、
責務ごとにクラスを分離している。

各クラスは次のような責務のみを持つ。

```
             POSCAR
                │
                ▼
      VaspStructure
                │
                ▼
     QnNetworkAnalysis
                │
                ▼
   RmcConstraintWriter
                │
                ▼
        *.fnc / *.top
```

全体をまとめる入口として

```
QnNetworkBuilder
```

のみを利用する。

利用者は Builder を呼び出すだけでよく、
解析の詳細を意識する必要はない。

---

# クラス構成

## VaspStructure

構造情報のみを管理するクラスである。

責務

- POSCAR 読み込み
- 格子情報保持
- 原子情報保持
- PBC 距離計算
- PBC ベクトル計算
- 角度計算

このクラスは

- Qn
- Topology
- FNC

については一切知らない。

純粋な構造情報クラスとして実装されている。

---

## QnNetworkAnalysis

ネットワーク解析を担当するクラスである。

本ライブラリの中心となるクラスである。

責務

- 原子種抽出
- Neighbor 探索
- Qn 判定
- Bond 情報生成
- Angle 情報生成
- FNC 用 Pair 生成

解析結果は

- Qn 分布
- Bond 情報
- Bridge 情報
- FNC Pair

として保持される。

解析結果そのものは
RMC の書式とは無関係である。

つまり、

```
構造
    ↓
解析
    ↓
抽象ネットワーク情報
```

までがこのクラスの責務である。

---

## RmcConstraintWriter

解析結果を
RMC_POT の入力形式へ変換するクラスである。

責務

- FNC 出力
- Topology 出力

解析処理は一切行わない。

入力は

```
QnNetworkAnalysis
```

のみである。

---

## QnNetworkBuilder

ライブラリ利用者が利用する入口である。

Builder は

```
POSCAR
      ↓
Structure

      ↓
Analysis

      ↓
Writer
```

を順番に実行する。

利用者は

```python
builder = QnNetworkBuilder.from_poscar(...)
builder.write_all(...)
```

のみを呼び出せばよい。

Builder 自身は解析ロジックを持たない。

---

# 本ライブラリの特徴

本ライブラリでは

「構造解析」

と

「RMC 入力生成」

を明確に分離している。

そのため

```
解析アルゴリズム
```

を変更しても

```
Writer
```

を変更する必要はない。

逆に

```
RMC_POT の書式変更
```

があっても

```
解析アルゴリズム
```

へ影響しない。

この責務分離は、
今後 RMC_POT 以外の拘束形式へ対応する場合にも有効である。

---

# RMC_POT における FNC と Topology

RMC_POT では
局所構造を維持する方法として
大きく二種類の方法が存在する。

- FNC (Fixed Neighbour Constraint)
- Topology (Bonded Potential)

本ライブラリは
両方の入力ファイルを生成できる。

両者は目的は似ているが、
拘束方法は全く異なる。

以降の章では、

- Qn ネットワーク解析
- FNC
- Topology

について順に解説する。