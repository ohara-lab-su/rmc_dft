"""インストール済みの編集用スクリプトを作業ディレクトリに配置する。"""

from __future__ import annotations

import argparse
import shutil
import sysconfig
from importlib import metadata
from pathlib import Path

DISTRIBUTION_NAME = "rmc-dft"
SCRIPTS_RELATIVE_DIRECTORY = Path("share/rmc_dft/scripts")
CATEGORIES = ("run", "plot", "make", "check", "tool", "get", "analyze", "convert", "edit")


def find_installed_scripts(category: str | None = None) -> list[Path]:
    """標準のインストール先と配布記録からスクリプトを取得する。"""
    sources: dict[tuple[str, str], Path] = {}
    root = Path(sysconfig.get_path("data")) / SCRIPTS_RELATIVE_DIRECTORY
    selected = CATEGORIES if category is None else (category,)
    for name in selected:
        directory = root / name
        if directory.is_dir():
            for path in sorted(directory.glob("*.py")):
                if path.is_file():
                    sources[(name, path.name)] = path

    distribution = metadata.distribution(DISTRIBUTION_NAME)
    for record in distribution.files or []:
        parts = Path(str(record)).parts
        marker = SCRIPTS_RELATIVE_DIRECTORY.parts
        for index in range(len(parts) - len(marker) - 1):
            if parts[index:index + len(marker)] != marker:
                continue
            remainder = parts[index + len(marker):]
            if len(remainder) != 2 or remainder[0] not in selected:
                continue
            path = Path(distribution.locate_file(record))
            if path.is_file() and path.suffix == ".py":
                sources.setdefault((remainder[0], path.name), path)
            break
    return [sources[key] for key in sorted(sources)]


def install_scripts(destination: Path, *, category: str | None = None,
                    force: bool = False) -> tuple[int, int]:
    """作業ディレクトリにスクリプトをコピーする。既存ファイルは原則保持する。"""
    if category is not None and category not in CATEGORIES:
        raise ValueError(f"不明なカテゴリー: {category}")
    scripts = find_installed_scripts(category)
    if not scripts:
        raise RuntimeError("インストール済みスクリプトが見つかりません。配布設定を確認してください。")
    names = [path.name for path in scripts]
    if len(names) != len(set(names)):
        raise RuntimeError("同名のスクリプトが複数カテゴリーに存在します。")
    destination.mkdir(parents=True, exist_ok=True)
    copied = skipped = 0
    for source in scripts:
        target = destination / source.name
        if target.exists() and not force:
            print(f"既存のためスキップ: {target.name}")
            skipped += 1
            continue
        if target.is_dir():
            raise IsADirectoryError(target)
        existed = target.exists()
        shutil.copy2(source, target)
        print(f"{'上書き' if existed else 'コピー'}: {target.name}")
        copied += 1
    return copied, skipped


def main() -> None:
    """rmc_dft install [カテゴリー] [--force] を処理する。"""
    parser = argparse.ArgumentParser(prog="rmc_dft")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("install", help="編集可能なスクリプトを配置する")
    command.add_argument("category", nargs="?", choices=CATEGORIES)
    command.add_argument("--force", action="store_true", help="既存ファイルを上書きする")
    args = parser.parse_args()
    copied, skipped = install_scripts(Path.cwd(), category=args.category, force=args.force)
    print(f"完了: コピー {copied} 件、スキップ {skipped} 件")


if __name__ == "__main__":
    main()
