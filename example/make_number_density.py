#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from x_logger import XLogger
from make_amorphous import Packmol


def main() -> None:
    logger = XLogger()

    # ----------------------------------
    # 入力パラメータ
    # ----------------------------------
    symbols = ["Fe", "Si", "B"]
    ratios = [80, 9, 11]  # Fe80Si9B11
    mass_density_g_cm3 = 7.3  # 質量密度 [g/cm^3]
    N_tot = 2000  # 総原子数

    packmol = Packmol(logger=logger)

    # ----------------------------------
    # 質量密度 → 数密度
    # ----------------------------------
    number_density_A3 = packmol.number_density_from_mass_density(
        symbols=symbols,
        ratios=ratios,
        mass_density_g_cm3=mass_density_g_cm3,
    )

    logger.info(f"number density n = {number_density_A3:.6e} [1/Å^3]")

    # ----------------------------------
    # 数密度 → セル一辺長
    # ----------------------------------
    L = packmol.cell_length_from_number_density(
        N_tot=N_tot,
        number_density_A3=number_density_A3,
    )

    logger.info(f"cell length L = {L:.6f} [Å]")

    # ----------------------------------
    # 各元素の原子数
    # ----------------------------------
    element_counts = packmol.compute_element_counts(
        symbols=symbols,
        ratios=ratios,
        N_tot=N_tot,
    )

    logger.info("element counts:")
    for elem, count in element_counts.items():
        logger.info(f"  {elem}: {count}")


if __name__ == "__main__":
    main()
