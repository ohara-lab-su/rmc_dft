# rmc_dft

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/rmc_dft/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/rmc_dft/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/)

`rmc_dft` は、Reverse Monte Carlo（RMC）による実験データを再現する3次元構造モデルの生成と、
DFT によるエネルギー・原子間力に基づく構造緩和を交互に行う RMC-DFT
ワークフローを Python から構築・実行するためのパッケージです。

現在の実装は **RMC_POT + VASP** を実動系としており、
RMC と VASP の反復実行、入力条件の更新、restart、実行ごとの初期化スクリプト、
計算結果の保存など、実際の
RMC-DFT 計算を継続的に運用するための機能を含んでいます。

## 現在の位置づけ

`rmc_dft` は当初、RMC_POT の操作機能と RMC-DFT ワークフローの両方を同じパッケージ内に持っていました。

v0.7.0 で RMC_POT の入力・実行・解析に関する機能を独立した [`rmc_util`](https://pypi.org/project/rmc-util/)
パッケージへ分離しました。現在の `rmc_dft` は、VASP 側の操作と RMC-DFT ワークフローの制御を担当し、RMC_POT のハンドリングには
`rmc_util` を利用します。

新しいコードでは RMC_POT 関連クラスを `rmc_util` から直接 import します。

```python
from rmc_dft import Config, Vasp, VaspIncar, VaspKpoints
from rmc_util import RmcPot, RmcPotDat, RmcPotHst
```

この分離により、RMC_POT 単独の操作は `rmc_util`、RMC と DFT を組み合わせた計算フローは `rmc_dft` という役割分担になっています。

## サンプルスクリプトの配置

`rmc_dft install <カテゴリ>` で、指定カテゴリ以下の**すべてのファイル**をカレントディレクトリへコピーします。カテゴリのディレクトリ自体は作成しません。対象は `analyze`、`check`、`edit`、`job`、`make`、`plot`、`run`、`tools` の8カテゴリです。`all` は8カテゴリすべてをカテゴリ別ディレクトリ構造を保ってコピーします。

```bash
rmc_dft install analyze
rmc_dft install check
rmc_dft install edit
rmc_dft install job
rmc_dft install make
rmc_dft install plot
rmc_dft install run
rmc_dft install tools
rmc_dft install all
rmc_dft install plot --force
```

`rmc_dft install all` は `./analyze/`、`./check/`、`./edit/`、`./job/`、`./make/`、`./plot/`、`./run/`、`./tools/` にコピーします。個別ファイル指定は受け付けません。

例えば `rmc_dft install run` は `scripts/run/` 内の7ファイルを `./` にコピーします。既存ファイルがある場合は事前に中止し、`--force` 指定時のみ上書きします。配布には `src/rmc_dft/scripts/` に元の `scripts/` 全44ファイルを同じ構造で収録してください。


## インストール

PyPI からインストールします。

```bash
pip install rmc-dft
```

RMC_POT を利用する現在のワークフローでは `rmc_util` を使用します。

RMC_POT および VASP の実行バイナリそのものはこのパッケージには含まれません。現在の RMC-DFT
計算を実行するには、それぞれの実行環境を別途用意する必要があります。

## 現在実装されている主な機能

### RMC_POT / VASP の反復実行

現在の実運用コードでは、RMC_POT と VASP を交互に実行します。

基本的な流れは、

```text
initial structure
      |
      v
   RMC_POT
      |
      v
     VASP
      |
      v
   RMC_POT
      |
      v
     VASP
      |
     ...
```

です。

RMC 側では `rmc_util` の `RmcPot`、`RmcPotDat`、`RmcPotLog`、`RmcPotHst` などを利用し、DFT 側では `rmc_dft` の `Vasp`、
`VaspIncar`、`VaspKpoints`、`VaspLog` などを利用します。

### 計算条件のスクリプト化

RMC と VASP の条件は、実行スクリプトから変更できます。

現在のワークフローでは主に、

```text
rmc_init.py
rmc_vasp_init.py
```

を用いて RMC / VASP の計算条件を設定します。

さらに、

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

のような番号付き init を用意することで、特定の RMC / VASP run だけ異なる条件を適用できます。

番号付き init では `CONTINUE_NUMBERED_INIT` により、その設定を次の run に引き継ぐか、通常の init に戻すかを指定できます。init
ファイルは実行直前に読み込まれるため、長い RMC-DFT 計算の途中でも、その後の計算条件を変更できます。

### restart

RMC / VASP の保存済み結果を調べ、RMC または VASP のどちらから再開すべきかを判断する restart 処理を持っています。

計算結果は `rmc_log*` / `dft_log*` などの実行ごとのディレクトリへ保存され、継続計算や計算履歴の確認に利用されます。

### VASP 入力と結果のハンドリング

現在の VASP 実装には、たとえば以下が含まれます。

- `INCAR` の読み書きとパラメータ更新
- `KPOINTS` の設定
- `POTCAR` の構築
- VASP の local / MPI / job 実行
- `OUTCAR` などの結果読み取り
- 計算結果の保存
- POSCAR / CONTCAR と RMC の CFG の受け渡し
- 構造・原子移動・force 解析のための補助機能

## `RmcDft` クラス

`RmcDft` は RMC と DFT を交互に実行するための統合クラスです。

```python
from rmc_dft import Config, RmcDft

config = Config("config.yml")

rmc_dft = RmcDft(
    config=config,
)

rmc_dft.run()
```

`Config` には現在、

```python
rmc_code = "RmcPot"
dft_code = "Vasp"
```

というコード選択用の設定があり、`RmcDft` 側も RMC / DFT 実装を名前から選択する構造を持っています。

ただし、 **現時点で実際に接続されている実装は RMC_POT と VASP です**。RMCProfile や Quantum ESPRESSO
などを設定名だけで利用できる状態ではありません。

## RMC-DFT 実運用スクリプト

現在の実運用では、`RmcDft` クラスだけでなく、より細かな実行制御を行うスクリプトも使用しています。

`rmc_vasp_script.py` は、RMC と VASP の交互実行、restart、番号付き init、ログディレクトリ管理などを行います。

`rmc_vasp_script_sequence.py` では、通常の単純な RMC → VASP の繰り返しだけでなく、あらかじめ指定した RMC / VASP の実行
sequence を組むことができます。その後に通常の RMC-DFT loop を継続することもできます。

これらには歴史的な理由から `rmc_vasp` という名前が残っています。現在のパッケージ名とワークフロー全体の名称は `rmc_dft`
です。

## 設計目的と今後の方向

RMC-DFT の本質は、特定の RMC コードと特定の DFT コードを固定して呼び出すことではなく、

1. RMC により、実験データと整合する3次元構造モデルを生成する
2. DFT により、エネルギー・原子間力に基づいてその構造を緩和する
3. 両者の間で構造を受け渡しながら反復する

という計算フローにあります。

現在は RMC_POT と VASP を用いてこのワークフローを実装していますが、`rmc_dft` の設計上の目的は、最終的には特定の **RMC コードや
DFT コードに依存しない**形へ拡張することです。

エネルギー・力に基づく構造緩和側についても、必ず第一原理 DFT
で行う必要がない場合には、機械学習ポテンシャル（MLP）などによる構造緩和を選択できる構成を想定しています。これにより、大規模系や多数の反復を必要とする場合に、DFT
と MLP を目的・精度・計算量に応じて使い分けられるワークフローを目指します。

概念的には、将来的に次のような構成を対象とします。

```text
                    RMC modeling / experimental-data fitting
                              |
                    +---------+---------+
                    |                   |
                 RMC_POT            other RMC
                    |                   |
                    +---------+---------+
                              |
                           structure
                              |
                    +---------+---------+
                    |                   |
                    DFT                MLP
              (VASP, etc.)      structure relaxation
                    |                   |
                    +---------+---------+
                              |
                           structure
                              |
                             ...
```

これは **将来の設計目標**であり、現在すべてのバックエンドが実装済みという意味ではありません。現状の実動バックエンドは
RMC_POT と VASP です。

## `rmc_util` との関係

RMC_POT 関連の汎用機能は `rmc_util` に分離されています。

`rmc_util` は、RMC_POT の fixed / free format の入力、構造制約、実行、ログ・HST・FIT・PPCF の解析などを単独でも利用できるライブラリです。

`rmc_dft` はそれらを利用して、RMC と DFT の間の構造受け渡し、反復実行、restart、VASP 側の計算条件と実行、全体のワークフロー制御を担当します。

この分離により、RMC_POT の汎用機能を RMC-DFT 以外からも利用できる一方、`rmc_dft` 側では RMC-DFT
ワークフローそのものの実装に集中できる構成になっています。

## ドキュメント

- [API ドキュメント](docs/_build/html/api/modules.html)
- [チュートリアル](docs/_build/html/tutorials/index.html)

## 参考

- [rmc_util on PyPI](https://pypi.org/project/rmc-util/)
- [RMC_POT](https://www.szfki.hu/~nphys/rmc++/opening.html)
- [VASP](https://www.vasp.at/)
