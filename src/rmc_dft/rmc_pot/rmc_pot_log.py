#!/usr/bin/env python
"""
K.KOBAYASHI
K.NAKADA, kengo.nakada@gmail.com
"""
import os
import shutil

from rmc_dft.config import Config
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from x_logger import XLogger


class RmcPotLog:

    def __init__(
        self,
        config: Optional[Config] = None,  # Config(),
        logger: Optional[XLogger] = None,  # XLogger,
        *,
        cfg_name: str = None,
        log_filename: Optional[str] = None,
    ) -> None:
        """
        config インスタンスを与えると、cfg_name はいらない

        Args:
            config (Config): 全てインスタンスが同じ Config()
            logger (XLogger): 全てのインスタンスが同じ XLogger()
            cfg_name (str):
            log_filename (str): jobファイル中にRMCのログを垂れ流した時はそれを書く
                                この指定がない時は cfg_name.log がログファイルとなる
        """
        self._logger: Optional[XLogger] = logger or XLogger()
        self._config: Optional[Config] = config or Config()
        self._cfg_name: Optional[str] = cfg_name or self._config.cfg_name

        # ログファイル名を決定
        # ログファイル名の指定がない時は cfg_name.log をログファイルとする
        if log_filename is None:
            log_filename = f"{self._cfg_name}.log"

        self._log_filename: str = log_filename
        self._log_lines: List[str] = []

        # --- ログファイルの自動読み込み ---
        self.load_log()

    # ============================================================
    # ログファイル読込み(メモリに入れる)
    # ============================================================

    def load_log(
        self,
        log_filename: str = None,
    ) -> None:
        """
        log ファイルが存在するなら読み込み、
        self._log_lines に保存する。
        (保存される内容はファイル全てなので、ファイルの中身は実はどうでもいい)
        """
        log_filename = log_filename or self._log_filename
        if not os.path.exists(self._log_filename):
            return

        try:
            with open(
                self._log_filename,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as f:
                self._log_lines = f.readlines()
            self._logger.info(f"Loaded log file: {self._log_filename}")

        except Exception as e:
            self._logger.error(f"Failed to read log file: {e}")
            self._log_lines = []

    def set_cfg_name(
        self,
        cfg_name: str,
    ) -> None:
        self._cfg_name: str = cfg_name
        self._log_filename = f"{cfg_name}.log"

        # ログファイルの再読み込み
        self.load_log()

    def get_cfg_name(self) -> str:
        return self._cfg_name

    # ============================================================
    # RMC パート開始・終了ペアの走査
    # ============================================================

    def _scan_rmc_blocks(self) -> List[Tuple[int, int]]:
        """
        ログ全体から「RMC_POT++ program ... END OF ATOMIC RMC++ PROGRAM!」の
        開始・終了ペアを抽出する。

        戻り値の各要素は (start_index, end_index) で、
        end_index が -1 の場合は「開始したが終了行が無い（未完）」を表す。
        """
        blocks: List[Tuple[int, int]] = []
        start_index: int = -1

        line_count: int = len(self._log_lines)
        i: int = 0

        while i < line_count:
            line: str = self._log_lines[i]

            # RMC パート開始の検出
            if "RMC_POT++ program" in line:
                # すでに開始中のブロックがあれば、それは未完として閉じる
                if start_index >= 0:
                    blocks.append((start_index, -1))
                start_index = i

            else:
                # RMC パート終了の検出
                if "END OF ATOMIC RMC++ PROGRAM" in line:
                    if start_index >= 0:
                        blocks.append((start_index, i))
                        start_index = -1

            i = i + 1

        # ループ終了後、開始したまま終わっていないブロックがあれば未完として追加
        if start_index >= 0:
            blocks.append((start_index, -1))

        return blocks

    def _scan_rmc_loops(self, block_index: int) -> List[Tuple[int, int]]:
        """
        指定された RMC ブロック内の loop 開始・終了行番号 (start, end) を返す。
        """
        blocks = self._scan_rmc_blocks()
        if block_index < 0 or block_index >= len(blocks):
            return []

        b_start, b_end = blocks[block_index]
        if b_end == -1:
            b_end = len(self._log_lines) - 1

        loop_ranges: List[Tuple[int, int]] = []
        start = -1

        for i in range(b_start, b_end + 1):
            line = self._log_lines[i]

            if "TOTAL NUMBER OF MOVES" in line:
                if start >= 0:
                    loop_ranges.append((start, i - 1))
                start = i

        if start >= 0:
            loop_ranges.append((start, b_end))

        return loop_ranges

    # ============================================================
    # RMC の終了判定（最後の RMC パートが閉じているか）
    # ============================================================
    def is_finished(self) -> bool:
        """
        ログの「最後の RMC パート」が正常終了しているかを判定する。

        - RMC パートが一度も現れない       → False
        - 最後の RMC パートが start のみ   → False
        - 最後の RMC パートが start〜end   → True

        ここでの「最後」は、ログの末尾から見て最後に現れた
        RMC_POT++ program ... の開始ブロックを意味する。
        """
        if len(self._log_lines) == 0:
            return False

        blocks: List[Tuple[int, int]] = self._scan_rmc_blocks()
        if len(blocks) == 0:
            return False

        last_block: Tuple[int, int] = blocks[-1]
        last_start: int = last_block[0]
        last_end: int = last_block[1]

        if last_start < 0:
            return False

        if last_end < 0:
            # 開始したが終了行が無い → 未完
            return False

        return True

    def get_num_rmc_block(self) -> int:
        """
        ログ中に出現した RMC パートの個数（開始ブロックの個数）を返す。
        未完のブロックも 1 と数える。
        """
        blocks: List[Tuple[int, int]] = self._scan_rmc_blocks()
        return len(blocks)

    def get_num_rmc_loop(self, block_index: int) -> int:
        """
        RMC ブロック内での loop 数の数
        Args:
            block_index:

        Returns:

        """
        loops = self._scan_rmc_loops(block_index)
        return len(loops)

    @staticmethod
    def _extract_value(lines: List[str], key: str, cast_func):
        for line in lines:
            if key in line:
                parts = line.replace("=", " ").split()
                for p in parts:
                    try:
                        return cast_func(p)
                    except Exception:
                        pass
        return None

    def get_generated(self, block: int, loop: int) -> Optional[int]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "GENERATED", int)

    def get_tried(self, block: int, loop: int) -> Optional[int]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "TRIED", int)

    def get_accepted(self, block: int, loop: int) -> Optional[int]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "ACCEPTED", int)

    def get_global_chi2(self, block: int, loop: int) -> Optional[float]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "Global chi-squared value", float)

    def get_dataset_chi2(self, block: int, loop: int) -> Optional[float]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "Chi-square/npoints", float)

    def get_rw(self, block: int, loop: int) -> Optional[float]:
        loops = self._scan_rmc_loops(block)
        if loop < 0 or loop >= len(loops):
            return None
        s, e = loops[loop]
        lines = self._log_lines[s : e + 1]
        return self._extract_value(lines, "Rw for the set", float)

    def clear(
        self,
        cfg_name: str,
    ) -> None:
        """
        rmc_pot の出力ファイルを消す

        Args:
            cfg_name (str):

        Returns:

        """
        delete_list = [
            "bcf",
            "calcdat",
            "chi",
            "expt",
            "fit",
            "free",
            "freer",
            "grid",
            "hgm",
            "hst",
            "pfq",
            "ppcf",
            "state",
            "",
        ]

        for extname in delete_list:
            if not os.path.isfile(f"{cfg_name}.{extname}"):
                continue
            try:
                self.remove_file(f"{cfg_name}.{extname}")

                if os.path.isfile(f"{cfg_name}start.grid"):
                    self.remove_file(f"{cfg_name}start.grid")
                if os.path.isfile(f"{cfg_name}start.hgm"):
                    self.remove_file(f"{cfg_name}start.hgm")
            except FileNotFoundError as e:
                self._logger.info(f"[SKIP] {e}")
            except PermissionError:
                self._logger.error(f"[Error] 権限がありません: {cfg_name}.{extname}")

    def remove_file(self, filename: str) -> bool:
        """
        現在の作業ディレクトリ（スクリプト実行フォルダ）にある指定ファイルを削除する。

        Args:
            filename (str): 削除するファイル名（相対/絶対どちらでも可）

        """
        # パスを絶対化（カレントディレクトリ基準）
        path = os.path.abspath(filename)

        if not os.path.isfile(path):
            self._logger.error(f"指定ファイルが存在しません: {path}")
            return False

        os.remove(path)
        self._logger.info(f"delete: {path}")
        return True

    def collect_result(self):
        self._logger.info("collect_result")

    def backup_result(
        self,
        log_dir: Optional[str] = None,
        cfg_name: Optional[str] = None,
    ):
        """
        Copy RMC log files to the specified directory.

        Args:
            log_dir (str): Directory to copy the log files to.
            cfg_name (str): Name of the configuration file.
        """
        self._logger.info("== backup_result")

        if not cfg_name:
            cfg_name = self.cfg_name

        if not log_dir:
            log_dir = self._config.rmc_log_dir

        if not os.path.exists(log_dir):
            self._logger.info(f"mkdir {log_dir}")
            os.makedirs(log_dir)

        files_to_copy = [
            "grep_khi_RMC.txt",
            f"{cfg_name}.chi",
            f"{cfg_name}.cfg",
            f"{cfg_name}.sq",
            f"{cfg_name}.dat",
            f"{cfg_name}.hst",
            f"{cfg_name}.ppcf",
            f"{cfg_name}.fit",
            f"{cfg_name}.pfq",
            f"{cfg_name}.log",
        ]

        for file_name in files_to_copy:
            if os.path.exists(f"{file_name}"):
                shutil.copy(file_name, log_dir)
                self._logger.info(f"Copied {file_name} to {log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")
