# VASP 実行チュートリアル

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/tutorials/dft_vasp.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/tutorials/dft_vasp.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.ja.html)

単独実行では `vasp_util install` で `vasp.py` と `vasp_init.py` を配置し、`config.yml` を用意します。統合 runner に渡す場合は初期化ファイルを `rmc_vasp_init.py`、番号付きなら `rmc_vasp_init_N.py` として置きます。

> 対象: **rmc_dft v0.6.13**
>
> `vasp.py` を直接実行して VASP を単独で動かす場合と、`vasp_init.py` の使い方を説明します。

## 1. 概要

`vasp.py` は、既存の VASP 入力を利用して VASP を実行するスクリプトです。

VASP の入力条件は `vasp_init.py` に記述します。

```text
config.yml
    |
vasp_init.py
    |
    +--> KPOINTS
    +--> POTCAR
    +--> VaspIncar.init()
    +--> INCAR のタグ設定
    |
vasp.py
    |
    +--> run_vasp()
            |
            +--> VASP 実行
            +--> postprocess
            +--> logN_dft へ保存
```

## 2. 必要なファイル

典型的には、

```text
config.yml
vasp.py
vasp_init.py
POSCAR
```

を用意します。

`INCAR`、`KPOINTS`、`POTCAR` は既存ファイルを使用することも、init 側から準備することもできます。

## 3. `vasp_init.py`

`vasp.py` を直接起動すると、

```python
run_vasp_init(
    config=config_,
    vasp_incar=vasp_incar_,
    logger=logger_,
)
```

が VASP 実行前に呼ばれます。

### KPOINTS

現行 init では、`KPOINTS` が存在しない場合のみ作成します。

```python
if not os.path.exists("KPOINTS"):
    ...
```

既存 `KPOINTS` があれば、そのまま使用します。

### POTCAR

`POTCAR` も存在しない場合のみ作成します。

元素情報は `config.element_info` を使用します。

### INCAR

INCARについては、

```python
vasp_incar.init()
```

を最初に実行します。

これはRMC側の `rmc_dat.init()` に対応する初期化です。

## 4. `VaspIncar.init()`

v0.6.13 では、VASP側にも正式な初期化処理があります。

基本動作は、

```text
INCARあり
    -> 既存INCARを読み込む
    -> init() 自体では書き換えない

INCARなし
    -> 初期INCARを作成する

すでに初期化済み
    -> init() は再初期化しない
```

です。

その後、

```python
vasp_incar.set_tag("EDIFF", 1e-4)
vasp_incar.set_tag("EDIFFG", 1e-3)
vasp_incar.set_tag("ISMEAR", 0)
vasp_incar.set_tag("SIGMA", 0.1)
vasp_incar.set_tag("NSW", 30)
vasp_incar.set_tag("ISIF", 2)
vasp_incar.set_tag("IBRION", 2)
```

のように、`vasp_init.py` に明示したタグを設定します。

重要なのは、**既存 `INCAR` がある場合でも init を無視しない**ことです。

既存INCARを初期入力として読み込み、その上で `vasp_init.py` の setter を実行します。

## 5. 実行

```bash
python vasp.py
```

で実行します。

実行モードは基本的に `config.yml` の `run_mode` を使用します。

`run_vasp()` 内では、

```python
if run_mode is None:
    run_mode = config.run_mode
```

として VASP を起動します。

## 6. postprocess

VASP終了後、通常は postprocess が実行されます。

```python
vasp.postprocess(
    log_dir=log_dir_vasp,
    cfg_name=config.cfg_name,
)
```

ここで計算結果のバックアップや、次のRMC計算に必要な構造ファイルへの変換・更新が行われます。

## 7. ログディレクトリ

保存先は、

```python
next_log_dir_name("dft")
```

で決定されます。

例えば、

```text
log0_dft
log1_dft
log2_dft
...
```

という名前になります。

RMC-DFTとして使用するとき、数字部分はRMCとDFTで共有する通し番号です。

## 8. `CONTINUE_NUMBERED_INIT`

`vasp_init.py` には、

```python
CONTINUE_NUMBERED_INIT = False
```

があります。

単独で `vasp.py` を実行する場合には通常使用しません。

`rmc_vasp_script.py` / `rmc_vasp_script_sequence.py` から、

```text
rmc_vasp_init_N.py
```

として使用するときに、番号付きinitを次のVASP runでも継続するかを指定します。

## 9. 基本的な編集方針

VASP条件を変更する場合は、原則として `vasp.py` 本体ではなく `vasp_init.py` を編集します。

例えば、

```text
EDIFF
EDIFFG
ISTART
ISMEAR
SIGMA
NELM
NSW
ISIF
IBRION
LREAL
ISPIN
ALGO
KPAR
NCORE
NSIM
```

などです。

`vasp.py` は実行処理、`vasp_init.py` は入力条件、という役割分担にします。
