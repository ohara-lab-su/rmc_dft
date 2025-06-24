# rmc_vasp
第一原理分子動力学と逆モンテカルロ法(RMC)を交互に行うのを支援するpythonモジュール。
構造変換パッケージを基盤にしています。( StructureAnalysisEnvironment: 
https://github.com/shimane-dev/sae.git )


## 準備
### VASP
VASPをインストールします。
(https://www.vasp.at/)
#### 必要ファイル
VASPのインプットファイル

### RMC
RMC POTをインストールします。
(https://www.szfki.hu/~nphys/rmc++/opening.html)
#### 必要ファイル
RMC POTのインプットファイル（実験データ）

### 初期構造


## Install

Just download https://github.com/shimane-dev/rmc_vasp/
Install using pip:
````
pip install rmc_vasp
````

## 実行

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
