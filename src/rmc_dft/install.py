"""パッケージに同梱された scripts のカテゴリを作業ディレクトリに展開する。"""

from __future__ import annotations

import argparse
import shutil
from importlib.resources import files
from pathlib import Path

CATEGORIES = ("analyze", "check", "edit", "job", "make", "plot", "run", "tools")
CHOICES = (*CATEGORIES, "all")


def install(category: str, *, force: bool = False, destination: Path | None = None) -> list[Path]:
    """指定カテゴリ以下の全ファイルをカレントディレクトリへコピーする。"""
    if category not in CHOICES:
        raise ValueError(f"カテゴリを指定してください: {', '.join(CHOICES)}")
    root = files("rmc_dft").joinpath("scripts")
    base = Path.cwd() if destination is None else Path(destination)
    pairs = []
    categories = CATEGORIES if category == "all" else (category,)
    for name in categories:
        source_dir = root.joinpath(name)
        if not source_dir.is_dir():
            raise FileNotFoundError(f"同梱カテゴリが見つかりません: {name}")
        for source, relative in _walk(source_dir):
            target = base / name / relative if category == "all" else base / relative
            pairs.append((source, target))
    conflicts = [str(dst) for _, dst in pairs if dst.exists()]
    if conflicts and not force:
        raise FileExistsError("既存ファイルがあります（--force で上書き）:\n" + "\n".join(conflicts))
    for source, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as src, dst.open("wb") as out:
            shutil.copyfileobj(src, out)
    return [dst for _, dst in pairs]


def _walk(directory, prefix=Path()):
    for entry in sorted(directory.iterdir(), key=lambda item: item.name):
        relative = prefix / entry.name
        if entry.is_dir():
            yield from _walk(entry, relative)
        elif entry.is_file():
            yield entry, relative


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rmc_dft")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("install", help="カテゴリ以下の全ファイルをカレントディレクトリにコピー")
    command.add_argument("category", choices=CHOICES)
    command.add_argument("--force", action="store_true", help="既存ファイルを上書き")
    args = parser.parse_args(argv)
    try:
        for path in install(args.category, force=args.force):
            print(path)
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        parser.exit(1, f"エラー: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
