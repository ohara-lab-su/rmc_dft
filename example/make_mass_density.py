#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数密度から質量密度を計算する。"""

from packmol_util.config import Config
from packmol_util.packmol import Packmol
from x_logger import XLogger

logger = XLogger(logger_name=__name__)

# config = Config("config.yml", logger=logger)

config = Config(logger=logger)
config.element_info = ["Fe", "Si", "B"]
config.ratios = [82, 4, 14]
config.number_density_A3 = 0.09119

packmol = Packmol(logger=logger)

mass_density_g_cm3 = packmol.mass_density_from_number_density(
    config.element_info,
    config.ratios,
    config.number_density_A3,
)

print(f"symbols            = {config.element_info}")
print(f"ratios             = {config.ratios}")
print(f"number_density_A3  = {config.number_density_A3:.10f}")
print(f"mass_density_g_cm3 = {mass_density_g_cm3:.10f}")
