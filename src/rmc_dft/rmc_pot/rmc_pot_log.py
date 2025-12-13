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

        # --- ログ解析の一時保存
        self._moves_cache = {}
        self._chi2_cache = {}
        self._dataset_cache = {}
        self._rw_cache = {}

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

    def _inspect_scan_rmc_loops(self, block_index: int) -> None:
        """
        for test

        RMC ログのループ構造を、順序のみで厳密に検出する検証専用ルーチン。
        ※「40 行以内」などの行距離条件は完全に排除。
        """

        print("============================================================")
        print(" INSPECT scan_rmc_loops (順序ベースの正しい検証)")
        print("============================================================")

        # --- ブロック範囲を取得 ---
        blocks = self._scan_rmc_blocks()
        if block_index < 0 or block_index >= len(blocks):
            print(f"[INSPECT] invalid block_index={block_index}")
            return

        b_start, b_end = blocks[block_index]
        if b_end == -1:
            b_end = len(self._log_lines) - 1

        print(f"[INSPECT] block range = {b_start} 〜 {b_end}")

        # --- ループ検出 ---
        loop_starts = []
        last_global_idx = -1  # 前回検出した Global の行番号

        print("\n[INSPECT] scanning TOTAL → Global …")

        for i in range(b_start, b_end + 1):
            line = self._log_lines[i].rstrip()

            # -------------------------------
            # STEP 1: TOTAL NUMBER OF MOVES
            # -------------------------------
            if "TOTAL NUMBER OF MOVES" in line:

                # 現在位置 i を開始候補として記録
                total_idx = i
                print(f"[FOUND TOTAL] line {total_idx}: {line}")

                # -------------------------------
                # STEP 2: total_idx 以降で Global を探す
                # -------------------------------
                found_global = False

                for j in range(total_idx + 1, b_end + 1):
                    line2 = self._log_lines[j].rstrip()

                    if "Global chi-squared value" in line2:
                        print(f"    [FOUND GLOBAL] line {j}: {line2}")

                        # 以前検出した Global より後ならば loop として採用
                        if j > last_global_idx:
                            loop_starts.append(total_idx)
                            last_global_idx = j
                            print(
                                f"    [REGISTER LOOP] start={total_idx}, global_at={j}"
                            )
                        else:
                            print(
                                f"    [SKIP] global {j} は前の global {last_global_idx} より前"
                            )

                        found_global = True
                        break

                if not found_global:
                    print(
                        f"    [SKIP] TOTAL {total_idx} に対応する Global が見つからない"
                    )

        print("\n[INSPECT] loop_starts =", loop_starts)
        print(f"[INSPECT] total loops detected = {len(loop_starts)}")

        # --- start/end の構造を可視化 ---
        print("\n[INSPECT] constructing loop ranges …")
        for idx, s in enumerate(loop_starts):
            if idx + 1 < len(loop_starts):
                e = loop_starts[idx + 1] - 1
            else:
                e = b_end
            print(f"    loop {idx}: start={s}, end={e}")

        print("============================================================")
        print(" END INSPECT")
        print("============================================================")

    def _inspect_moves(self, block_index: int) -> None:
        """
        for test

        ループブロック中で、GENERATED/TRIED/ACCEPTED の
        「行を正しく拾えているかだけ」を確認するための検証専用ルーチン。
        本番のパース処理はここでは一切しない。
        """

        print("============================================================")
        print(" INSPECT moves (内部検証)")
        print("============================================================")

        # ブロック検出（あなたと同じ）
        blocks = self._scan_rmc_blocks()
        print(f"[INSPECT] blocks = {blocks}")

        if block_index < 0 or block_index >= len(blocks):
            print(f"[INSPECT] invalid block_index={block_index}")
            return

        b_start, b_end = blocks[block_index]
        if b_end == -1:
            b_end = len(self._log_lines) - 1

        print(f"[INSPECT] block range = {b_start} 〜 {b_end}")

        print("\n[INSPECT] scanning lines for moves header and numbers...")

        header_line = None
        numbers_line = None

        for i in range(b_start, b_end + 1):
            line = self._log_lines[i].rstrip()

            # GENERATED/TRIED/ACCEPTED という「ヘッダー行」
            if "GENERATED" in line and "TRIED" in line and "ACCEPTED" in line:
                print(f"[FOUND HEADER] line {i}: {line}")
                header_line = i

                # 次の行をそのまま印字（数字行のはず）
                if i + 1 <= b_end:
                    numline = self._log_lines[i + 1].rstrip()
                    print(f"[FOUND NUMBER] line {i+1}: {numline}")
                    numbers_line = i + 1
                print("")

        print(f"[INSPECT] header_line  = {header_line}")
        print(f"[INSPECT] numbers_line = {numbers_line}")

        print("============================================================")
        print(" END INSPECT")
        print("============================================================")

    # -----------------------
    # ログファイルをパース
    # -----------------------

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
        RMC block 内部をパースする

        RMC++ のループを正しく切り出す正式版ルーチン。
        パースした結果をキャッシュに入れる

        - TOTAL NUMBER OF MOVES:
        - Global chi-squared value (per data point):
        の順序で 1 ループとみなす。
        """

        blocks = self._scan_rmc_blocks()
        if block_index < 0 or block_index >= len(blocks):
            return []

        b_start, b_end = blocks[block_index]
        if b_end == -1:
            b_end = len(self._log_lines) - 1

        total_lines = self._log_lines

        # -----------------------------
        # 1. TOTAL → Global のペアを検出
        # -----------------------------
        loop_starts: List[int] = []

        i = b_start
        while i <= b_end:
            line = total_lines[i]

            # TOTAL NUMBER OF MOVES が見つかった
            if "TOTAL NUMBER OF MOVES" in line:
                total_idx = i

                # 次に Global を探す
                j = i + 1
                found_global = False
                while j <= b_end:
                    if "Global chi-squared value (per data point):" in total_lines[j]:
                        # 正常なループ検出
                        loop_starts.append(total_idx)
                        found_global = True
                        break

                    # 次の TOTAL が来たらこの TOTAL は無効
                    if "TOTAL NUMBER OF MOVES" in total_lines[j]:
                        break

                    j += 1

                # （found_global が False の場合は無視される）
            i += 1

        # -----------------------------
        # 2. start/end 行インデックス構築
        # -----------------------------
        loops: List[Tuple[int, int]] = []

        for idx, start in enumerate(loop_starts):
            if idx + 1 < len(loop_starts):
                end = loop_starts[idx + 1] - 1
            else:
                end = b_end
            loops.append((start, end))

        return loops

    def _scan_moves(self, b_start: int, b_end: int, block_index: int):
        """
        RMC block の内部の move のループのキャッシュをパースする

        Args:
            b_start:
            b_end:
            block_index:

        Returns:

        """
        if block_index in self._moves_cache:
            return self._moves_cache[block_index]

        results = []

        header = "GENERATED        TRIED     ACCEPTED"

        i = b_start
        while i <= b_end:
            line = self._log_lines[i].rstrip()

            # ヘッダー検出
            if header in line:
                numbers_line = self._log_lines[i + 1].rstrip()
                parts = numbers_line.split()
                if len(parts) >= 3:
                    gen = int(parts[0])
                    tried = int(parts[1])
                    acc = int(parts[2])
                    results.append((gen, tried, acc))

                i += 2
                continue

            i += 1

        self._moves_cache[block_index] = results
        return results

    def _scan_global_chi2(self, block_index: int):
        if block_index in self._chi2_cache:
            return self._chi2_cache[block_index]

        loops = self._scan_rmc_loops(block_index)
        chi2_list = []

        for s, e in loops:
            val = None
            for line in self._log_lines[s : e + 1]:
                if "Global chi-squared value" in line:
                    parts = line.split()
                    for p in parts:
                        try:
                            val = float(p)
                            break
                        except Exception:
                            pass
                    break
            chi2_list.append(val)

        self._chi2_cache[block_index] = chi2_list
        return chi2_list

    def _scan_dataset_chi2(self, block_index: int):
        if block_index in self._dataset_cache:
            return self._dataset_cache[block_index]

        loops = self._scan_rmc_loops(block_index)
        ds_list = []

        for s, e in loops:
            val = None
            for line in self._log_lines[s : e + 1]:
                if "Chi-square/npoints" in line:
                    parts = line.split()
                    for p in parts:
                        try:
                            val = float(p)
                            break
                        except Exception:
                            pass
                    break
            ds_list.append(val)

        self._dataset_cache[block_index] = ds_list
        return ds_list

    def _scan_rw(self, block_index: int):
        if block_index in self._rw_cache:
            return self._rw_cache[block_index]

        loops = self._scan_rmc_loops(block_index)
        rw_list = []

        for s, e in loops:
            val = None
            for line in self._log_lines[s : e + 1]:
                if "Rw for the set" in line:
                    parts = line.split()
                    for p in parts:
                        try:
                            val = float(p)
                            break
                        except Exception:
                            pass
                    break
            rw_list.append(val)

        self._rw_cache[block_index] = rw_list
        return rw_list

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
        blocks = self._scan_rmc_blocks()
        if block < 0 or block >= len(blocks):
            return None
        b_start, b_end = blocks[block]
        moves = self._scan_moves(b_start, b_end, block)
        if loop < 0 or loop >= len(moves):
            return None
        return moves[loop][0]

    def get_tried(self, block: int, loop: int) -> Optional[int]:
        blocks = self._scan_rmc_blocks()
        if block < 0 or block >= len(blocks):
            return None
        b_start, b_end = blocks[block]
        moves = self._scan_moves(b_start, b_end, block)
        if loop < 0 or loop >= len(moves):
            return None
        return moves[loop][1]

    def get_accepted(self, block: int, loop: int) -> Optional[int]:
        blocks = self._scan_rmc_blocks()
        if block < 0 or block >= len(blocks):
            return None
        b_start, b_end = blocks[block]
        moves = self._scan_moves(b_start, b_end, block)
        if loop < 0 or loop >= len(moves):
            return None
        return moves[loop][2]

    def get_global_chi2(self, block: int, loop: int) -> Optional[float]:
        vals = self._scan_global_chi2(block)
        if loop < 0 or loop >= len(vals):
            return None
        return vals[loop]

    def get_dataset_chi2(self, block: int, loop: int) -> Optional[float]:
        vals = self._scan_dataset_chi2(block)
        if loop < 0 or loop >= len(vals):
            return None
        return vals[loop]

    def get_rw(self, block: int, loop: int) -> Optional[float]:
        vals = self._scan_rw(block)
        if loop < 0 or loop >= len(vals):
            return None
        return vals[loop]

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
