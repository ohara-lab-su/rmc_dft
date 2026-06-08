# CHANGELOG

## v0.4.20 nakada

sample の rmc.py が rmc_ini.py を呼び出してなかった(コメントアウトしていた)
ので、それ自体は rmc.py の趣旨からして間違っていないのだが、RMC のテスト用としては
不便極まりないので。rmc.py から rmc_init.py を呼び出す（コメントアウトを外す）

## v0.4.19 nakada

- packmol 関係を強化して、独立パッケージ化(packmol_util)したので、
rmc-dft 関係のツリーから削除
- packmol 関係の example を packmol_util の example に置き換え
  - make_amorphous.py 削除
    - make_FeSiB.py 追加
    - make_Li3PO4.py 追加
 
## v0.4.18 nakada

富岳向けの VASP/RMC_POT デフォルト設定をサンプルに追加

## v0.4.17 nakada

config と init スクリプトでの二重定義が混在していたため、
RMC-DFT 実行時の設定値の流れを整理した。

### 主な整理方針

- `aaa.dat` にある値
- `config.yml` にある値
- `init` スクリプトで `set_*()` する値

の優先順位を整理し、
RMC 側では

- `aaa.dat` / 初期テンプレート値
- `config.yml`
- `init` スクリプトの `set_*()`

の順で上書きされることを前提に見直した。

### RMC 側

- `RmcPotDat` の `set_*()` を通して設定した値が、
  `.dat` の current state だけでなく `Config` 側にも反映されるよう整理した
- 実験データファイル名 (`exp_filename`) について、
  `get_exp_filename()` が current state を優先し、
  必要時のみ `config.yml` 側の既定値へ落ちるように整理した
- `RMC` 実行前の存在確認は、
  `RmcPotDat` インスタンス上の current state を参照する流れを前提に確認した

### VASP 側

- `VaspIncar` / `VaspKpoints` を shared `config` で扱う前提を整理した
- `run_vasp_init()` / `run_vasp()` 側でも、
  helper インスタンスを経由した設定共有が崩れないよう見直した
- `Vasp.run()` の設定値解決では、
  script 側で明示した値を `config` より優先する形に整理した

### 補足

- `restart` はログ番号を引き継ぐだけでなく、
  既存の `logNN_rmc` / `logNN_dft` を見て
  `RMC` と `VASP` のどちらから再開するかを判定する用途として残す
- 通常起動時は初期化から開始するが、
  ログディレクトリ名は既存最大番号の次を採用する
 
## v0.4.16 nakada

v0.4.15 で進めた config 周りの整理の続きとして、
VASP 実行系の細かい不整合を修正した。

- VASP 実行まわりで残っていた typo を修正
- `dft_bin` 未設定時や PATH 上に存在しない場合のエラーハンドリングを改善
- `Vasp.run()` の実行コマンド組み立てとログ出力を整理
- `vasp_kpoints.py` の未使用処理を整理
- `xdatcar2poscar.py` の変数名不整合を修正

バージョンを `0.4.16` に更新

## v0.4.15 nakada

config 周りの整理を進めた。

これまで、script 側で `set_*()` して変更した値と、他クラスが `config` を見たときの値がずれる箇所があり、
RMC/DFT の loop をまたいだときや、別クラスから設定値を参照したときに整合が崩れやすかった。

今回の方針は、

- 明示的に `set_*()` した値を最優先とする
- その値を `Config` インスタンスにも反映する
- 明示 set が無いときだけ `Config` の既定値を使う
- どちらにも無いときは未設定として扱う

という形に寄せること。

### RMC 側

- `RmcPotDat` の主要な `set_*()` メソッドで、`.dat` の行更新だけでなく `Config` 側の mirror 値も更新するようにした
  - comment
  - density
  - cutoffs
  - maximum moves
  - r spacing
  - moveout option
  - time and save
  - data flags
  - exp filename
  - exp range
  - sigma factor
  - number of atoms per move

- `xsq` ファイル名取得 (`get_exp_filename`) の挙動を整理した
  - まず `.dat` 11 行目の現在値を使う
  - `.dat` 側に値が無いときだけ `config.rmc_exp_filename` を使う
  - 両方無いときは未設定エラーにする

これにより、`run_rmc_init()` などで `set_exp_filename()` した値が、
そのまま `RmcPot.preprocess()` の存在チェックでも使われる形に整理された。

### VASP 側

- `VaspIncar` / `VaspKpoints` に `config` を共有できるようにした
- script 側で `set_tag()` や `set_mode()/set_grid()/set_shift()` した値を、
  helper クラス内部だけでなく `Config` 側にも反映するようにした
- `Vasp` 生成時に、内部で作る `VaspIncar` / `VaspKpoints` へ同じ `Config` を渡すようにした
- `set_mpi()` / `set_job_cmd()` で変更した値も `Config` に反映するようにした

### RMC-DFT 全体

- `RmcDft.set_cfg_name()` と `RmcDft.set_max_rmc_dft_loop()` で、
  内部値だけでなく `Config` にも反映するようにした
- `example/rmc_vasp_script.py` でも、
  `VaspIncar` / `VaspKpoints` を `config` 共有で生成するようにした

### まだ残る注意

- `Config` は依然として「ユーザー向け mirror」と「クラス横断の共有データコンテナ」の両方を兼ねている
- そのため、今後も新しく `set_*()` を増やす場合は、
  「内部状態だけでなく `Config` も更新する」ことを原則にした方がよい
- getter 側についても、`.dat` / `INCAR` / `KPOINTS` の現在値を優先し、
  無いときだけ `Config` 既定値へ落とす、という方針で今後そろえていく必要がある
 
## v0.4.14 nakada

タグ/ブランチ忘れなので、下記の内容は v0.4.15 に繰り越す

- RMC-DFT(rmc/vasp/rmc-dft)の基本RUNを富岳で実現するための修正諸々
- 今までの問題
  - config で設定するべき parameter
  - script で編集するべき parameter
- がちょっとカオスっている（経験で調整した絶妙なバランスで動いている）
  状態なのを改めて問題(v0.4.15 似て解決？) 

## v0.4.13 nakada

### 変更内容

- RMC 実行と VASP 実行で、OpenMP のスレッド数を別々に設定できるようにした。
- `rmc_omp_num_threads` は `rmc_pot` 実行時の `OMP_NUM_THREADS` にのみ反映される。
- `dft_omp_num_threads` は VASP 実行時の `OMP_NUM_THREADS` にのみ反映される。
- これにより、RMC 側で指定した OpenMP スレッド数に VASP 側が縛られないようにした。

### 修正

- `rmc_pot` の非同期実行経路でも、設定した環境変数を子プロセスへ渡すように修正した。
- `example/config.yml` における OpenMP 設定の記述を、正しい YAML 形式に修正した。

### 設定方法

設定例:

```yaml
mpi_cmd: "mpiexec"
mpi_flag: null

rmc_omp_num_threads: 8
dft_omp_num_threads: 1
```

## v0.4.12 nakada

これまでの example script では、RMC 側・DFT 側ともに、
入力ファイルの設定更新と実行処理が同じ関数の中にまとめていました。
そのため、RMC-DFT の各 loop ごとにパラメータを変更したい場合、
run_rmc / run_vasp の内部処理を直接編集する必要があり、
独自の RMC-DFT スクリプトを作るには少し扱いにくい構成になっていました。

今回の変更では、RMC 側を

  run_rmc_init()
  run_rmc()

に分離し、DFT 側も

  run_vasp_init()
  run_vasp()

として、直接rmc_vasp_script から呼び出す形にしました。

これにより、rmc_vasp_script.py 側から見ると、

  RMC 入力設定
  RMC 実行
  DFT 入力設定
  DFT 実行

という流れが明確になったと思います。

具体的には、RMC 側では run_rmc_init() で RmcPotDat の set_* 系メソッドを呼び、
dat ファイルの内容を更新してから、run_rmc() で RMC_POT を実行する。
DFT 側では run_vasp_init() で INCAR などの入力条件を更新し、
その後 run_vasp() で VASP を実行する。

この構造により、各 loop ごとに RMC や DFT
のパラメータをスクリプト側で明示的に変更しやすくなったと思います。
スクリプト中で自動でパラメーターを変更など。
たとえば、最初の数 loop だけ RMC の条件を変える、
途中から VASP の収束条件を変更する、
といった処理を、run_rmc_init() / run_vasp_init() の中で比較的直接的に書けるようになりました。

構造的にはもともとそのような利用を意図していたのですが、
使いやすいようにどんどんとサブ関数におしこんでしまって、結果的に使いにくくなっていました。

今回の変更により、example script は一見すると少し長くなりましたが、
RMC 入力設定、RMC 実行、DFT 入力設定、DFT 実行の責務がトップのループ制御の段階で分かれたため、
独自の RMC-DFT 計算スクリプトを作りやすくなったとは思います。
むしろ初期バージョンのRMC-DFT側のインスタンス呼び出し構成に戻した形になります。

## v0.4.11 nakada

リスタート形におけるログ番号の自動化のルールに合わせて、
通常モードのログ番号も合わせる（完全に連番というシンプルか形にする)

RMC が収束自動判定（まだ動作が不安定）をもし使ったときに、

(1) NEW-style
```aiignore
log1_rmc
log2_rmc
..
log10_dft
log11_rmc
...
```
などとなる。rmc<-->dft が完全に一対一対応でなくなるために
、従来の

(2) OLD-style
```aiignore
log1_rmc
log1_dft
log2_rmc
log2_dft
...
```
というように、rmc-dft のペアを1loopとする数え方を通常モードにおいてもやめる

再起動モードのときは、最初から NEW-style である。
これは、もし
```aiignore

...
log10_dft
```
で計算が終わっているフォルが構造があったとする。
このとき ```rmc_vasp_script.py restart ``` として、restart オプションで動かすと

```aiignore
...
log10_dft
log11_rmc
log12_dft
```
となる。これは、rmcで終わっていても同じであり。
```aiignore
log11_rmc
...
log12_dft
log12_rmc
```
log11_rmc でフォルがある時に、rmc_vasp_script.py を動かすと。log12_dft を始める。
(これらのフォルダは結果保存フォルダである）

これらの機能により、非常に気楽に途中の計算をリカバリーできる。
計算再開の保証性は、それぞれの計算結果しあいなので、スクリプトでチェックをしない。
以前のバージョンでは無駄にスクリプト側で計算終了をチェックをしていたために、
非常に条件分岐が複雑で、気楽にrestartするのが怖かったが。シンプル化したので
しれはなくなった。

## v0.4.10 nakada

主にリスタート機能のバグ修正

## v0.4.9 nakada

example の rmc.py のバグ修正

## v0.4.8 nakada

- bugfix: 使い方によっては巡回importするのを改善


## v0.4.7 nakada

- 旧版で実装していた restart 系を新盤 0.4.x 系で復帰
- rmc_vasp を読んでいるときは run_dft 系をやめて、run_vasp に統一し直す

## v0.4.6 nakada

- RMCの自動収束が少しイマイチなので手動をデフォルトに変更
- スクリプトサンプルを少し修正

## v0.4.5 nakada

- RMC の自動収束に関して機能追加
  - それに伴い、rmc_vasp_script/rmc_vasp/rmc の sample ファイル関係を調整
  - **短い時間でRMCを回すと hst における step 数が少ないために、自動判定でエンドレス化するので注意**

## v0.4.4 nakada

- density 関係のメソッドの名前変更と単独で実行可能な main-python化

## v0.4.3 nakada

- cfg2poscar 自身を 引数 element_info として、
  1. リスト(str) をファイルとして読み込み、そこ書かれている Fe,Si,B という内容を、"Fe,Si,B" として扱う
  2. リスト(str) をファイルとして読むのに失敗したら、そのストリングを、"Fe,Si,B"
  3. ["Fe","Si","B"] のようなリストとして受ける

機能を追加した

## v0.4.2 nakada

- bugfix
 
## v0.4.1 nakada

- Log 解析で hst と同等のことができるように修正(むしろこちらの方が生情報)
- Hst/Log の解析でできるだけ同じメソッドに(total/global で概念が異なっている可能性がある) 
- Hst 解析を追加(全ての不情報を取り出せる形い)

## v0.4.0 nakada

- RMC-DFT を途中で止めた時の再開処理について検討・実装

方針:
  - 現在の作用ディレクトリ(カレントを想定)において
    RMCの途中で終わったか？DFTの途中で終わったかの判定をする
    - 終了判定メソッドを追加する(収束ではなくてプログラムが正常終了したか？の判定)
  - スクリプト側で終了判定がない方をみつけて、その計算を再スタートさせる
  - RMC_POT はいわゆる判定に使えるログが標準出力垂れ流しなので
    それを保存できるように修正

- RMC_POT.py
  - subprocess での実行を blocking/non-blockng 切り替えられるようにした
  - subprocess での実行で標準出力をファイルに記録できるようにした
    - log ファイルを解析して整理できるようにした
      - rmc_pot_log.py クラスの拡張
    - log ファイルを RMC_POT の標準出力として取るが、
      ジョブファイルのログとして取得した場合でも判断できるように、RMC_POTのstart/end
      をログファイル挙動から見て取得できるように変更

## v0.3.25 nakada

- bugfix
  - 主にplot系
 
## v0.3.24 nakada

- データー欠損がある場合のプロット(計算途中でのプロット)
  - plot_multi_converge
  - plot_multi_fit

(*) まだ単独版だと、バグが残っているかもしれない

## v0.3.23 nakada

- セルサイズの便利？ツール追加
 
## v0.3.22 nakada

- bugfix
 
## v0.3.21 nakada

- プログラムが途中の時に multi plot で止まる問題
- VaspOutcar に終了は判定メソッドを加える
- VaspIncar での INCAR 比較メソッドを追加
  - RMC_DFT が DFT と RMC それぞれに便利ツールを集約する

## v0.3.20 nakada

- config に項目をいくつか追加
- スクリプト側の変数のいくつかを config に押し込み(make_amarphous.py)

## v0.3.19 nakada

- packmol_inp.py (Packmol Inp 作成支援クラス)
- 原子間距離の下位を表示スクリプト
- packmol 20.15.0 からの周期境界オプション(PBC)のための修正
  - テスト

## v0.3.18 nakada

- 0.3.17 の　bugfix
- vasp.run() のエラーハンドリングを修正
- poscar 関係を、x_poscar リポジトリから移行
- plot_distance_histgram.py
  - (原子間距離でのヒストグラム作成)
  - packmol での初期構造作成のときの検証用

## v0.3.17 nakada

label 更新

- bugfix
- label.txt の代わり ["Fe", "Si", "B"] などを与えても機能するように
- label.txt ファイルの自動チェックを停止(代わりに引数チェックを加える)
 
Packmol 利用の簡便化のための python パッケージ(nakada)

- make_amorphous 関係の一般化
  - pkmol クラスに機能の大半を押し込む

docs

- エラーをだいぶ潰した
 
## v0.3.16 nakada

注意)

- None のときのデフォルト分岐をシンプルにした（バグが起きる可能性がないわけじゃない）

主な改変

- config.yml / config.py のデフォルト設定に s(q) ファイル名を入れる
- rmc_vasp_script スクリプトのバグ修正 rmc (preprosess)
- rmc_vasp_script スクリプトのRMC関係のファイルチェック

クラス

- dft_dft 関連 rmc_vasp.run() での例外処理を方針転換(例外を出してもそのまま RMC に流す)
 
## v0.3.15 nakada

- example (bugfix)
 
## v0.3.14 nakada

- docstring 修正(sphihxでのエラー対策)
  - 修正し切れてない・軽減

アモルファス作成

- make_amarphous.py
- rmc_dft/packmol.py
 
## v0.3.13 nakada

DFT 関係のプロットのためのクラス

- VaspOutcar.py 作成
- plot_energy.py
- plot_multi_energy.py
- plot_mulit_converge.py

## v0.3.12 nakada

RMC

- multi_plot
- bugfix
 
## v0.3.11 nakada

プロット/解析 関係の基本クラス

- rmc_pot_fit.py
- rmc_pot_hst.py
- rmc_pot_ppcf.py

プロットプログラム例

- plot_fit.py
- plot_hst.py
- plot_ppcf.py


## v0.3.10 nakada

- VaspPoscarBuilder()
- VaspIncar()
- VaspKpoints()

を見直し、実行の example スクリプトを個別に用意

- data_edit_dat.py (RMC_POT)
- data_edit_incar.py (RMC_POT)
- data_edit_kpoints.py (RMC_POT)
- data_edit_potcar.py (RMC_POT)

計算の example スクリプト rmc_vasp.py にこれらを組み込む

- rmc_vasp.py

RMC-DFT の example スクリプト rmc_vasp_script.py に組み込み

- rmc_vasp_script.py

「作る・動かす系」の python 化は、RMC/DFT でできているかな。
とは思うが、ここまで書いて、VASP 周りはもっと pymatgen/ase 活用した方が良かった。
と後悔。途中で本心を変えたので、クラスが大きくなってしまった。

## v0.3.9 nakada,kobayashi

- mpi job 関係の動作モード実装・確認
  - run_vasp.py などを丸ごと job スクリプトに書いて
  - config で mpi オプション、cpu 数などの null にして
    - mpirun vasp_std
  - などを動かすような形でにして、job スクリプト自体を長い RMC-DFT
  - として動作させる
- docs の充実(RMCチュートリアル), 主に小林
- DFT 関係のdocsの作成予定のスケルトン作成
 
## v0.3.8 nakada

- bugfix
 
## v0.3.7 nakada

- bugfix
 
## v0.3.6 nakada

- setup.py の python 3.6(hpcs) とそれ以外を pythonバージョンで切り替えられるようにした
 
## v0.3.5 nakada

- 名前変更
  - vasp_bin --> dft_bin

## v0.3.4 nakada

- python 3.6/hpcs(idss) でテスト/調整
  - VASP/RMC 個別試験は概ね終わり
  - DFT_RMC クラスでのテスト開始

## v0.3.3 nakada

- python 3.6 互換
    - いくつか 3.6 未対応だったのを修正
- VASP / RMC 実行前の必要ファイルチェックなどを導入
- Vasp/RmcPot などの各主要クラスにおいて VaspLog() や RmcPotLog() などの
  ログ結果を取得すクラスを委譲しなくても、None のときはコンストラクにて生成する
  仕様に変更（仕様を追加)。従来型もOK

## v0.3.2 nakada

- python 3.6 互換
  - いくつか 3.6 未対応だったのを修正

## v0.3.1 nakada

- python3.6 + 非ネットワーク環境対応 (尾原研 hpcs 環境対応)
  - setup.py を追加 (tomlと共存)
  - python 3.10 以上の構文( config: str | None = None) のようなものを廃止
    - python 3.6 でも動作するように config: Optional[str] = None などとする
    - dataclass を 内部モジュールから外部モジュール(pip instal dataclasses) 3.6対応のため
    - アノテーション記法を後方互換性が高いものに変更 list[str] --> List[str]
- config.py を修正(config.yaml 導入) 
- config.py を instance 形にする
  - 直接 cfg_name などを引かなくても、config を引けば、cinfig 情報をクラスやメソッドで参照できるように統合
  - config.yml による編集部分
 
## v0.3.0 nakada

- INPUT 関係を クラスライブラリ上から行う・管理できる仕様に改変
  - vasp_incar.py
  - vasp_potcar.py
  - vasp_kpoints.py
  - rmc_pot_dat.py

## v0.2.3 nakada

- v0.2.2 相当の機能を再構成
  - RMC/VASP の処理単位の再構築
    - method 整理
- それぞれの機能の最低限試験
- RMC/VASP の個別の class を連携したテスト
- RMC-DFT からの RMC/VASP 呼び出しテスト

## v0.2.2 nakada

- dft_rmc により、vasp, rmc_pot などのクラスを読んで使うように一般化した
  - example (モジュールを読んで実際に rmc_dft を動かすprogram) と module を分離を明確に
- bugfix
- さまざまな調整
- rm_vasp から rmd_dft の改変での(主にリポジトリ関係)のゴタゴタ解消
 
## v0.2.1 nakada

- bugfix & test

## v0.2.0, nakada

- rmc_vasp 大整理
  - クラスと関数構造を全面的に変更
    - 個別メソッドのクラス化
    - util のみメソッドのまま
    - log 関係を独立クラス化(のちにファイル出力ではなくてクラス中でハンドリング)

## v0.1.x kabayashi

- RMC/VASP の method を若干追加
- input_sample の追加・テスト
- RMC-VASP の基本動作・テスト

## v0.0.x nakada

- 雛形構造を準備(subprocess & class & method 基本構造)