# CHANGELOG

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
    - log 関係を独立クラス化(のちにファイル出力ではなくてクラス中でハンドリング)

## v0.1.x kabayashi

- RMC/VASP の method を若干追加
- input_sample の追加・テスト
- RMC-VASP の基本動作・テスト

## v0.0.x nakada

- 雛形構造を準備(subprocess & class & method 基本構造)