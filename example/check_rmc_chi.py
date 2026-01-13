#!/usr/bin/env python
from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_hst import RmcPotHst

hst = RmcPotHst(cfg_name="aaa")
chi2 = hst.get_chi2_tot()


chi2_last = hst.get_chi2_tot()[-1]

print("final chi2_tot =", chi2_last)

# 例：しきい値判定
threshold = 1.0e-3  # 適宜決める
if chi2_last < threshold:
    print("RMC finished -> go to DFT")
