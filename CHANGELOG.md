# CHANGELOG

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

## v0.0.x nakada

- 雛形構造を準備(subprocess & class & method 基本構造)