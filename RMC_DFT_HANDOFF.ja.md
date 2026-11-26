# rmc_dft 開発引継書

## 調査対象とリリースの境界

- 作業ブランチは `develop_nakada`、調査開始時の HEAD は `4180f25`。ソース、サンプル、日英 README・変更履歴、Pages の入口と全チュートリアル、配布・Pages ワークフローを確認した。
- 比較元はローカルの `v0.7.10`、`v0.7.12`（`35f0acb`）、`v0.7.13`（`70e0dc8`）および現行作業ツリー。タグ v0.7.13 と調査開始時の `4180f25` のツリー差は `.gitignore`。v0.7.11 を名乗る変更は履歴内で取り消されている。
- PyPI、GitHub Releases、ローカルタグで確認した最新リリースは v0.7.13。次の未公開版を v0.7.14 とし、単独 RMC 描画4本の削除とインストーラ・文書の更新を同版に記載した。
- 関連資料は提供された `../rmc_util.zip`（ソースの宣言 v0.1.12）と `../vasp_util.zip`（v0.0.9）。ZIP 内のソース、配布設定、説明資料を照合した。例やアーカイブに残る履歴上の名前は、現行環境の公開 API と照合する。

## パッケージの境界と呼び出し経路

| パッケージ | 主な責務・入口 |
| --- | --- |
| `rmc_util` | RMC_POT の DAT fixed/free、SNC・FNC・TOP、CFG 変換、RMC 実行、ログ・HST・FIT・PPCF。単独実行は配布される `rmc.py`、`rmc_init.py`、`config.yml` から `rmc_util.runners.run_rmc` を呼ぶ。 |
| `vasp_util` | INCAR・KPOINTS・POTCAR、VASP 実行とバックアップ、OUTCAR、POSCAR・軌跡・周期セル解析。単独実行は `vasp.py`、`vasp_init.py` と作業ディレクトリの `config.yml` を用い、`vasp_util.runners.run_vasp` を呼ぶ。ZIP の配布設定では `config.yml` はコピー対象外。 |
| `rmc_dft` | 統合 `Config`、通常 runner と手動 sequence、計算間の構造受け渡しと restart、統合解析例。Packmol の例は `packmol_util` に委譲する。 |

通常 runner は `src/rmc_dft/runners/rmc_vasp_script.py`。通常開始時に `POSCAR0` → `POSCAR` → CFG と変換し、`run_rmc` の後処理が作る `<cfg_name>.vasp` を次の VASP の `POSCAR` にコピーする。`run_vasp` の後処理では CONTCAR から次の CFG を作る。標準 init と番号付き init は `runpy.run_path()` で読み直す。`rmc_vasp_script_sequence.py` は `rmc_vasp_script_sequence_dat.py` の `manual_sequence` を同様に読み、各 init の番号を次のログ番号と照合する。`continue_rmc_dft` が真なら標準ループへ進む。

`RmcDft` は別の交互実行 API で、設定されたプレフィックスでログ名を組み立て、`RmcPot` と `Vasp` のクラスを直接呼ぶ。通常・手動 runner は `logNN_rmc` と `logNN_dft` の通し番号を使う。統合 runner の restart は `util/check_restart_rmc_vasp.py` が最新名から段階を選ぶ。実ファイルの終了判定は別の `check_rmc_and_vasp.py` にあり、旧候補の `check_restart_rmc_vasp_.py` も残る。

## 分離が残している具体的な課題

1. **互換 import と配布サンプル**。直下の `rmc_dft`、`rmc_dft.rmc_pot`、`rmc_dft.vasp` には再公開がある。`rmc_dft.rmc_pot.rmc_pot_hst` 等の実モジュールは消えており、`scripts/check/check_rmc_chi.py`、`check_rmc_finalized.py`、`scripts/analyze/analyze_sio2_qn.py`、`analyze_zeolite.py`、`example/fnc/convert_gromacs_top_to_rmc_top.py` に旧パスが残る。相当する `rmc_util` API を確認して更新する。`analyze_sio2_qn.py`、`make/make_analyze_qn.py`、`make/make_qn_fnc_top.py`、`example/fnc/SiO2_O4` には `qn.qn_*` の参照もある。旧 `example/fnc/SiO2_03/qn_network.py` と現行の制約 API の役割を比較してから、供給元を決める。
2. **重複実装と設定**。`rmc_dft.rmc_pot_dat_top` と `rmc_util.rmc_pot_dat_top` は別ファイルで、差分がある。提供 ZIP の `poscar2cfg.py` は `rmc_util.util` と `vasp_util.util` に同じ内容があり、統合 runner は前者、`rmc_dft.util` の再公開は後者を使う。統合用・RMC 単独用・VASP 単独用の各 `Config`、各パッケージのログ採番も別実装。整理の際は公開 import、CFG/POSCAR の座標・原子順、更新タイミング、ログの 0 始まり・ゼロ埋め・通し番号を比較する。
3. **統合雛形と計算検証**。`scripts/run/` は `config.yml`、手動順序と変換・構造作成例を配布する。統合の `rmc_init.py` と `rmc_vasp_init.py` は利用者側で準備する。PBS 例は旧ローカル起動ファイルを参照する。runner に渡す統合設定、初期化、restart、sequence から標準ループへの復帰、途中停止とログ採番を実データで確認する作業が残る。
4. **依存関係と Pages**。ZIP の `vasp_util.vasp` は import 時に ASE を必要とする。依存パッケージの配布設定に ASE がなかったため、統合パッケージの依存に追加した。所有元の `vasp_util` 側への反映は別途扱う。Pages の CI は Sphinx 周辺だけをインストールするので、英日 HTML が生成されることと autodoc に API 本文が掲載されることを分けて確認する。ローカルで依存関係を使ったビルドでも、既存 docstring の書式と重複 API の診断が出る。
5. **作図スクリプトの移行**。v0.7.14 の配布対象から外れた `plot_fit.py`、`plot_hst.py`、`plot_ppcf.py`、`plot_ppcf2.py` は ZIP の `rmc_util` v0.1.12 が配布する。複数 run 比較・統合収束の作図は `rmc_dft` が配布する。ZIP v0.1.12 の一覧コマンドは `rmc_util list`、`vasp_util` v0.0.9 は `install` で一括配置。今回の `rmc_dft install list` を確認する際に、二つの関連パッケージのコマンド名まで同じと仮定しない。

## 今回の確認

- Python 3.12 で sdist から wheel をビルドし、テンポラリ環境へ導入。配布物の40ファイルを作業ツリーと照合した。CLI で列揃え、一覧表示時の書き込みなし、`install all` のカテゴリ構造、`install run` の既存ファイル保護と `--force` を確認した。
- 2つの ZIP のソースを使い、統合 runner と各依存 runner、TOP/FNC API の import および呼び出しシグネチャを確認した。RMC_POT、VASP、Packmol の実計算、PBS、サンプルの全件実行は未検証。
- Sphinx は英語ルート、`/en/`、`/ja/` をローカル生成した。三つのビルド合計で診断が 27 件から 15 件に減り、残りは旧ソースと共通だった。PyPI と GitHub Pages への反映は未確認。コミットとリリースは利用者が行う。

## 維持する記憶

### グローバル

- 配布可能な雛形の一覧 CLI を追加する場合は、`<module> install list` でファイル名と1行の用途を固定列で表示する。一覧は配布物を参照し、コピー処理と対象を共有する。旧 CLI の引数や配置先はプロジェクトごとに確認する。
- 日英の README・変更履歴・Pages は日本語を基準に揃える。変更履歴はタグの実ファイル、現在のコミット、ステージ済み変更と未ステージの差分を照合し、作業版と実際の公開状態を区別する。
- 配布処理を変更したときは sdist と wheel に含まれる実ファイルを確認し、インストール済みのコマンドで配置結果を検証する。雛形のコピーと計算の実行は別に扱う。

### rmc_dft 専用

- 旧 `rmc_dft` を起点とした3パッケージ。RMC_POT は `rmc_util`、VASP は `vasp_util`、両者の統合は `rmc_dft` が担当する。重複実装と一部の再公開が残る。
- 通常・手動 runner は `rmc_dft.runners`。編集対象の `config.yml` と `rmc_vasp_script_sequence_dat.py` は `install run` で配置する。init 名、実行番号とログ名は後方互換に関わる。
- v0.7.14 のインストーラは8カテゴリをコピーする。`list` は項目単位で示すが、コピー単位はカテゴリまたは `all`。単独 RMC 描画4本は提供 ZIP の `rmc_util` v0.1.12 に移った。
