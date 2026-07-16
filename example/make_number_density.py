#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""質量密度から数密度を計算する。"""

from packmol_util.config import Config
from packmol_util.packmol import Packmol
from x_logger import XLogger

logger = XLogger(logger_name=__name__)

# config = Config("config.yml", logger=logger)

config = Config(logger=logger)
# config.element_info = ["Fe", "Si", "B"]
# config.ratios = [82, 4, 14]
config.element_info = ["Si", "O"]
config.ratios = [1, 2]
config.mass_density_g_cm3 = 2.214  # SiO2製法A: S1
# config.mass_density_g_cm3 = 2.277 # SiO2製法B: S2
# config.mass_density_g_cm3 = 2.113 # SiO2製法C: S7

packmol = Packmol(logger=logger)

number_density_A3 = packmol.number_density_from_mass_density(
    config.element_info,
    config.ratios,
    config.mass_density_g_cm3,
)

print(f"symbols            = {config.element_info}")
print(f"ratios             = {config.ratios}")
print(f"mass_density_g_cm3 = {config.mass_density_g_cm3:.10f}")
print(f"number_density_A3  = {number_density_A3:.10f}")
