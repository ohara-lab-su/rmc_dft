#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import re
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import numpy as np
from x_logger import XLogger


class VaspOutcar:
    """
    VASP OUTCAR から
      - エネルギー (free, without entropy, sigma->0)
      - 原子位置
      - 力
      - 原子ごとの磁気モーメント (s, p, d, total)
      - 全体の磁気モーメント (total)
    を取り出して保持するクラス。

    イオンステップの配列長は (NSW + 1) とする:
      NSW = 0 -> ステップ 0 のみ (要素数 1)
      NSW = 1 -> ステップ 0,1    (要素数 2)
      一般に -> ステップ 0..NSW (要素数 NSW+1)
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename

        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            self.lines = f.readlines()

        self.nsw: int = self._read_int("NSW", default=0)
        self.nelm: int = self._read_int("NELM", default=60)
        self.nions: int = self._read_int("NIONS", default=0)

        # イオンステップ数 = NSW + 1
        self.num_ion_steps: int = self.nsw + 1
        if self.num_ion_steps < 1:
            self.num_ion_steps = 1

        if self.nions <= 0:
            self.nions = self._guess_nions()

        # エネルギー配列: (ion_step, iter)
        shape_energy = (self.num_ion_steps, self.nelm)
        self.energy_toten: np.ndarray = np.full(shape_energy, np.nan, dtype=float)
        self.energy_e0: np.ndarray = np.full(shape_energy, np.nan, dtype=float)
        self.energy_sigma0: np.ndarray = np.full(shape_energy, np.nan, dtype=float)
        self.iter_count: np.ndarray = np.zeros(self.num_ion_steps, dtype=int)

        # 位置・力: (ion_step, ion_index, xyz)
        shape_pos = (self.num_ion_steps, self.nions, 3)
        self.positions: np.ndarray = np.full(shape_pos, np.nan, dtype=float)
        self.forces: np.ndarray = np.full(shape_pos, np.nan, dtype=float)

        # 磁気モーメント: (ion_step, ion_index, (s,p,d,total))
        shape_mag = (self.num_ion_steps, self.nions, 4)
        self.magmom_atom: np.ndarray = np.full(shape_mag, np.nan, dtype=float)
        # 全体の磁気モーメント: (ion_step,)
        self.magmom_total: np.ndarray = np.full(self.num_ion_steps, np.nan, dtype=float)

        # 実際に検出できたイオンステップ数（後で更新）
        self.actual_ion_steps: int = 0

        self._parse_energy()
        self._parse_pos_force()
        self._parse_magmom()
        self._shrink_ion_steps()

    # =========================================================
    # 内部ヘルパ
    # =========================================================
    def _read_int(self, key: str, default: int = 0) -> int:
        pattern = rf"\b{key}\s*=\s*(\d+)"
        for line in self.lines:
            m = re.search(pattern, line)
            if m:
                return int(m.group(1))
        return default

    def _guess_nions(self) -> int:
        """
        NIONS 行が見つからない場合のフォールバック: 最初の
        POSITION TOTAL-FORCE ブロックから原子数を推定する。
        """
        reading: bool = False
        count: int = 0

        for line in self.lines:
            if "POSITION" in line and "TOTAL-FORCE" in line:
                reading = True
                count = 0
                continue

            if reading:
                if "drift" in line or "--------" in line:
                    # ブロック終端
                    break
                parts = line.split()
                if len(parts) >= 6:
                    # x y z fx fy fz の行
                    count += 1

        return count

    # =========================================================
    # エネルギーのパース
    # =========================================================
    def _parse_energy(self) -> None:
        """
        "FREE ENERGIE OF THE ION-ELECTRON SYSTEM" ブロックから
        free energy (TOTEN), without entropy, sigma->0 を取り出す。
        """
        ion_index: int = -1
        iter_index: int = 0

        for line in self.lines:
            if "FREE ENERGIE OF THE ION-ELECTRON SYSTEM" in line:
                ion_index += 1
                iter_index = 0
                continue

            if ion_index < 0 or ion_index >= self.num_ion_steps:
                continue

            m_toten = re.search(r"free\s+energy\s+TOTEN\s*=\s*([-\d\.Ee+]+)", line)
            if m_toten:
                if iter_index < self.nelm:
                    self.energy_toten[ion_index, iter_index] = float(m_toten.group(1))
                continue

            m_e0 = re.search(r"energy\s+without entropy=\s*([-\d\.Ee+]+)", line)
            if m_e0:
                if iter_index < self.nelm:
                    self.energy_e0[ion_index, iter_index] = float(m_e0.group(1))
                continue

            m_sigma = re.search(r"energy\(sigma->0\)\s*=\s*([-\d\.Ee+]+)", line)
            if m_sigma:
                if iter_index < self.nelm:
                    self.energy_sigma0[ion_index, iter_index] = float(m_sigma.group(1))
                iter_index += 1
                if iter_index > self.iter_count[ion_index]:
                    self.iter_count[ion_index] = iter_index
                continue

        # エネルギーブロックから見た実際のイオンステップ数
        if ion_index >= 0:
            self.actual_ion_steps = max(self.actual_ion_steps, ion_index + 1)

    # =========================================================
    # 位置・力のパース
    # =========================================================
    def _parse_pos_force(self) -> None:
        """
        "POSITION" "TOTAL-FORCE" ブロックから
        位置と力を取り出す。
        """
        ion_index: int = -1
        atom_index: int = 0
        reading: bool = False

        for line in self.lines:
            if "POSITION" in line and "TOTAL-FORCE" in line:
                ion_index += 1
                if ion_index >= self.num_ion_steps:
                    reading = False
                    continue
                atom_index = 0
                reading = True
                continue

            if not reading:
                continue

            if "drift" in line or "--------" in line:
                reading = False
                if ion_index >= 0:
                    self.actual_ion_steps = max(self.actual_ion_steps, ion_index + 1)
                continue

            parts = line.split()
            if len(parts) < 6:
                continue

            if atom_index >= self.nions:
                continue

            try:
                x, y, z = map(float, parts[0:3])
                fx, fy, fz = map(float, parts[3:6])
            except Exception:
                continue

            self.positions[ion_index, atom_index, :] = (x, y, z)
            self.forces[ion_index, atom_index, :] = (fx, fy, fz)
            atom_index += 1

    # =========================================================
    # 磁気モーメントのパース
    # =========================================================
    def _parse_magmom(self) -> None:
        """
        "magnetization (x)" ブロックから
        原子ごとの (s, p, d, total) と
        total magnetization を取り出す。
        """
        ion_index: int = -1
        atom_index: int = 0
        reading: bool = False

        for line in self.lines:
            if "magnetization (x)" in line:
                ion_index += 1
                if ion_index >= self.num_ion_steps:
                    reading = False
                    continue
                atom_index = 0
                reading = True
                continue

            if not reading:
                continue

            parts = line.split()

            # 原子ごとの行: "1  s  p  d  tot"
            if len(parts) == 5 and parts[0].isdigit():
                if atom_index < self.nions:
                    try:
                        s_val = float(parts[1])
                        p_val = float(parts[2])
                        d_val = float(parts[3])
                        t_val = float(parts[4])
                    except Exception:
                        atom_index += 1
                        continue
                    self.magmom_atom[ion_index, atom_index, :] = (
                        s_val,
                        p_val,
                        d_val,
                        t_val,
                    )
                atom_index += 1
                continue

            # total magnetization
            if "total magnetization" in line:
                m_tot = re.search(r"total magnetization\s*=\s*([-\d\.Ee+]+)", line)
                if m_tot:
                    try:
                        val = float(m_tot.group(1))
                        self.magmom_total[ion_index] = val
                        self.actual_ion_steps = max(
                            self.actual_ion_steps, ion_index + 1
                        )
                    except Exception:
                        pass
                reading = False

    # =========================================================
    # 実際のイオンステップ数でスライス
    # =========================================================
    def _shrink_ion_steps(self) -> None:
        """
        実際に検出できたイオンステップ数まで配列を切り詰める。
        NSW=0 の場合も最低 1 にする。
        """
        if self.actual_ion_steps <= 0:
            self.actual_ion_steps = 1
        if self.actual_ion_steps > self.num_ion_steps:
            self.actual_ion_steps = self.num_ion_steps

        used: int = self.actual_ion_steps

        if used < self.num_ion_steps:
            self.energy_toten = self.energy_toten[:used, :]
            self.energy_e0 = self.energy_e0[:used, :]
            self.energy_sigma0 = self.energy_sigma0[:used, :]
            self.iter_count = self.iter_count[:used]
            self.positions = self.positions[:used, :, :]
            self.forces = self.forces[:used, :, :]
            self.magmom_atom = self.magmom_atom[:used, :, :]
            self.magmom_total = self.magmom_total[:used]

        self.num_ion_steps = used

    # =========================================================
    # 公開 API
    # =========================================================
    def get_ionstep_count(self) -> int:
        return self.num_ion_steps

    def get_iter_count(self, ionstep: int) -> int:
        if ionstep < 0 or ionstep >= self.num_ion_steps:
            return 0
        return int(self.iter_count[ionstep])

    def get_energy(
        self,
        ionstep: int,
        iterstep: int,
        *,
        mode: str = "e0",
    ) -> Optional[float]:
        """
        指定イオンステップ・指定 iter のエネルギーを返す。

        mode:
            "e0"     : energy without entropy
            "toten"  : free energy TOTEN
            "sigma0" : energy(sigma->0)
        """
        if (
            ionstep < 0
            or ionstep >= self.num_ion_steps
            or iterstep < 0
            or iterstep >= self.iter_count[ionstep]
        ):
            return None

        if mode == "e0":
            val = self.energy_e0[ionstep, iterstep]
        elif mode == "toten":
            val = self.energy_toten[ionstep, iterstep]
        elif mode == "sigma0":
            val = self.energy_sigma0[ionstep, iterstep]
        else:
            val = self.energy_e0[ionstep, iterstep]

        if np.isnan(val):
            return None
        return float(val)

    def get_energy_matrix(self, mode: str = "e0") -> np.ndarray:
        """
        イオンステップ × iter のエネルギー配列を返す。
        未使用部分は NaN を含む。
        """
        if self.num_ion_steps == 0:
            return np.empty((0, 0), dtype=float)

        max_iter: int = int(self.iter_count.max()) if self.iter_count.size > 0 else 0
        if max_iter <= 0:
            return np.empty((self.num_ion_steps, 0), dtype=float)

        if mode == "e0":
            mat = self.energy_e0[:, :max_iter]
        elif mode == "toten":
            mat = self.energy_toten[:, :max_iter]
        elif mode == "sigma0":
            mat = self.energy_sigma0[:, :max_iter]
        else:
            mat = self.energy_e0[:, :max_iter]

        return mat.copy()

    def get_energy_flat(self, mode: str = "e0") -> np.ndarray:
        """
        イオンステップと iter をすべてまとめた 1 次元配列を返す。
        NaN は除く。
        """
        mat = self.get_energy_matrix(mode=mode)
        return mat[~np.isnan(mat)]

    def get_energy_ionstep(self, mode: str = "e0") -> np.ndarray:
        """
        各イオンステップごとの「最後の iter のエネルギー」を
        1 次元配列で返す。
        """
        if self.num_ion_steps == 0:
            return np.empty(0, dtype=float)

        vals = np.full(self.num_ion_steps, np.nan, dtype=float)

        for ion in range(self.num_ion_steps):
            n_iter = int(self.iter_count[ion])
            if n_iter <= 0:
                continue
            idx = n_iter - 1

            if mode == "e0":
                vals[ion] = self.energy_e0[ion, idx]
            elif mode == "toten":
                vals[ion] = self.energy_toten[ion, idx]
            elif mode == "sigma0":
                vals[ion] = self.energy_sigma0[ion, idx]
            else:
                vals[ion] = self.energy_e0[ion, idx]

        return vals

    def get_positions(self, ionstep: int) -> np.ndarray:
        """
        指定イオンステップの原子位置 (nions, 3) を返す。
        """
        if ionstep < 0 or ionstep >= self.num_ion_steps:
            return np.empty((0, 3), dtype=float)
        return self.positions[ionstep].copy()

    def get_forces(self, ionstep: int) -> np.ndarray:
        """
        指定イオンステップの力 (nions, 3) を返す。
        """
        if ionstep < 0 or ionstep >= self.num_ion_steps:
            return np.empty((0, 3), dtype=float)
        return self.forces[ionstep].copy()

    def get_magmom_atom(self, ionstep: int) -> np.ndarray:
        """
        指定イオンステップの原子ごとの磁気モーメント
        (nions, 4) を返す。列順は (s, p, d, total)。
        """
        if ionstep < 0 or ionstep >= self.num_ion_steps:
            return np.empty((0, 4), dtype=float)
        return self.magmom_atom[ionstep].copy()

    def get_magmom_total(self, ionstep: int) -> Optional[float]:
        """
        指定イオンステップの全体磁気モーメント total を返す。
        """
        if ionstep < 0 or ionstep >= self.num_ion_steps:
            return None
        val = self.magmom_total[ionstep]
        if np.isnan(val):
            return None
        return float(val)
