#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import numpy as np
import matplotlib.pyplot as plt
from rmc_dft import VaspOutcar


def main() -> None:
    out = VaspOutcar("OUTCAR")

    # VaspOutcar 側でフラット化した配列をもらう
    # 例: without entropy 基準のエネルギー
    energies = out.get_energy_flat()  # np.ndarray, shape = (N,)

    x = np.arange(energies.size, dtype=int)

    plt.plot(x, energies)
    plt.xlabel("SCF step (flattened ion × iter)")
    plt.ylabel("Energy (without entropy) [eV]")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
