# -*- coding: utf-8 -*-
"""RMC_POT 用 FNC / Qn ネットワーク生成補助モジュール。

この package は、RMC_POT でネットワーク系を扱うための汎用前処理だけを持つ。
既存構造から central-bridge-second 型の Qn ネットワークを解析し、
FNC=3 用 ``*.fnc`` と FNC=4 用 GROMACS 型 topology を生成する。

ここには SiO2、B2O3、GeO2 などの系固有パラメータを置かない。
系固有の設定は ``example/fnc`` 以下の JSON に置く。

通常の入口は ``QnNetworkBuilder`` である。

Example:
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
