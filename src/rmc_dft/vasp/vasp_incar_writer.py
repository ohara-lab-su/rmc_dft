#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any
from x_logger import XLogger


class VaspIncarWriter:
    """
    INCAR の実ファイルを、コメント・空行を保持したまま編集・書き換えるためのクラス。

    基本的に TAG の 入出力(INCARファイルに対する読み書き)だけならば、
    VaspIncar() で終わる話なのだが、INCAR 中の既存のコメントや
    既存のフォーマット形式を維持するために、読み書き関係を強化するクラスが
    必要で、そのための機能をこのクラスが有する

    目的:
        - 既存ファイルの構造を壊さない
        - 特定タグのみ置換・追加・削除ができる
    """

    def __init__(
        self,
        incar_name: str = "INCAR",
        logger: XLogger = None,
    ):
        """

        Args:
            incar_name (str):
            logger (XLogger):
        """
        if not logger:
            logger = XLogger()
        self._logger = logger

        self.incar_name: str = incar_name

        if os.path.exists(self.incar_name):
            self._logger.info(f"== OPEN INCAR: incar_name = {self.incar_name}")
            with open(self.incar_name, "r", encoding="utf-8") as f:
                self.lines: list[str] = f.readlines()
        else:
            self._logger.info(f"== OPEN INCAR (NEW)")
            self.lines: list[str] = []

    @staticmethod
    def _is_value_line(line: str) -> bool:
        """タグ行かどうかを判定する（コメント行・空行は除外）。"""
        stripped = line.strip()
        return stripped != "" and not stripped.startswith("#")

    def set_tag(self, tag: str, value: Any) -> None:
        """
        タグを設定する。既存の同タグがあれば上書き、なければ末尾に追加する。
        コメントや空行は保持される。
        """
        tag_upper = tag.upper()
        new_line = f" {tag_upper} = {value}\n"
        found = False
        new_lines = []

        for line in self.lines:
            if self._is_value_line(line):
                # コメント除去前部分で '=' を検索
                before_comment = line.split("#", 1)[0]
                if "=" in before_comment:
                    key = before_comment.split("=")[0].strip().upper()
                    if key == tag_upper:
                        new_lines.append(new_line)
                        found = True
                        continue
            new_lines.append(line)

        # ファイル内にタグがなかった場合 --> 末尾に追加
        if not found:
            if len(new_lines) > 0 and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(new_line)

        self.lines = new_lines
        self._write()

    def remove_tag(self, tag: str) -> None:
        """指定タグの行を削除する（コメント・空行は保持）。"""
        tag_upper = tag.upper()
        new_lines = []
        for line in self.lines:
            if self._is_value_line(line):
                before_comment = line.split("#", 1)[0]
                if "=" in before_comment:
                    key = before_comment.split("=")[0].strip().upper()
                    if key == tag_upper:
                        continue  # スキップ＝削除
            new_lines.append(line)
        self.lines = new_lines
        self._write()

    def _write(self) -> None:
        """現在の行バッファをファイルに書き戻す。"""
        with open(self.incar_name, "w", encoding="utf-8") as f:
            f.writelines(self.lines)
