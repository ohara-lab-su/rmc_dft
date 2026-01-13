#!/usr/bin/env python
from typing import Optional
from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_hst import RmcPotHst

from x_logger import XLogger


def main() -> None:
    logger = XLogger(logger_name="RMC_CONVERGENCE")

    # HST 読み込み（cfg_name または hst_name を指定）
    hst = RmcPotHst(cfg_name="sample")  # sample.cfg → sample.hst

    # 収束判定
    loop: Optional[int] = hst.detect_convergence(
        rel_tol=1.0e-2,
        acc_tol=1.0e-3,
        min_consecutive=2,
    )

    if loop is None:
        logger.info("RMC is NOT converged.")
        return

    # 収束点の情報を取得
    generated = hst.get_generated(loop)
    chi2_tot = hst.get_chi2_tot(loop)
    chi2_set1 = hst.get_chi2_set1(loop)
    acc = hst.get_accepted_per_tried(loop)

    logger.info("RMC is converged.")
    logger.info(f"  loop index           = {loop}")
    logger.info(f"  generated            = {generated}")
    logger.info(f"  chi2_tot             = {chi2_tot:.6e}")
    logger.info(f"  chi2/F(Q)_set#1      = {chi2_set1:.6e}")
    logger.info(f"  accepted/tried       = {acc:.6e}")


if __name__ == "__main__":
    main()
