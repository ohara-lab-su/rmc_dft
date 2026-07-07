# qn_network_state

VASP/POSCAR 形式の構造ファイル 1 個から、Si-O-Si 型ネットワーク状態を調べる最小構成です。

## 方針

- コマンドライン引数は使いません。
- 読み込むファイル名や出力名は `run_qn_network_state.py` の変数を書き換えます。
- `qn_network.py` は変更しません。
- `qn_config_sio2.json` は変更しません。
- 複数構造の比較機能は入れていません。
- このスクリプトは、与えられた 1 構造の network state を出すだけです。

## ファイル

- `qn_network_state.py`
  - 再利用用モジュールです。
  - VASP 読み込み、Si-O bond 判定、Qn/O 配位、連結成分、CSV/TXT 出力を行います。
- `run_qn_network_state.py`
  - 実行用スクリプトです。
  - 冒頭の変数だけを書き換えて使います。

## 使い方

`run_qn_network_state.py` の冒頭を書き換えます。

```python
STRUCTURE_FILE = "structure_after.vasp"
CONFIG_FILE = "qn_config_sio2.json"
OUTPUT_PREFIX = "structure_after"
```

実行します。

```bash
python run_qn_network_state.py
```

## 出力

`OUTPUT_PREFIX` が `structure_after` の場合、以下を出力します。

- `structure_after_network_state.txt`
  - Qn 分布
  - O0/O1/O2/O3... 分布
  - Si ネットワーク連結成分
  - 最大連結成分比率
- `structure_after_atoms.csv`
  - 各 Si/O 原子の coordination と network label
- `structure_after_bonds.csv`
  - 判定された Si-O bond と距離

## 判定

`qn_config_sio2.json` の `qn.first_min` と `qn.first_max` を使い、Si-O 距離で bond を判定します。

Qn は、各 Si に結合した O のうち、2 個以上の Si に結合している O の数として数えます。

O 配位は、その O に結合した Si 数です。O2 は通常の bridging oxygen、O1 は non-bridging oxygen、O3 は tricluster oxygen に相当します。
