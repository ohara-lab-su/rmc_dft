# rmc_vasp
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.ja.md)

"rmc_vasp" は第一原理分子動力学と逆モンテカルロ法(RMC)交互実行をサポートするソフトです。
Structure Analysis Environment package ( 
https://github.com/shimane-dev/sae.git )をベースにしています。


## 準備
### VASP
VASPをインストールします。
(https://www.vasp.at/)
#### インプットファイル
VASPのインプットファイルを準備します。

### RMC
RMC POTをインストールします。
(https://www.szfki.hu/~nphys/rmc++/opening.html)
#### インプットファイル
RMC POT のインプットファイルを準備します。特に、実験による測定データが重要です。
(X線回折, 中性子回折 などなど )

### 初期構造
密度, 原子数 (セルサイズ)。


## インストール

"rmc_vasp"をダウンロードします。 https://github.com/shimane-dev/rmc_vasp/
"x_logger"もダウンロードします。 https://github.com/shimane-dev/x_logger
pipでインストールします:
````
$ pip install x_logger
$ pip install rmc_vasp
````
## インストールなしで使うとき

"rmc_vasp"をダウンロードします。 https://github.com/shimane-dev/rmc_vasp/
"x_logger"もダウンロードします。 https://github.com/shimane-dev/x_logger

 "x_logger/" を "rmc_vasp/src/rmc_vasp/"　の下に置きます。


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
で、実行します。