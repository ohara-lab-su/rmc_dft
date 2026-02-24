# CHANGELOG

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