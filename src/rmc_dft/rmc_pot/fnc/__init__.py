# -*- coding: utf-8 -*-
"""RMC_POT の FNC / Qn ネットワーク生成補助モジュール。

この package には、RMC_POT でネットワーク系を扱うための前処理を置く。
具体的には、既存構造から central-bridge-second 型の Qn ネットワークを解析し、
FNC=3 用 ``*.fnc`` と FNC=4 用 GROMACS 型 topology を生成する。

設計方針
--------
この package は汎用機能だけを持つ。SiO2 固有の値は package 内に置かず、
``example/fnc/SiO2_03/qn_config_sio2.json`` のような外部設定に置く。
そのため、ここでは ``sio2.py`` や SiO2 用デフォルト設定を import しない。

主な入口
--------
``QnNetworkBuilder`` を使うのが通常の入口である。

例::

    from rmc_dft.rmc_pot.fnc import QnNetworkBuilder

    builder = QnNetworkBuilder.from_poscar(
        poscar_name="POSCAR",
        config_name="qn_config_sio2.json",
    )
    builder.write_all("SiO2_750_S1_nvt4")
"""

from .qn_network import ConfigError
from .qn_network import NetworkData
from .qn_network import PoscarData
from .qn_network import QnNetworkBuilder
from .qn_network import build_fnc3_pairs
from .qn_network import build_network
from .qn_network import collect_fnc3_ranges
from .qn_network import load_config
from .qn_network import read_poscar

__all__ = [
    "ConfigError",
    "NetworkData",
    "PoscarData",
    "QnNetworkBuilder",
    "build_fnc3_pairs",
    "build_network",
    "collect_fnc3_ranges",
    "load_config",
    "read_poscar",
]
