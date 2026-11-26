"""同梱スクリプトの一覧表示と作業ディレクトリへの配置を行う。"""

from __future__ import annotations

import argparse
import shutil
from importlib import metadata
from pathlib import Path

CATEGORIES = ("analyze", "check", "edit", "job", "make", "plot", "run", "tools")
CHOICES = (*CATEGORIES, "all")
_SCRIPTS_DIR = Path("share/rmc_dft/scripts")
_DESCRIPTIONS = {
    "analyze/analyze_sio2_qn.py": "SiO2 構造の Qn 分布を解析",
    "analyze/analyze_zeolite.py": "ゼオライト骨格を解析",
    "check/check_rmc_chi.py": "RMC の χ² を確認",
    "check/check_rmc_finalized.py": "RMC 計算の終了を確認",
    "check/check_vasp_distance.py": "周期境界を考慮した短い原子間距離を確認",
    "check/check_vasp_finalized.py": "VASP 計算の終了を確認",
    "edit/data_edit_dat.py": "RMC_POT の DAT 入力を編集",
    "edit/data_edit_incar.py": "VASP の INCAR を編集",
    "edit/data_edit_kpoints.py": "VASP の KPOINTS を編集",
    "edit/data_edit_potcar.py": "VASP の POTCAR を作成",
    "job/job_hpcs2024_node1.sh": "HPCS 2024 向け PBS ジョブ例（ノード 01・02）",
    "job/job_hpcs2024_node2.sh": "HPCS 2024 向け PBS ジョブ例（ノード 03・04）",
    "make/make_analyze_qn.py": "VASP 構造から Qn の個数と比率を表示",
    "make/make_log_dirname.py": "保存済みの RMC・DFT ログを番号順に整理",
    "make/make_mass_density.py": "原子組成と構造から質量密度を求める",
    "make/make_qn_fnc_top.py": "Qn ネットワークから FNC と TOP を生成",
    "make/make_qn_snc.py": "Qn 設定から SNC 制約を生成",
    "make/qn_config.json": "Qn と構造制約の設定例",
    "plot/diff_incar.py": "二つの INCAR の差分を表示",
    "plot/get_force.py": "OUTCAR の最終ステップから力を抽出",
    "plot/get_force_converge.py": "OUTCAR から力ノルムの推移を抽出",
    "plot/get_position.py": "vasprun.xml から原子位置と変位を取得",
    "plot/plot_distance_histgram.py": "原子間距離ヒストグラムを描画",
    "plot/plot_energy.py": "VASP のエネルギーを描画",
    "plot/plot_multi_converge.py": "RMC と VASP の収束履歴を対比",
    "plot/plot_multi_energy.py": "複数の VASP 計算のエネルギーを比較",
    "plot/plot_multi_fit.py": "複数の RMC 計算の FIT を比較",
    "plot/plot_multi_hst.py": "複数の RMC 計算の HST を比較",
    "plot/plot_rmc_hst_converge.py": "HST の収束履歴を描画",
    "plot/plot_rmc_log_converge.py": "RMC ログの収束履歴を描画",
    "run/config.yml": "RMC–DFT の共通設定例",
    "run/conv_cfg2poscar.py": "RMC の CFG を VASP 形式へ変換",
    "run/conv_poscar2cfg.py": "POSCAR を RMC の CFG へ変換",
    "run/make_amorphous_random.py": "Packmol で初期非晶質構造を生成",
    "run/make_composition_ratio.py": "組成比から原子数の組み合わせを求める",
    "run/make_number_density.py": "原子組成と質量密度から数密度を求める",
    "run/rmc_vasp_script_sequence_dat.py": "RMC と VASP の手動実行順序を指定",
    "tools/clean.sh": "RMC と DFT の出力削除スクリプトを呼び出す",
    "tools/clean_dft.py": "VASP の出力ファイルを削除",
    "tools/clean_rmc.py": "指定した構造名に対応する RMC の出力を削除",
}


def _find_scripts() -> dict[Path, Path]:
    """配布記録から、同梱ファイルの相対パスと実ファイルを取得する。"""
    distribution = metadata.distribution("rmc-dft")
    records = distribution.files
    if records is None:
        raise FileNotFoundError("rmc-dft の配布ファイルの記録がありません")

    scripts = {}
    prefix = _SCRIPTS_DIR.parts
    for record in records:
        parts = record.parts
        for index, part in enumerate(parts):
            if part != prefix[0] or parts[index : index + len(prefix)] != prefix:
                continue

            relative = Path(*parts[index + len(prefix) :])
            if (
                len(relative.parts) >= 2
                and relative.parts[0] in CATEGORIES
                and "__pycache__" not in relative.parts
            ):
                source = Path(distribution.locate_file(record))
                if source.is_file():
                    scripts[relative] = source
            break
    return dict(sorted(scripts.items()))


def _list_scripts() -> None:
    scripts = _find_scripts()
    if not scripts:
        raise FileNotFoundError("同梱スクリプトが見つかりません")

    width = max(len("FILE"), max(len(path.as_posix()) for path in scripts))
    print(f"{'FILE':<{width}}  DESCRIPTION")
    for path in scripts:
        name = path.as_posix()
        description = _DESCRIPTIONS.get(name, "作業ディレクトリ用の配布ファイル")
        print(f"{name:<{width}}  {description}")


def install(
    category: str,
    *,
    force: bool = False,
    destination: Path | None = None,
) -> list[Path]:
    """指定カテゴリ以下の全ファイルを作業ディレクトリへコピーする。"""
    if category not in CHOICES:
        raise ValueError(f"カテゴリを指定してください: {', '.join(CHOICES)}")

    base = Path.cwd()
    if destination is not None:
        base = Path(destination)
    scripts = _find_scripts()

    categories = (category,)
    if category == "all":
        categories = CATEGORIES

    pairs = []
    for name in categories:
        selected = [
            (relative, source)
            for relative, source in scripts.items()
            if relative.parts[0] == name
        ]
        if not selected:
            raise FileNotFoundError(f"同梱カテゴリが見つかりません: {name}")
        for relative, source in selected:
            if category != "all":
                relative = relative.relative_to(name)
            pairs.append((source, base / relative))

    conflicts = [str(target) for _, target in pairs if target.exists()]
    if conflicts and not force:
        raise FileExistsError(
            "既存ファイルがあります（--force で上書き）:\n" + "\n".join(conflicts)
        )

    for source, target in pairs:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return [target for _, target in pairs]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rmc_dft")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("install", help="同梱ファイルを一覧表示またはコピー")
    command.add_argument(
        "category",
        choices=(*CHOICES, "list"),
        help="コピーするカテゴリ、全カテゴリを表す all、または一覧表示の list",
    )
    command.add_argument("--force", action="store_true", help="既存ファイルを上書き")
    args = parser.parse_args(argv)
    try:
        if args.category == "list":
            _list_scripts()
        else:
            for path in install(args.category, force=args.force):
                print(path)
    except (OSError, ValueError, metadata.PackageNotFoundError) as exc:
        parser.exit(1, f"エラー: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
