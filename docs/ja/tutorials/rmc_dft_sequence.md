# RMC-DFT 手動 sequence 実行チュートリアル

> 対象: **rmc_dft v0.6.13**
>
> `rmc_vasp_script_sequence.py` を使用し、RMC/VASPの実行順序を通し番号単位で明示的に指定する方法を説明します。

## 1. sequence の目的

通常の `rmc_vasp_script.py` は、

```text
RMC -> VASP -> RMC -> VASP -> ...
```

を自動的に繰り返します。

一方、sequenceでは、

```text
RMC
RMC
VASP
RMC
RMC
VASP
```

のように、RMCとVASPの実行順を明示的に指定できます。

例えば、

```text
rmc_init_1.py
rmc_init_2.py
rmc_vasp_init_3.py
rmc_init_4.py
rmc_init_5.py
rmc_vasp_init_6.py
```

という任意の並びを実行できます。

## 2. 使用するファイル

sequence実行では主に、

```text
rmc_vasp_script_sequence.py
rmc_vasp_script_sequence_dat.py
rmc_init_N.py
rmc_vasp_init_N.py
```

を使用します。

通常、実行順序を変更するときに編集するのは、

```text
rmc_vasp_script_sequence_dat.py
```

です。

## 3. `manual_sequence`

実行順序は `manual_sequence` に書きます。

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
    "rmc_init_5.py",
    "rmc_vasp_init_6.py",
]
```

上から順に実行されます。

この例では、

```text
1: RMC
2: RMC
3: VASP
4: RMC
5: RMC
6: VASP
```

となります。

## 4. 通し番号との一致

ファイル名の番号は、実際に次に作成されるログ番号と一致している必要があります。

例えば、

```text
rmc_init_4.py
```

を実行するとき、次のRMCログが

```text
log4_rmc
```

でなければエラーになります。

同様に、

```text
rmc_vasp_init_6.py
```

なら、次のDFTログは

```text
log6_dft
```

である必要があります。

sequence側は `next_log_dir_name()` で実際の次番号を確認し、指定番号と一致しなければ `RuntimeError` で停止します。

## 5. RMCを連続して実行する

通常RMC-DFTではRMCとVASPを交互に実行しますが、sequenceなら、

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_init_3.py",
]
```

のようにRMCを連続して実行できます。

各runで別の `rmc_init_N.py` を使用できるため、

```text
run 1: sigmaを大きくして初期緩和
run 2: maximum moveを小さくする
run 3: sigmaを下げてフィットを厳しくする
```

といった段階的な操作が可能です。

## 6. VASPを任意の位置へ入れる

例えば、

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
]
```

なら、RMCを2回実行した後にVASPを実行し、その後再びRMCを実行します。

VASP条件は `rmc_vasp_init_3.py` に記述します。

## 7. init ファイルは実行直前に読む

sequenceでも init ファイルは、

```python
runpy.run_path(init_file)
```

で実行直前に読み込みます。

したがって、sequence実行中でも、まだ実行されていない

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

を書き換えることができます。

変更後の内容が、そのrunで使用されます。

## 8. `continue_rmc_dft`

`rmc_vasp_script_sequence_dat.py` には、

```python
continue_rmc_dft = False
```

があります。

### `False`: sequenceだけ実行

```python
continue_rmc_dft = False
```

の場合、

```text
manual_sequence
    |
    +--> 全項目を実行
    |
    +--> 終了
```

です。

通常の `rmc_vasp_script.py` の補完として、指定した処理だけを実行したい場合に使用します。

### `True`: sequence後に通常RMC-DFTへ移行

```python
continue_rmc_dft = True
```

の場合、

```text
manual_sequence
    |
    +--> 全項目を実行
    |
    +--> 通常の RMC-DFT loop
```

へ移ります。

sequence終了後はRMCから通常ループを再開します。

## 9. `CONTINUE_NUMBERED_INIT` と sequence

v0.6.13 では、manual sequenceから通常RMC-DFTへ移る場合も `CONTINUE_NUMBERED_INIT` が追従します。

例えば最後に使用したRMC initが、

```python
# rmc_init_5.py
CONTINUE_NUMBERED_INIT = True
```

なら、`continue_rmc_dft=True` で通常ループへ移った後も、次のRMC runで `rmc_init_5.py` を継続して使用します。

`False` なら通常の、

```text
rmc_init.py
```

へ戻ります。

VASP側も同じです。

```python
# rmc_vasp_init_6.py
CONTINUE_NUMBERED_INIT = True
```

なら、そのVASP initの継続状態が通常ループへ引き継がれます。

## 10. sequence中の動的変更

継続中の番号付きinitも毎runファイルから再読込されます。

したがって、

```python
CONTINUE_NUMBERED_INIT = True
```

として継続中の `rmc_init_5.py` を、計算実行中に編集することもできます。

次にそのinitが使用されるときには変更後の内容が反映されます。

## 11. 典型例: RMCを段階的に収束させてからDFT

```python
continue_rmc_dft = False

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
]
```

例えば、

```text
rmc_init_1.py
    sigma 大
    maximum move 大

rmc_init_2.py
    sigma 小
    maximum move 小

rmc_vasp_init_3.py
    VASP structure relaxation
```

のように条件を分けられます。

## 12. 典型例: sequence後に通常RMC-DFTへ戻す

```python
continue_rmc_dft = True

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
]
```

この場合、

```text
log1_rmc
log2_rmc
log3_dft
```

までを手動sequenceで制御し、その後は通常のRMC-DFTループへ移ります。

最後に使用した番号付きinitの `CONTINUE_NUMBERED_INIT` に応じて、番号付きinitを継続するか通常initへ戻るかが決まります。

## 13. 通常 script との使い分け

`rmc_vasp_script.py` が適するケース:

```text
RMC -> VASP -> RMC -> VASP
```

という通常の反復を行う場合。

`rmc_vasp_script_sequence.py` が適するケース:

```text
RMC -> RMC -> VASP -> RMC -> RMC -> VASP
```

など、実行順序そのものを明示的に制御したい場合。

sequenceは通常scriptを置き換えるだけでなく、`continue_rmc_dft=False` によって通常scriptを補完するための部分実行にも使用できます。
