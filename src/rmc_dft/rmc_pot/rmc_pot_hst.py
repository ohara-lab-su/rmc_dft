#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotHst
----------
RMC_POT の .hst ファイルを読み取り、各ステップの履歴データを解析する。

・hst は行ベースのログ形式であり、シミュレーションの「履歴（History）」を示す。
・有効行は「先頭が整数」で始まり、最低 9 列の数値を持つ。
・各行が 1 ステップに対応し、generated / tried / accepted / χ2 など
  RMC のアルゴリズム評価に必要な物理量が並ぶ。

このクラスは以下の方針に従う：
----------------------------------
1. ファイル読み込みは最初の一度だけ
2. パースも最初の一度だけ
3. 全 API は必ず個別実装し、共通関数へまとめない（疎結合）
4. loop_index=None → 全ループのリストを返す
5. loop_index=int → 単一ステップの値を返す
6. ログに存在しない量は絶対に計算しない（捏造禁止）
7. 既存の read_chi2() は互換形式を維持する

このクラスは「ファイル形式 → データ構造化」までを担当し、
物理的解釈やフィッティングには踏み込まない。
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import re

from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotHst:
    """
    RMC_POT .hst の履歴データ管理クラス。

    _records: List[Dict]
        パース済みの数値行だけを格納した内部データ。
        各 dict は 1 行分の情報（1 ステップ）を持つ。

        例：
        {
            "step": 0,
            "generated": 0,
            "tried": 0,
            "accepted": 0,
            "time": 0,
            "tried_per_gen": 0.0,
            "acc_per_tried": 0.0,
            "chi2_tot": 7.616e+04,
            "chi2_set1": 2.208e+07,
        }

    各 API は、この _records から値を取り出すだけであり、
    追加の計算や推測は行わない。
    """

    def __init__(
        self,
        hst_path: Optional[str] = None,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
    ) -> None:

        # logger を外部から渡せるようにする（rmc_dft の共通設計）
        self._logger: XLogger = logger or XLogger(logger_name="RmcPotHst")

        # config がある場合は config.cfg_name を使う
        self._config: Config = config or Config()

        # hst パスは明示指定 > config.cfg_name の優先順位
        self._hst_path: str = hst_path or self._config.cfg_name

        # 生ログ行と、パース結果を保持する領域
        self._lines: List[str] = []
        self._records: List[Dict[str, Union[int, float]]] = []

        # パース済みかどうかのフラグ
        self._parsed: bool = False

        self._load_file()
        self._parse()

    # ==============================================================
    # ファイル読み込み
    # ==============================================================
    def _load_file(self) -> None:
        """
        HST ファイルを全行読み込む。
        この段階では内容の解析は行わず、生テキストを保持するだけ。
        """
        try:
            with open(self._hst_path, "r") as f:
                self._lines = f.readlines()
            self._logger.info(f"Loaded HST: {self._hst_path}")

        except FileNotFoundError:
            self._logger.warning(f"HST not found: {self._hst_path}")
            self._lines = []

    # ==============================================================
    # パース処理（唯一の構造化処理）
    # ==============================================================
    def _parse(self) -> None:
        """
        生テキストから数値行だけを抽出し、_records に展開する。
        ここが唯一のデータ構造化ポイントであり、後の API は _records を読むだけ。

        HST のフォーマットは以下のような整形済みカラムを含む：

            generated    tried    accepted    time   tried/gen   acc/tried   chi2_tot    chi2_set1

        先頭の整数（step）が本当に整数かどうかでデータ行を識別する。
        """
        if self._parsed:
            return  # 重複パースを避ける

        for line in self._lines:
            items = line.strip().split()

            # データ行の条件：最低 9 列以上かつ items[0] が整数
            if len(items) < 9:
                continue
            if not items[0].isdigit():
                continue

            # 数値行と判断 → フィールドを抽出する
            try:
                rec = {
                    "step": int(items[0]),
                    "generated": int(items[1]),
                    "tried": int(items[2]),
                    "accepted": int(items[3]),
                    "time": int(items[4]),
                    "tried_per_gen": float(items[5]),
                    "acc_per_tried": float(items[6]),
                    "chi2_tot": float(items[7]),
                    "chi2_set1": float(items[8]),
                }
                self._records.append(rec)

            except Exception:
                # 整数変換失敗や float 変換失敗 → 無視
                continue

        self._parsed = True

    # ==============================================================
    # 既存互換 API（rmc_dft 既存コードの依存性を壊さないため）
    # ==============================================================
    def read_chi2(self):
        """
        旧 RmcPotHst が提供していた I/F と互換のメソッド。
        (steps, chi2_tot_list) を返す。

        ・既存コードで read_chi2() を使っている部分を壊さないために残す。
        ・内部では _records を読むだけなので動作は安定している。
        """
        steps: List[int] = []
        chi2: List[float] = []

        for rec in self._records:
            steps.append(rec["step"])
            chi2.append(rec["chi2_tot"])

        return steps, chi2

    # ==============================================================
    # 以下、個別 API（まとめ禁止・疎結合・独立実装）
    # ==============================================================

    def get_step(self, loop_index: Optional[int] = None):
        """
        step を取得する。
        loop_index=None → 全ステップのリスト
        loop_index=int → 指定ステップの値
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["step"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["step"]

    def get_generated(self, loop_index: Optional[int] = None):
        """
        generated（生成試行数）を返す。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["generated"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["generated"]

    def get_tried(self, loop_index: Optional[int] = None):
        """
        tried（実際に評価された試行数）を返す。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["tried"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["tried"]

    def get_accepted(self, loop_index: Optional[int] = None):
        """
        accepted（受理された試行数）を返す。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["accepted"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["accepted"]

    def get_time(self, loop_index: Optional[int] = None):
        """
        time（このループの経過時間）を返す。
        RMC_POT 内部ユニットであり、秒とは限らない。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["time"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["time"]

    def get_tried_per_gen(self, loop_index: Optional[int] = None):
        """
        tried/gen（生成試行に対する実評価割合）を返す。
        ログに記録された値をそのまま返し、再計算は行わない。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["tried_per_gen"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["tried_per_gen"]

    def get_acc_per_tried(self, loop_index: Optional[int] = None):
        """
        acc/tried（試行に対する受理割合）を返す。
        RMC_POT のログが記録した生データを返す。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["acc_per_tried"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["acc_per_tried"]

    def get_chi2_tot(self, loop_index: Optional[int] = None):
        """
        χ2_tot/data_point（総 χ² / データ点）を返す。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_tot"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["chi2_tot"]

    def get_chi2_set1(self, loop_index: Optional[int] = None):
        """
        χ2/F(Q)_set#1（第 1 データセットの χ²）を返す。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_set1"])
            return out

        if loop_index < 0 or loop_index >= len(self._records):
            return None

        return self._records[loop_index]["chi2_set1"]
