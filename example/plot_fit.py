#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rmc_dft import RmcPotFit


def plot_sq(fitfile: str) -> None:
    """
    .fit ファイルを読み取り、
    計算 S(Q) と 実験 S(Q) を 1 枚の図として描画する。
    """

    fit = RmcFitData(fitfile)

    Q = fit.Q
    S_calc = fit.get_S_calc()
    S_exp = fit.get_S_exp()

    plt.figure(figsize=(8, 5))
    plt.plot(Q, S_calc, label="S_calc (RMC)", linewidth=2)
    plt.plot(Q, S_exp, label="S_exp (renormalized)", linewidth=2)

    plt.xlabel("Q (1/Å)")
    plt.ylabel("S(Q)")
    plt.title(f"Comparison of S(Q): {fitfile}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 例: python plot_sq.py aaa.fit
    import sys

    if len(sys.argv) != 2:
        print("Usage: python plot_sq.py <fitfile>")
        sys.exit(1)

    _fitfile = sys.argv[1]
    plot_sq(_fitfile)
