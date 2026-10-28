# from rmc_dft.rmc_pot.util.cfg2poscar import cfg2poscar
import importlib
import sys

modules = [
    "cfg2poscar",
    "gromacs_top_to_rmc_top",
    "zeolite",
]

for name in modules:
    module = importlib.import_module("rmc_util.util." + name)
    sys.modules[__name__ + "." + name] = module
