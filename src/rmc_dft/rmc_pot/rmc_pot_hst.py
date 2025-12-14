#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotHst
-----------
RMC_POT の .hst ファイルを読み取り、
History::save が 1 回呼ばれたときの履歴レコードを 1 つとして扱う。

・履歴レコードは「generated ～ chi2/F(Q)_set#1」までの 8 個の数値要素から成る。
・ファイル中の表ヘッダ行（generated ...）の直後から、
　空行または非数値行が出るまでを「履歴表」として読み取る。
・History::save の呼び出し回数 ＝ 履歴レコード数。

内部構造：
_records = [
    {
        "generated": int,
        "tried": int,
        "accepted": int,
        "time": int,
        "tried_per_gen": float,
        "acc_per_tried": float,
        "chi2_tot": float,
        "chi2_set1": float,
    },
    ...
]
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotHst:

    def __init__(
        self,
        hst_name: Optional[str] = None,
        cfg_name: Optional[str] = None,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
    ) -> None:
        """
        1) cfg_name があればそれが優先
           hst_nameと書いている場合がある
           基本的には hst_name.hst ファイルを読む
           内部的には cfg_name として扱う
        2) config があればそれが優先

        Args:
            hst_path (str):
            cfg_name (str):
            config (Config):
            logger (XLogger):
        """
        self._logger: XLogger = logger or XLogger(logger_name="RmcPotHst")

        # HST ファイル名は cfg_name を基準に決定する
        if hst_name is not None:
            self._hst_file: str = hst_name
        elif cfg_name is not None:
            self._hst_file: str = f"{cfg_name}.hst"
        elif config is not None:
            config: Config = Config("config.yaml")
            cfg_name: str = config.cfg_name
            self._hst_file: str = f"{cfg_name}.hst"
        else:
            self._logger.error(f"hst_name or cfg_name not provided")
            raise NotImplementedError

        # 生ログ行と記録行
        self._lines: List[str] = []
        self._records: List[Dict[str, Union[int, float]]] = []

        # パースしたか？
        self._parsed: bool = False

        self._load_file()
        self._parse()

    # ---------------------------------------------------------------
    # HST ファイル読み込み（純粋に行読み取り）
    # ---------------------------------------------------------------
    def _load_file(self) -> None:
        try:
            with open(self._hst_file, "r") as f:
                self._lines = f.readlines()
            self._logger.info(f"Loaded HST: {self._hst_file}")
        except FileNotFoundError:
            self._logger.warning(f"HST not found: {self._hst_file}")
            self._lines = []

    # ---------------------------------------------------------------
    # パース（唯一の構造化処理）
    # ---------------------------------------------------------------
    def _parse(self) -> None:
        """
        hst の「履歴表」を抽出し、_records に格納する。

        履歴表の構造（横方向＝1 レコード＝History::save 1 回分）:
            generated
            tried
            accepted
            time
            tried/gen
            acc/tried
            chi2_tot/data_point
            chi2/F(Q)_set#1

        つまり、**横方向に 8 個の数値カラム**を持つ行だけを
        1 レコードとして採用する。
        """

        # ==== 修正ここから ====
        if self._parsed:
            return

        in_table: bool = False  # 「generated ...」ヘッダ以降かどうか

        for line in self._lines:
            stripped: str = line.strip()

            # 空行
            if stripped == "":
                # すでに履歴表を読み始めていれば、ここで終了
                if in_table:
                    break
                # まだヘッダ前なら単にスキップ
                continue

            # まだヘッダ行を見つけていない段階
            if not in_table:
                # 履歴表ヘッダ行を検出
                if stripped.startswith("generated"):
                    in_table = True  # 次の行からデータ行として扱う
                continue

            # ここに来たら、ヘッダ行の「次以降」＝データ候補行
            items: List[str] = stripped.split()

            # 横方向の要素数が 8 未満なら履歴表の終端とみなす
            if len(items) < 8:
                break

            try:
                # 8 個すべて数値に変換できるかどうかを確認
                generated_val: int = int(items[0])
                tried_val: int = int(items[1])
                accepted_val: int = int(items[2])
                time_val: int = int(items[3])
                tried_per_gen_val: float = float(items[4])
                acc_per_tried_val: float = float(items[5])
                chi2_tot_val: float = float(items[6])
                chi2_set1_val: float = float(items[7])
            except ValueError:
                # 数値に変換できない＝履歴表の終端とみなして終了
                break

            rec: Dict[str, Union[int, float]] = {
                "generated": generated_val,
                "tried": tried_val,
                "accepted": accepted_val,
                "time": time_val,
                "tried_per_gen": tried_per_gen_val,
                "acc_per_tried": acc_per_tried_val,
                "chi2_tot": chi2_tot_val,
                "chi2_set1": chi2_set1_val,
            }
            self._records.append(rec)

        self._parsed = True
        # ==== 修正ここまで ====

    # ==============================================================
    # 互換 API（read_chi2）
    # ==============================================================
    def read_chi2(self) -> Tuple[List[int], List[float]]:
        """
        （互換 API）
        旧 RmcPotHst は：
            steps = [0, 1, 2, ...]
            chi2_list = [chi2_tot_of_loop0, chi2_tot_of_loop1, ...]
        の形式で返していたため、それを再現する。

        ※ hst には "step" が存在しないため、
          行番号＝ステップ番号として扱う。
        """
        steps: List[int] = []
        chi2: List[float] = []

        for i, rec in enumerate(self._records):
            steps.append(i)
            chi2.append(rec["chi2_tot"])

        return steps, chi2

    # ==============================================================
    # ループ総数
    # ==============================================================
    def get_num_rmc_loops(self) -> int:
        """
        hst に含まれるデータ行数＝ループ数を返す。
        """
        return len(self._records)

    # ==============================================================
    # 以下、個別 API
    # ==============================================================

    # -----------------------------
    def get_generated(self, loop_index: Optional[int] = None):
        """
        generated（このループで生成した移動数）を返す。
        loop_index=None → 全ループ list
        loop_index=int → 当該ループの値
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["generated"])
            return out

        return self._records[loop_index]["generated"]

    # -----------------------------
    def get_tried(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["tried"])
            return out
        return self._records[loop_index]["tried"]

    # -----------------------------
    def get_accepted(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["accepted"])
            return out
        return self._records[loop_index]["accepted"]

    # -----------------------------
    def get_time(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["time"])
            return out
        return self._records[loop_index]["time"]

    # -----------------------------
    def get_tried_per_generated(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["tried_per_gen"])
            return out
        return self._records[loop_index]["tried_per_gen"]

    # -----------------------------
    def get_accepted_per_tried(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["acc_per_tried"])
            return out
        return self._records[loop_index]["acc_per_tried"]

    # -----------------------------
    def get_chi2_tot(self, loop_index: Optional[int] = None):
        """
        全データーセットをまとめた chi
        chi2_tota/data_point

        おそらく
        log側 (global)
        hst側 (total)
        で同じものを指している

        Args:
            loop_index:

        Returns:

        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_tot"])
            return out
        return self._records[loop_index]["chi2_tot"]

    # -----------------------------
    def get_chi2_set1(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_set1"])
            return out
        return self._records[loop_index]["chi2_set1"]
