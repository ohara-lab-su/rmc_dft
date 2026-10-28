# RMC 実行チュートリアル

> 対象: **rmc_dft v0.6.13**
>
> `rmc.py` を直接実行して、RMC_POT を単独で動かす場合の基本的な使い方を説明します。

## 1. 概要

`rmc.py` は、現在の `*.cfg` 構造に対して RMC_POT を実行するためのスクリプトです。

RMC の入力パラメーターは `rmc_init.py` に記述します。

基本的な流れは次の通りです。

```text
config.yml
    |
    +--> RmcPotDat
    |
rmc_init.py
    |
    +--> run_rmc_init()
            |
            +--> *.dat の初期化
            +--> RMC パラメーター設定
    |
rmc.py
    |
    +--> run_rmc()
            |
            +--> RMC_POT 実行
            +--> logN_rmc へ保存
```

## 2. 必要なファイル

最低限、計算ディレクトリに以下を用意します。

```text
config.yml
rmc.py
rmc_init.py
aaa.cfg
```

`aaa` の部分は `config.yml` の `cfg_name` に依存します。

RMC_POT の実行ファイルや実験データなど、`config.yml` および `*.dat` から参照されるファイルも必要です。

## 3. `rmc_init.py`

`rmc.py` を直接起動した場合、実行前に

```python
run_rmc_init(
    config=config_,
    rmc_dat=rmc_dat_,
    logger=logger_,
)
```

が呼ばれます。

RMC のパラメーター変更は `rmc.py` ではなく、基本的に `rmc_init.py` に記述します。

例えば、

```python
rmc_dat.set_density(0.0570880440)

rmc_dat.set_maximum_moves(
    [
        0.01,
        0.01,
        0.01,
        0.01,
    ]
)

rmc_dat.set_sigma_factor(0.05)
rmc_dat.set_moveout_option(True)
rmc_dat.set_time_and_save(15, 1)
```

のように setter を使用します。

COORD、SNC/Qn、角度拘束などの free-format 設定も `rmc_init.py` で行います。

## 4. `rmc_dat.init()`

`run_rmc_init()` の最初では `RmcPotDat.init()` を実行します。

v0.6.13 の基本的な考え方は、

- 既存の `*.dat` がある場合は、それを初期入力として使用する。
- `*.dat` がない場合は初期入力を作成する。
- 一度初期化された `RmcPotDat` に対して再び `init()` を呼んでも、初期化を繰り返さない。
- 実際のパラメーター変更は、その後の `set_*()` が担当する。

というものです。

したがって、`init()` と setter は別の役割を持ちます。

## 5. 実行

```bash
python rmc.py
```

を実行します。

`rmc.py` は `rmc_init.py` を適用した後、RMC_POT を実行します。

## 6. ログディレクトリ

RMC の保存先は `next_log_dir_name("rmc")` によって決定されます。

例えば、

```text
log0_rmc
log1_rmc
log2_rmc
...
```

のように保存されます。

RMC と DFT を組み合わせた場合も、番号はRMC専用番号・DFT専用番号ではなく、RMC/DFTで共有する**通し番号**として扱います。

## 7. Ctrl+C

v0.6.13 の `rmc.py` / `run_rmc()` では、RMC_POT 実行部分を `try/finally` で処理しています。

そのため、RMC_POT を `Ctrl+C` で停止した場合でも、途中まで生成された `*.cfg` などに対して postprocess が実行され、ログディレクトリへの退避処理が行われます。

## 8. `CONTINUE_NUMBERED_INIT`

`rmc_init.py` には、

```python
CONTINUE_NUMBERED_INIT = False
```

があります。

これは `rmc_init.py` を単独RMC用として使用するときには実質的に使用しません。

この設定が意味を持つのは、`rmc_vasp_script.py` または `rmc_vasp_script_sequence.py` から、

```text
rmc_init_N.py
```

として使用するときです。

詳細は `rmc_dft.md` および `rmc_dft_sequence.md` を参照してください。

## 9. 典型的な編集箇所

通常、RMC条件を変更するときは `rmc.py` 本体ではなく `rmc_init.py` を編集します。

代表的な設定は、

```text
density
cutoff
maximum move
sigma
moveout
RMC time / save interval
experimental range
r spacing
experimental data
FNC / topology
COORD
SNC / Qn
angle constraint
```

です。

実行制御と入力パラメーター設定を分離し、計算条件は init 側に置くのが基本です。
