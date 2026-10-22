"""周期結晶セルの汎用幾何操作。格子ベクトルは3x3行列の行に格納する。

POSCARの読み込みは既存の rmc_dft.vasp.vasp_poscar.VaspPoscar を使用する。
本モジュールはファイル入出力やRMC/ænet固有の構造生成を行わない。
最短画像は整数格子シフトを列挙して直交座標ノルムで判定する。
"""

from itertools import product
from typing import Tuple
import numpy as np


def _lattice(
    cell: np.ndarray,
) -> np.ndarray:
    """格子行列を検査し、float64の3x3行列として返す。"""
    lattice = np.asarray(cell, dtype=float)
    if lattice.shape != (3, 3):
        raise ValueError("cell must be a 3x3 matrix")
    if abs(float(np.linalg.det(lattice))) < 1.0e-12:
        raise ValueError("cell is singular")
    return lattice


def cell_volume(cell: np.ndarray) -> float:
    """周期セルの体積を返す（格子がÅならÅ³）。"""
    return abs(float(np.linalg.det(_lattice(cell))))


def direct_to_cartesian(
    coords: np.ndarray,
    cell: np.ndarray,
) -> np.ndarray:
    """分率座標 (...,3) を直交座標へ変換する。"""
    return np.asarray(coords, dtype=float) @ _lattice(cell)


def cartesian_to_direct(
    coords: np.ndarray,
    cell: np.ndarray,
) -> np.ndarray:
    """直交座標 (...,3) を分率座標へ変換する。"""
    return np.asarray(coords, dtype=float) @ np.linalg.inv(_lattice(cell))


def wrap_direct(
    coords: np.ndarray,
) -> np.ndarray:
    """分率座標を [0,1) に折り返す。入力は変更しない。"""
    return np.mod(np.asarray(coords, dtype=float), 1.0)


def wrap_cartesian(
    coords: np.ndarray,
    cell: np.ndarray,
) -> np.ndarray:
    """直交座標を周期セル内に折り返す。"""
    return direct_to_cartesian(wrap_direct(cartesian_to_direct(coords, cell)), cell)


def minimum_image_vector(
    a: np.ndarray,
    b: np.ndarray,
    cell: np.ndarray,
    search_radius: int = 1,
) -> np.ndarray:
    """aからbへの最短周期変位（直交座標、Å）を返す。

    分率差を最近整数で中心化した後、[-search_radius,+search_radius]^3
    の画像を探索する。強く歪んだセルでは探索範囲の拡大が必要。
    """
    if search_radius < 0:
        raise ValueError("search_radius must be nonnegative")
    lattice = _lattice(cell)
    delta = cartesian_to_direct(
        np.asarray(b, dtype=float) - np.asarray(a, dtype=float), lattice
    )
    if delta.shape != (3,):
        raise ValueError("a and b must be 3-vectors")
    delta = delta - np.round(delta)
    best = None
    best_squared = float("inf")
    for shift in product(range(-search_radius, search_radius + 1), repeat=3):
        vec = (delta + np.asarray(shift, dtype=float)) @ lattice
        squared = float(vec @ vec)
        if squared < best_squared:
            best = vec
            best_squared = squared
    assert best is not None
    return best


def periodic_distance(
    a: np.ndarray,
    b: np.ndarray,
    cell: np.ndarray,
    search_radius: int = 1,
) -> float:
    """2点の周期最短距離（Å）。"""
    return float(np.linalg.norm(minimum_image_vector(a, b, cell, search_radius)))
