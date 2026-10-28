"""
K.NAKADA, kengo.nakada@gmail.com
"""

import sys
import importlib

from rmc_util.rmc_pot import RmcPot
from rmc_util.rmc_pot_dat import RmcPotDat
from rmc_util.rmc_pot_dat_fixed import RmcPotDatFixed
from rmc_util.rmc_pot_dat_free import RmcPotDatFree
from rmc_util.rmc_pot_log import RmcPotLog
from rmc_util.rmc_pot_fit import RmcPotFit
from rmc_util.rmc_pot_hst import RmcPotHst
from rmc_util.rmc_pot_ppcf import RmcPotPpcf

modules = [
    "rmc_pot",
    "rmc_pot_dat",
    "rmc_pot_dat_fixed",
    "rmc_pot_dat_fnc",
    "rmc_pot_dat_free",
    "rmc_pot_dat_top",
    "rmc_pot_fit",
    "rmc_pot_hst",
    "rmc_pot_log",
    "rmc_pot_ppcf",
    "rmc_pot_snc",
]

# for name in modules:
#    module = importlib.import_module("rmc_util." + name)
#    sys.modules[__name__ + "." + name] = module
