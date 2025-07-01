# rmc_vasp
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.ja.md)

"rmc_vasp" は第一原理分子動力学と逆モンテカルロ法(RMC)を交互にやるのをサポートするソフトです。
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
RMC POT のインプットファイルを準備します。特に、実験による測定データがキーです。
(X線回折, 中性子回折 などなど )

### 初期構造
密度, 原子数 (セルサイズ).


## Install

Just download https://github.com/shimane-dev/rmc_vasp/
Install using pip:
````
$ pip install rmc_vasp
````

## How to run

Put input files in a folder and open python:
````
$ python3
````
then,
````
>>> import rmc_vasp
````
and,
````
>>> run()
````
