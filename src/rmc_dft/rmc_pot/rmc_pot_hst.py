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
        hst_path: str,
        config: Config = Config(),
        logger: Optional[XLogger] = None,
    ) -> None:
        """

        Args:
            hst_path (str):  cfg_name
            config (Config):
            logger (XLogger):
        """
        self._logger: Optional[XLogger] = logger or XLogger(logger_name="RmcPotFit")
        self._config: Config = config
        self._hst_path: Optional[str] = hst_path or config.cfg_name

    def read_chi2(self) -> Union[Tuple[List[int], List[float]], bool]:
        """
        hst ファイルから step と chi2_tot/data_point のリストを返す。

        Returns:
            steps (List[int]): step 数
            chi2  (List[float]): χ2_tot/data_point
        """
        steps: List[int] = []
        chi2: List[float] = []

        try:
            with open(self._hst_path, "r") as f:
                for line in f:
                    items = line.strip().split()
                    # 数値行は 8 列以上あり、先頭が整数（step）
                    if len(items) >= 8 and items[0].isdigit():
                        step_val = int(items[0])
                        chi_val = float(items[6])  # 7列目
                        steps.append(step_val)
                        chi2.append(chi_val)
        except FileNotFoundError:
            # HST がない、からデーターとして扱う
            self._logger.warning(f"HST file not found: {self._hst_path}")
            return False

        return steps, chi2
