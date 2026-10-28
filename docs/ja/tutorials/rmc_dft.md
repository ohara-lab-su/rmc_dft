# RMC-DFT 実行チュートリアル

> 対象: **rmc_dft v0.6.13**
>
> `rmc_vasp_script.py` による通常の RMC → VASP → RMC → VASP ... の自動実行と、`rmc_init_N.py` / `rmc_vasp_init_N.py` の使い方を説明します。

## 1. 基本動作

`rmc_vasp_script.py` は RMC と VASP を交互に実行します。

概念的には、

```text
RMC
 |
 v
DFT(VASP)
 |
 v
RMC
 |
 v
DFT(VASP)
 |
 ...
```

です。

RMCで得た構造をVASPへ渡し、VASPで得た構造を次のRMCへ戻します。

## 2. 通し番号

v0.6.13 では RMC と DFT のログ番号は**共通の通し番号**です。

例えば、

```text
log0_rmc
log1_dft
log2_rmc
log3_dft
log4_rmc
log5_dft
```

のように進みます。

RMC用カウンターとDFT用カウンターを別々に持つ方式ではありません。

現在の番号は `next_log_dir_name()` から決定されます。

## 3. 通常開始

通常開始は、

```bash
python rmc_vasp_script.py
```

です。

通常開始では、

```text
POSCAR0
   |
   +--> POSCAR
           |
           +--> initial CFG
```

を作成してRMCから開始します。

## 4. restart

restart は、

```bash
python rmc_vasp_script.py restart
```

です。

既存の `logN_rmc` / `logN_dft` を調べ、次に実行すべき通し番号とRMC/VASPのどちらから再開するかを決定します。

restartだから init を無効にする、という特別な扱いはしません。

通常実行と同じ init 選択規則を使用します。

特に、番号付きVASP initを使っていない通常運用でも、restart後に通常の

```text
rmc_vasp_init.py
```

が適用されます。

## 5. 通常 init

通常の入力条件は、

```text
rmc_init.py
rmc_vasp_init.py
```

に記述します。

RMC run では `rmc_init.py`、VASP run では `rmc_vasp_init.py` が基本となります。

initファイルは各run直前にファイルから読み込まれるため、長時間のRMC-DFT実行中でも編集できます。

例えば実行中に、

```text
rmc_init.py
```

の `sigma` や `maximum move` を変更すると、そのファイルが次に使用されるRMC runで変更後の内容が読み込まれます。

VASP側も同様です。

## 6. 番号付き init

特定の通し番号だけ異なる条件で実行したい場合は、

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

を使用します。

例えば、

```text
rmc_init_4.py
```

が存在すると、通し番号4のRMC runではこのファイルが使用されます。

同様に、

```text
rmc_vasp_init_5.py
```

があれば、通し番号5のVASP runで使用されます。

`N` はRMC番号やDFT番号ではなく、RMC/DFT共通の通し番号です。

## 7. 番号付き init の継続

番号付きinitには、

```python
CONTINUE_NUMBERED_INIT = False
```

があります。

### `False`

```python
CONTINUE_NUMBERED_INIT = False
```

の場合、その番号付きinitは現在runだけで使用します。

次の同種runでは通常initへ戻ります。

例えば、

```text
log4_rmc -> rmc_init_4.py
log5_dft
log6_rmc -> rmc_init.py
```

となります。

### `True`

```python
CONTINUE_NUMBERED_INIT = True
```

の場合、その番号付きinitを次の同種runでも継続して使用します。

例えば、

```text
log4_rmc -> rmc_init_4.py
log5_dft
log6_rmc -> rmc_init_4.py
log7_dft
log8_rmc -> rmc_init_4.py
```

となります。

その後、新しい番号付きinitが現れれば、そちらが使用されます。

## 8. init ファイルは動的に再読込される

`CONTINUE_NUMBERED_INIT=True` で `rmc_init_4.py` を継続している場合も、最初に読み込んだPythonモジュールを固定して使い続けるわけではありません。

各runで、

```python
runpy.run_path(...)
```

によりファイルを再読込します。

したがって、計算実行中に `rmc_init_4.py` を編集すると、次のRMC runでは編集後の内容が使用されます。

これはVASP側も同じです。

## 9. RMC init と VASP init

RMC側では、

```python
rmc_dat.init(...)
```

で `*.dat` の初期入力を確定し、その後 `set_*()` で条件を設定します。

VASP側では、

```python
vasp_incar.init()
```

で `INCAR` の初期入力を確定し、その後 `set_tag()` で条件を設定します。

既存入力がある場合、それを初期状態として使用します。

initは既存入力を理由に無効化されません。

## 10. RMCからVASPへの構造受け渡し

RMC終了後、

```python
shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")
```

によって、RMC側から得たVASP形式の構造を次のVASP計算の `POSCAR` として使用します。

## 11. VASPからRMCへの構造受け渡し

VASPの `postprocess()` により、VASP計算後の構造が次のRMCで使用できる形へ処理されます。

この繰り返しによってRMCとDFTを交互に実行します。

## 12. 使い分け

通常は、

```text
rmc_init.py
rmc_vasp_init.py
```

だけで運用します。

途中の特定runで条件を変更したい場合だけ、

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

を追加します。

一時的な変更なら、

```python
CONTINUE_NUMBERED_INIT = False
```

継続的な変更なら、

```python
CONTINUE_NUMBERED_INIT = True
```

を使用します。

実行ロジックを `rmc_vasp_script.py` に書き込むのではなく、計算条件とその継続指定を init 側へ置くのが v0.6.13 の基本方針です。
