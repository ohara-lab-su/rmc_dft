#!/usr/bin/env bash
set -euo pipefail
DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
PACKAGE_DIR="$ROOT_DIR/src/rmc_dft"
OUTPUT_DIR="$DOCS_DIR/_build/html"

if [[ ! -d "$PACKAGE_DIR" ]]; then
  echo "Package not found: $PACKAGE_DIR" >&2
  exit 1
fi
export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

for lang in en ja; do
  SOURCE_DIR="$DOCS_DIR/$lang"
  [[ -f "$SOURCE_DIR/index.md" ]] || { echo "Missing $SOURCE_DIR/index.md" >&2; exit 1; }
  mkdir -p "$SOURCE_DIR/api"
  sphinx-apidoc --force --module-first -o "$SOURCE_DIR/api" "$PACKAGE_DIR"
  # /en/ と /ja/ は独立した Sphinx サイトとして生成する。
  sphinx-build -b html -c "$DOCS_DIR" -D "language=$lang" \
    "$SOURCE_DIR" "$OUTPUT_DIR/$lang"
done
# 英語のルートはリダイレクトではなく、同一ソースから独立にビルドする。
sphinx-build -b html -c "$DOCS_DIR" -D language=en \
  "$DOCS_DIR/en" "$OUTPUT_DIR"

# 静的ファイルの配置
if [[ -f "$DOCS_DIR/_robots.txt" ]]; then
  cp "$DOCS_DIR/_robots.txt" "$OUTPUT_DIR/robots.txt"
fi
touch "$OUTPUT_DIR/.nojekyll"
for file in "$OUTPUT_DIR/index.html" "$OUTPUT_DIR/en/index.html" "$OUTPUT_DIR/ja/index.html"; do
  [[ -s "$file" ]] || { echo "Missing output: $file" >&2; exit 1; }
done
