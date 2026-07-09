import math
from typing import List
from typing import Optional

import numpy as np

from rmc_dft.rmc_pot.qn.config_error import ConfigError


class VaspStructure(object):
    """VASP/POSCAR 構造データと PBC 幾何計算を保持するクラス。"""

    def __init__(self, labels: List[str], cell: np.ndarray, frac: np.ndarray) -> None:
        self.labels = labels
        self.cell = cell
        self.frac = frac

    @property
    def atom_count(self) -> int:
        return len(self.labels)

    def pbc_vector(self, i: int, j: int) -> np.ndarray:
        """i -> j の minimum-image vector を Angstrom 単位で返す。"""
        delta = self.frac[j] - self.frac[i]
        delta -= np.round(delta)
        return np.dot(delta, self.cell)

    def pbc_distance(self, i: int, j: int) -> float:
        """i-j の PBC 距離を Angstrom 単位で返す。"""
        return float(np.linalg.norm(self.pbc_vector(i, j)))

    def angle_degree(self, i: int, j: int, k: int) -> float:
        """i-j-k の角度を degree で返す。"""
        v1 = self.pbc_vector(j, i)
        v2 = self.pbc_vector(j, k)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        cosang = float(np.dot(v1, v2) / (n1 * n2))
        cosang = max(-1.0, min(1.0, cosang))
        return math.degrees(math.acos(cosang))

    @staticmethod
    def read_poscar(
        path: str, atom_types_from_config: Optional[List[str]]
    ) -> "VaspStructure":
        """POSCAR/CONTCAR/VASP 形式の構造ファイルを読む。

        VASP5 形式のように元素名行がある場合は、その元素名行を使う。
        VASP4 形式のように元素名行がなく個数行だけの場合は、
        JSON 設定の ``atom_types`` を ``atom_types_from_config`` として渡す。

        Args:
            path: POSCAR/CONTCAR/VASP ファイル名。
            atom_types_from_config: 元素名行がない場合に使う atom type 順。

        Returns:
            VaspStructure: 原子ラベル、格子、fractional coordinate。

        Raises:
            ConfigError: POSCAR として読めない、または atom type 数が一致しない場合。
        """
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        lines = []
        for line in raw_lines:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)

        if len(lines) < 8:
            raise ConfigError("POSCAR/CONTCAR として行数が不足しています。")

        scale = float(lines[1].split()[0])
        cell_rows = []
        for i in range(2, 5):
            tokens = lines[i].split()
            if len(tokens) < 3:
                raise ConfigError("POSCAR の格子ベクトル行が 3 成分未満です。")
            row = []
            for token in tokens[:3]:
                row.append(float(token))
            cell_rows.append(row)
        cell = np.array(cell_rows, dtype=float) * scale

        # VASP5 形式では 6 行目に元素名、7 行目に原子数が来る。
        # VASP4 形式では 6 行目がそのまま原子数行になる。
        tokens5 = lines[5].split()
        has_symbol_line = True
        try:
            for token in tokens5:
                int(token)
            has_symbol_line = False
        except ValueError:
            has_symbol_line = True

        if has_symbol_line:
            atom_types = tokens5
            count_tokens = lines[6].split()
            coord_mode_index = 7
        else:
            if atom_types_from_config is None:
                raise ConfigError(
                    "元素名行がない POSCAR です。config の atom_types を指定してください。"
                )
            atom_types = atom_types_from_config
            count_tokens = tokens5
            coord_mode_index = 6

        counts = []
        for token in count_tokens:
            counts.append(int(token))

        if len(atom_types) != len(counts):
            raise ConfigError("atom_types の数と POSCAR の個数行の数が一致しません。")

        coord_mode = lines[coord_mode_index].lower()
        start = coord_mode_index + 1
        if coord_mode.startswith("s"):
            coord_mode = lines[coord_mode_index + 1].lower()
            start = coord_mode_index + 2

        if not coord_mode.startswith("d") and not coord_mode.startswith("c"):
            raise ConfigError(
                "POSCAR の座標形式は Direct または Cartesian である必要があります。"
            )

        total = sum(counts)
        if len(lines) < start + total:
            raise ConfigError("座標行の数が不足しています。")

        coords = []
        for i in range(total):
            tokens = lines[start + i].split()
            if len(tokens) < 3:
                raise ConfigError("POSCAR の座標行が 3 成分未満です。")
            row = []
            for token in tokens[:3]:
                row.append(float(token))
            coords.append(row)
        frac_or_cart = np.array(coords, dtype=float)

        # 内部処理は fractional coordinate に統一する。
        if coord_mode.startswith("d"):
            frac = frac_or_cart.copy()
        else:
            cart = frac_or_cart * scale
            inv_cell = np.linalg.inv(cell)
            frac = cart.dot(inv_cell)

        labels = []
        for atom_type, count in zip(atom_types, counts):
            for _ in range(count):
                labels.append(atom_type)

        frac = frac - np.floor(frac)
        return VaspStructure(labels, cell, frac)
