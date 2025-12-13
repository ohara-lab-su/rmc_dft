#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import re

from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotHst:
    """
    RMC_POT の .hst ファイルを読み取り、
    各ステップごとの χ2_tot/data_point（7列目）を取得するクラス。
    """

    def __init__(
        self,
        hst_path: Optional[str] = None,
        config: Optional[Config] = None,  # Config(),
        logger: Optional[XLogger] = None,
    ) -> None:
        """

        Args:
            hst_path (str):  cfg_name
            config (Config):
            logger (XLogger):
        """
        self._logger: Optional[XLogger] = logger or XLogger(logger_name="RmcPotFit")
        self._config: Optional[Config] = config or Config()
        self._hst_path: Optional[str] = hst_path or self._config.cfg_name

        self._lines: List[str] = []
        self._parsed: bool = False

        # パース後のキャッシュ
        self._steps: List[int] = []
        self._generated: List[int] = []
        self._tried: List[int] = []
        self._accepted: List[int] = []
        self._chi2: List[float] = []

        self._load_file()
        self._parse()

    # def read_chi2(self) -> Union[Tuple[List[int], List[float]], bool]:
    #     """
    #     hst ファイルから step と chi2_tot/data_point のリストを返す。

    #     Returns:
    #         steps (List[int]): step 数
    #         chi2  (List[float]): χ2_tot/data_point
    #     """
    #     steps: List[int] = []
    #     chi2: List[float] = []

    #     try:
    #         with open(self._hst_path, "r") as f:
    #             for line in f:
    #                 items = line.strip().split()
    #                 # 数値行は 8 列以上あり、先頭が整数（step）
    #                 if len(items) >= 8 and items[0].isdigit():
    #                     step_val = int(items[0])
    #                     chi_val = float(items[6])  # 7列目
    #                     steps.append(step_val)
    #                     chi2.append(chi_val)
    #     except FileNotFoundError:
    #         # HST がない、からデーターとして扱う
    #         self._logger.warning(f"HST file not found: {self._hst_path}")
    #         return False

    #     return steps, chi2

    # --------------------------------------------------------------
    # ファイル読み込み
    # --------------------------------------------------------------
    def _load_file(self) -> None:
        try:
            with open(self._hst_path, "r") as f:
                self._lines = f.readlines()
            self._logger.info(f"Loaded HST file: {self._hst_path}")
        except FileNotFoundError:
            self._logger.warning(f"HST file not found: {self._hst_path}")
            self._lines = []

    # --------------------------------------------------------------
    # パース（最初の一回のみ）
    # --------------------------------------------------------------
    def _parse(self) -> None:
        if self._parsed:
            return

        for line in self._lines:
            items = line.strip().split()
            if len(items) < 8:
                continue
            if not items[0].isdigit():
                continue

            try:
                step = int(items[0])
                gen = int(items[1])
                tried = int(items[2])
                acc = int(items[3])
                chi = float(items[6])

                self._steps.append(step)
                self._generated.append(gen)
                self._tried.append(tried)
                self._accepted.append(acc)
                self._chi2.append(chi)

            except Exception:
                continue

        self._parsed = True

    # --------------------------------------------------------------
    # 既存互換 API
    # --------------------------------------------------------------
    def read_chi2(self) -> Tuple[List[int], List[float]]:
        return self._steps, self._chi2

    # --------------------------------------------------------------
    # ユーザー API（正式）
    # --------------------------------------------------------------
    def get_num_steps(self) -> int:
        return len(self._steps)

    def get_steps(self) -> List[int]:
        return self._steps

    def get_chi2(self) -> List[float]:
        return self._chi2

    def get_generated(self) -> List[int]:
        return self._generated

    def get_tried(self) -> List[int]:
        return self._tried

    def get_accepted(self) -> List[int]:
        return self._accepted

    def get_acceptance_ratio(self) -> List[float]:
        ratio = []
        for t, a in zip(self._tried, self._accepted):
            if t > 0:
                ratio.append(a / t)
            else:
                ratio.append(0.0)
        return ratio
