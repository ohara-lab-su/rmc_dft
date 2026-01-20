#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
packmol でつくることができるセルサイズを化学量論比から算出する
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from typing import List
from rmc_dft import Config, Packmol

from x_logger import XLogger


if __name__ == "__main__":

    logger = XLogger(log_level="debug")
    # config = Config("config.yml")
    # ratios: Sequence[int] = config.ratios

    ratios = [82, 4, 14]  # 化学量論比
    max_atom_count: int = 1000

    pm = Packmol()

    unit_count: int = pm.get_unit_atom_count(ratios)
    cell_sizes: List[int] = pm.compute_cell_sizes(ratios, max_atom_count)

    # logger.info(f"化学量論比 = {ratios}")
    # logger.info(f"1ユニット原子数 = {unit_count}")
    # print("生成可能なセル原子数:")
    # for size in cell_sizes:
    #     print(size)
