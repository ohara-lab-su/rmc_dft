#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotHst
-----------
RMC_POT の .hst ファイルを読み取り、
各ループ（hst の 1 行＝1 ループ）ごとの履歴データを提供する。

・hst のデータ行は「generated 〜 chi2_set1」までの数値カラムを持つ。
・行番号そのものが RMC のループ番号に対応する。
・loop_index=None の場合は全ループの値を list で返す。
・loop_index を整数で与えた場合は、そのループ行の値を返す。
・余計な計算・捏造は禁止し、ログに書かれた値だけを返す。
・既存互換 API（read_chi2）は旧仕様と同じ形式 (steps, chi2_tot_list) を返す。

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
    """
    RMC_POT .hst 履歴データクラス。
    """

    def __init__(
        self,
        hst_path: Optional[str] = None,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
    ) -> None:

        # ロガー
        self._logger: XLogger = logger or XLogger(logger_name="RmcPotHst")

        # Config
        self._config: Config = config or Config()

        # HST ファイルパス
        self._hst_path: str = hst_path or self._config.cfg_name

        # 生ログ行
        self._lines: List[str] = []

        # パース済みデータ
        self._records: List[Dict[str, Union[int, float]]] = []

        # フラグ
        self._parsed: bool = False

        # 読み込み → パース
        self._load_file()
        self._parse()

    # ---------------------------------------------------------------
    # HST ファイル読み込み（純粋に行読み取り）
    # ---------------------------------------------------------------
    def _load_file(self) -> None:
        try:
            with open(self._hst_path, "r") as f:
                self._lines = f.readlines()
            self._logger.info(f"Loaded HST: {self._hst_path}")
        except FileNotFoundError:
            self._logger.warning(f"HST not found: {self._hst_path}")
            self._lines = []

    # ---------------------------------------------------------------
    # パース（唯一の構造化処理）
    # ---------------------------------------------------------------
    def _parse(self) -> None:
        """
        hst の「データ行」を抽出し、_records に格納する。
        データ行の条件：
            ・空白区切りで 9 カラム以上
            ・すべて数値として読み込める
        """
        if self._parsed:
            return

        for line in self._lines:
            items = line.strip().split()
            if len(items) < 9:
                continue

            # データ行かどうかの判定：generated が整数であるかどうか
            # （hst は行番号ではないため先頭の items[0] の名前は "generated"）
            try:
                rec = {
                    "generated": int(items[0]),
                    "tried": int(items[1]),
                    "accepted": int(items[2]),
                    "time": int(items[3]),
                    "tried_per_gen": float(items[4]),
                    "acc_per_tried": float(items[5]),
                    "chi2_tot": float(items[6]),
                    "chi2_set1": float(items[7]),
                }
                self._records.append(rec)
            except Exception:
                # 数値変換できない行は無視
                continue

        self._parsed = True

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
    def get_num_loops(self) -> int:
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
    def get_tried_per_gen(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["tried_per_gen"])
            return out
        return self._records[loop_index]["tried_per_gen"]

    # -----------------------------
    def get_acc_per_tried(self, loop_index: Optional[int] = None):
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["acc_per_tried"])
            return out
        return self._records[loop_index]["acc_per_tried"]

    # -----------------------------
    def get_chi2_tot(self, loop_index: Optional[int] = None):
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
