#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Tuple


class RmcPotHst:
    """
    RMC_POT の .hst ファイルを読み取り、
    各ステップごとの χ2_tot/data_point（7列目）を取得するクラス。
    """

    def __init__(self, hst_path: str) -> None:
        self.hst_path: str = hst_path

    def read_chi2(self) -> Tuple[List[int], List[float]]:
        """
        hst ファイルから step と chi2_tot/data_point のリストを返す。

        Returns:
            steps (List[int]): step 数
            chi2  (List[float]): χ2_tot/data_point
        """
        steps: List[int] = []
        chi2: List[float] = []

        with open(self.hst_path, "r") as f:
            for line in f:
                items = line.strip().split()
                # 数値行は 8 列以上あり、先頭が整数（step）
                if len(items) >= 8 and items[0].isdigit():
                    step_val = int(items[0])
                    chi_val = float(items[6])  # 7列目
                    steps.append(step_val)
                    chi2.append(chi_val)

        return steps, chi2
