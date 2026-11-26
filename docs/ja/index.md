# rmc_dft

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/index.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/index.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.ja.html)

`rmc_dft` は、実験データに合う構造を RMC_POT で生成し、VASP でエネルギー・原子間力に基づいて緩和する反復計算を制御します。

## パッケージの役割

| パッケージ | 担当 |
| --- | --- |
| `rmc_dft` | RMC と VASP の構造受け渡し、反復、再開、手動シーケンス、統合設定と解析例 |
| [`rmc_util`](https://ohara-lab-su.github.io/rmc_util/ja/) | RMC_POT の DAT・FNC・TOP 入力、単独実行、ログ・FIT・HST・PPCF 解析 |
| [`vasp_util`](https://ohara-lab-su.github.io/vasp_util/ja/) | VASP の入力作成、単独実行と保存、POSCAR・OUTCAR・軌跡の読み取りと構造解析 |

RMC_POT と VASP の機能は、元の `rmc_dft` から段階的に分離されました。新しいコードでは各機能を提供元から読み込みます。旧コード向けに残っている再公開は一部の名前だけに対応しています。

```python
from rmc_dft import Config, RmcDft
from rmc_util import RmcPot, RmcPotDat
from vasp_util import Vasp, VaspIncar, VaspPoscar
```

## インストールとスクリプトの配置

Python 3.10 以上が必要です。連携計算を行う場合は RMC_POT と VASP の実行環境も別途用意してください。

```bash
pip install rmc-dft
rmc_dft install list
rmc_dft install run
```

`list` は同梱ファイルをカテゴリ付きのパスと1行の用途説明で表示します。`install <カテゴリ>` は指定カテゴリの中身をカレントディレクトリへコピーします。カテゴリは `analyze`、`check`、`edit`、`job`、`make`、`plot`、`run`、`tools` です。`install all` はカテゴリ別のディレクトリを作って全ファイルをコピーします。コピー単位はカテゴリです。コピー先に同名ファイルがある場合は配置前に中止します。上書きする場合は `--force` を指定します。

単独の RMC 結果を描画する `plot_fit.py`、`plot_hst.py`、`plot_ppcf.py`、`plot_ppcf2.py` は `rmc_util` 0.1.12 で配置できます。複数 run の比較や RMC–VASP の収束履歴を描画するスクリプトは `rmc_dft install plot` にあります。

## 統合計算の準備と起動

1. `rmc_dft install run` で配置した `config.yml` に構造名、実験データ、実行バイナリ、VASP の実行方法を設定します。通常開始では初期構造を `POSCAR0` として用意し、RMC の DAT と実験データ、VASP の INCAR・KPOINTS・POTCAR を準備します。
2. 計算条件を実行前に変更する場合は `rmc_init.py` に `run_rmc_init()`、`rmc_vasp_init.py` に `run_vasp_init()` を用意します。`rmc_util` の `rmc_init.py` と `vasp_util` の `vasp_init.py` は準備の出発点にできます。VASP 側のファイルは統合 runner が読む名前 `rmc_vasp_init.py` で置きます。`scripts/run/` には統合用の init は含まれません。
3. 作業ディレクトリから次のコマンドで起動します。

```bash
python -m rmc_dft.runners.rmc_vasp_script
```

通常 runner は RMC_POT の結果構造を `POSCAR` に渡し、VASP の後処理で生成した CFG を次の RMC に使います。結果は `logNN_rmc` と `logNN_dft` に保存されます。同じモジュールに `restart` を渡すと、最新のログ名から再開段階を選びます。番号付き init（`rmc_init_N.py`、`rmc_vasp_init_N.py`）は対応する run の直前に読み込まれ、`CONTINUE_NUMBERED_INIT` で後続 run への適用を指定できます。

手動シーケンスでは `rmc_vasp_script_sequence_dat.py` の `manual_sequence` と `continue_rmc_dft` を編集し、`python -m rmc_dft.runners.rmc_vasp_script_sequence` で起動します。各番号付き init も作業ディレクトリに用意します。

`RmcDft` クラスは交互実行の Python API です。上記 runner が番号付き init、restart、手動順序を管理します。設定できるバックエンドの実装は RMC_POT と VASP です。将来的には別の RMC コードや、機械学習ポテンシャルによる緩和を選択できる構成を目指しています。

## 既存サンプルの利用

一部の解析・制約生成例は移行途中です。`analyze/` の解析例や `check/check_rmc_*.py` には移動済みの旧 import、`make/make_analyze_qn.py` と `make/make_qn_fnc_top.py` には別途 `qn` モジュールへの参照が残っています。`job/` の PBS 例はクラスタ固有の設定と旧ローカル起動ファイルの指定を持つため、使用環境と現在の runner の起動方法に合わせて編集してください。

```{toctree}
:maxdepth: 2
:hidden:

tutorials/index
api/modules
```
