# rmc_vasp
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.ja.md)

"rmc_vasp" は第一原理分子動力学/構造最適化と逆モンテカルロ法(RMC)交互実行をサポートするソフトです。
Structure Analysis Environment package ( 
https://github.com/shimane-dev/sae.git )をベースにしています。


## 目次

[準備](#準備)

[インストール](#インストール)

[実行](#実行)

[アウトプット](#アウトプット)

## 準備
### VASP
VASPをインストールします。
(https://www.vasp.at/)。
動作確認済バージョン: 6.4.2, 5.3.5。

#### インプットファイル
VASPのインプットファイルを準備します。

### RMC
RMC POTをインストールします。
(https://www.szfki.hu/~nphys/rmc++/opening.html)。
動作確認済バージョン: 2023.1。

#### インプットファイル
RMC POT のインプットファイルを準備します。特に、実験による測定データが重要です。
(X線回折, 中性子回折 などなど )

### 初期構造
密度, 原子数 (セルサイズ)。
(例えば、Packmolを使って、初期構造を生成します。(https://m3g.github.io/packmol/)。ランダム構造は2Å程度の原子間距離にするとエラーが出にくいです。)


## インストール

"rmc_vasp"をダウンロードします。 https://github.com/shimane-dev/rmc_vasp/
"x_logger"もダウンロードします。 https://github.com/shimane-dev/x_logger
pipでインストールします:
````
$ pip install x_logger
$ pip install rmc_vasp
````

<details>

<summary> インストールなしで使うとき </summary>

"rmc_vasp"をダウンロードします。 https://github.com/shimane-dev/rmc_vasp/

"x_logger"もダウンロードします。 https://github.com/shimane-dev/x_logger

 "x_logger/" を "rmc_vasp/src/rmc_vasp/"　の下に置きます。

</details>

## 実行
インプットファイルをファルダー（work??）に配置し、そこで？pythonを開きます。
````
$ python3
````
次に、
````
>>> import rmc_vasp
````
と打ちます。そして、
````
>>> run()
````
で、実行します。（）

### 現状(2025年8月中旬)
"rmc_vasp/src/rmc_vasp/"　に各種インプットファイルを置き、
````
$ python ./main.py
````
で、実行しています。

### アウトプット
log0, log1, log2, ... というフォルダ内にアウトプットファイルが保存されます。
通常のvasp, rmcpotのアウトプットファイルの他、
aaa.chi (RMCのχ値、S(Q)のずれなど。RMCのインプットデータによっていろいろありますが。)、
grep_E0_OSZICAR.txt（エネルギー）
を出力します。


Link to the sample section: [Link Text](#sample-section)