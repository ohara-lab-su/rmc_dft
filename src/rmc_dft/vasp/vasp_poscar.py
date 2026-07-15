#!/usr/bin/env python
"""
K.NAKADA
kengo.nakada@mat.shimane-u.ac.jp
kengo.nakada@gmail.com
"""

import os
import numpy as np
from typing import List, Tuple, Optional, Any


class VaspPoscar:
    """
    VASP POSCARファイルの解析を行うクラス。

    疑似プライベート化された内部変数値は 0-base
    getter でアクセスさせる外部 I/F は 1-base
    """

    def __init__(
        self,
        poscar_path: str,
        verbose: bool = False,
    ) -> None:
        """
        POSCARAnalyzerの初期化。

        Args:
            poscar_path (str): POSCARファイルのパス。
        """
        self._filename: str = poscar_path

        # 基本並進ベクトル
        # 内部 array そのまま
        self._lattice: Optional[np.ndarray] = None

        # 各原子の種類のリスト [Li, Li, Li, P, P, S,,,]など
        # Liが3つでPが2つならば、Li,Li,Li,P,P と入る
        self._atom_indices: List[str] = []

        # 内部座標(必ずDirectが入る, 変換していれる)
        self._coords_direct: Optional[np.ndarray] = None

        # 原子種のインデック番号(1から）を返す
        self._element_site_indices: dict = {}

        # poscar 読み込み
        self._read_poscar()

    def _read_poscar(self) -> None:
        """
        POSCARファイルを読み込んで構造情報を初期化する。
        """
        with open(self._filename, "r") as f:
            lines = f.readlines()

        # label
        self._label: str = lines[0]

        # scale factor
        self._scale: float = float(lines[1].strip())

        # lattice parameter (scale factor を掛けたもの)
        self._lattice: np.array = np.array(
            [[float(x) for x in lines[i].split()] for i in range(2, 5)]
        )
        self._lattice *= self._scale  # ここでスケールを掛け算

        # element (VASP5以上ならば必ず存在する)
        # 元素記号のリスト
        self._elements: List[str] = [
            element.split("/", 1)[0] for element in lines[5].split()
        ]

        # atomic number
        self._elements_index = list(map(int, lines[6].split()))
        total_atoms = sum(self._elements_index)

        # Cartesian or Direct
        coord_mode_line: str = lines[7].strip().lower()
        if coord_mode_line.startswith("s"):
            coord_mode = lines[8].strip().lower()
            coord_start_line = 9
        else:
            coord_mode = coord_mode_line
            coord_start_line = 8

        coord_lines = lines[coord_start_line : coord_start_line + total_atoms]

        # 内部座標を保持
        coords = np.array(
            [[float(x) for x in line.split()[:3]] for line in coord_lines]
        )

        # 記録されている内部座標がどのモードなのか？ Direct ならば True
        self._is_direct = coord_mode.startswith("d")

        # direct 変換
        if not self._is_direct:
            inv_lattice = np.linalg.inv(self._lattice)
            coords = coords @ inv_lattice

        # (注意) 内部座標は Direct で記録される
        self._coords_direct = coords

        self._atom_indices = []
        self._element_site_indices = {}

        idx = 0
        for element, count in zip(self._elements, self._elements_index):
            self._element_site_indices[element] = []
            for i in range(count):
                self._atom_indices.append(element)
                self._element_site_indices[element].append(idx)
                idx += 1

    # @staticmethod
    # def apply_pbc_cartesian(vec, cell):
    #     """
    #     周期境界条件を適用して、格子ベクトル(位置ベクトル差) cartesian に
    #     基づく最近接の変位ベクトルを返す。

    #     vec = A-vector - B-vector (それぞれ周期境界条件を満たす)

    #     Args:
    #         vec (np.ndarray): cartesian 3次元の変位ベクトル
    #                           シミュレーションセル内の2つの原子（または点）の
    #                           位置ベクトルの差(r_j − r_i) を
    #                           デカルト座標（通常のx, y, z座標）で表したもの
    #         cell (np.ndarray): 3x3の格子ベクトル（列が a, b, c）

    #     Returns:
    #         np.ndarray: cartesian 周期境界条件を考慮した変位ベクトル
    #     """
    #     # 線形連立方程式 Ax=b を x について解く
    #     frac = np.linalg.solve(
    #         cell.T, vec
    #     )  # Cartesian 座標系の変位ベクトルを direct 座標系に変換

    #     frac -= np.round(frac)  # 周期境界条件

    #     return cell @ frac  # direct 座標系を cartesian 座標系に変換

    def apply_pbc_cartesian(self, vec):
        """
        cartesian に PBC 適応 --> cartesian With PBC

        周期境界条件を適用して、格子ベクトル(位置ベクトル差) cartesian に
        基づく最近接の変位ベクトルを返す。

        vec = A-vector - B-vector (それぞれ周期境界条件を満たす)

        Args:
            vec (np.ndarray): cartesian 3次元の変位ベクトル
                              シミュレーションセル内の2つの原子（または点）の
                              位置ベクトルの差(r_j − r_i) を
                              デカルト座標（通常のx, y, z座標）で表したもの

        Returns:
            np.ndarray: direct 周期境界条件を考慮した変位ベクトル
        """
        # 線形連立方程式 Ax=b を x について解く
        # Cartesian 座標系の変位ベクトルを direct 座標系に変換
        frac = np.linalg.solve(self._lattice.T, vec)
        frac -= np.round(frac)  # 周期境界条件
        return frac

    def apply_pbc_direct(self, vec):
        """
        direct --> direct with PBC

        direct 座標系(vec) を入力として、周期境界条件を適当
        """
        vec -= np.round(vec)  # 周期境界条件
        return vec  # direct with PBC

    def apply_pbc_shortest_direct_vector(self, vec_direct):
        """
        PBC補正を適用して最短距離ベクトルを取得する。

        Args:
            vec_direct (np.ndarray): フラクショナル座標系の差分ベクトル。

        Returns:
            np.ndarray: PBC適用後の最短距離ベクトル（direct 系）。
        """
        # 差分ベクトルに対してのみ round() を適用
        vec_direct -= np.round(vec_direct)

        min_dist = np.inf
        shortest_vec = vec_direct

        # print("\n=== PBC Vector Candidates ===")
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    shift = np.array([i, j, k])
                    shifted_vec = vec_direct + shift
                    dist = np.linalg.norm(shifted_vec)

                    # print(f"Shift: {shift}, Vec: {shifted_vec}, Norm: {dist:.3f}")
                    # 出力して確認
                    # print(
                    #    f"Shift:"
                    #    f"[{shift[0]:>3}"
                    #    f" {shift[1]:>3}"
                    #    f" {shift[2]:>3}]"
                    #    f", Vec: "
                    #    f"[{shifted_vec[0]:+11.8f},"
                    #    f" {shifted_vec[1]:+11.8f},"
                    #    f" {shifted_vec[2]:+11.8f}]"
                    #    f" Norm: {dist:.3f}"
                    # )

                    if dist < min_dist:
                        min_dist = dist
                        shortest_vec = shifted_vec

        # print(f"Selected Vector: {shortest_vec}, Norm: {min_dist:.3f}")
        return shortest_vec

    def get_shortest_pbc_direct_vector(
        self, A_direct: np.ndarray, B_direct: np.ndarray
    ):
        """
        direct
        PBCを考慮した最短距離ベクトルを計算する。

        Args:
            A_direct (np.ndarray): A点のフラクショナル座標。
            B_direct (np.ndarray): B点のフラクショナル座標。

        Returns:
            np.ndarray: direct系 PBC補正済みの最短距離ベクトル。
        """
        # フラクショナル座標での差分
        delta_direct = A_direct - B_direct

        # PBC補正（最短距離ベクトルを取得）
        delta_direct_pbc = self.apply_pbc_shortest_direct_vector(delta_direct)
        # print(f"PBC補正あり Delta direct = {delta_direct_pbc}")

        # デカルト座標に変換
        # delta_cartesian_pbc = self._lattice @ delta_direct_pbc
        # return delta_cartesian_pbc
        return delta_direct_pbc

    @property
    def is_direct(self) -> bool:
        """
        POSCARファイルの座標形式が Direct 形式かどうかを返す。

        Returns:
            bool: Direct形式ならば True、そうでなければ False
        """
        return self._is_direct

    def get_filename(self) -> str:
        """poscar name"""
        return self._filename

    def get_label(self) -> str:
        """コメント"""
        return self._label

    def get_comment(self) -> str:
        """コメント"""
        return self._label

    def get_lattice_constant(self) -> float:
        """格子定数(scale factor)を返す"""
        return self._scale

    def get_scale(self) -> float:
        return self._scale

    def get_inv_lattice(self):
        """scale も含めた"""
        return np.linalg.inv(self._lattice)

    def get_inv_lattice_vectors(self):
        """scale も含めた"""
        return np.linalg.inv(self._lattice)

    def get_lattice_vectors(self) -> np.ndarray:
        """
        格子ベクトルを返す。
        (scale factor が含んでいる前提)

        Returns:
            np.ndarray: 3×3の格子行列
        """
        return self._lattice

    def conv_direct_to_cartesian(self, direct_vec):
        """lattice には scale が入っている前提"""
        return direct_vec @ self._lattice

    def conv_cartesian_to_direct(self, cartesian_vec):
        """lattice には scale が入っている前提"""
        inv_lattice = np.linalg.inv(self._lattice)
        return cartesian_vec @ inv_lattice

    def get_elements(self):
        """POSCAR の元素記号の一行(POSCARの行そのまま)"""
        return self._elements

    def get_elements_index(self):
        """POSCAR の元素記号に対応するサイトない原子数の一覧(POSCARの行そのまま)"""
        return self._elements_index

    def get_atom_indices(self) -> List[str]:
        """原子種(Liが3つでPが2つならば、Li,Li,Li,P,P と入る)"""
        return self._atom_indices

    def get_num_atoms(self) -> int:
        """
        このPOSCAR内の全原子数を返す。

        注意:
            - この関数は原子の「個数（サイズ）」を返すものであり、インデックスではない。
            - Pythonの range() を使ってグローバルインデックスでループ処理を行う場合には、
              `range(1, poscar.get_num_atoms() + 1)` のように書いて末尾を含める必要がある。
            - これは range() の仕様によるものであり、1-based / 0-based の議論とは直接関係しない。

        Returns:
            int: 総原子数
        """
        return len(self._coords_direct)

    #
    # 内部座標系
    #

    def get_coords_direct(
        self, global_index: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        内部座標リスト（Direct座標）を返す。

        Args:
            global_index (int, optional): 1始まりのグローバルインデックス。None の場合は全体を返す。

        Returns:
            np.ndarray or Optional[np.ndarray]: 指定された原子の分数座標、または全体の配列
        """
        if global_index is None:
            return self._coords_direct
        else:
            return self._coords_direct[global_index - 1]

    def get_direct_position(self, global_idx) -> np.ndarray:
        """1base で得る"""
        return self.get_fractional_position(global_idx)

    def get_fractional_position(self, global_idx) -> np.ndarray:
        """
        指定したglobal indexに対応する分数座標を返す。

        Args:
            global_idx (int): グローバルインデックス(1から)
        Returns:
            np.ndarray: 分数座標 (3次元ベクトル)
        """
        # _coords_direct にはかならず変換されて direct 座標が入っている
        return self._coords_direct[global_idx - 1]

        # if self.is_direct:
        #     return self.coords_direct[global_idx]
        # else:
        #     # Cartesian座標 -> 分数座標へ変換
        #     inv_lattice = np.linalg.inv(self.lattice)
        #     return self.coords_direct[global_idx] @ inv_lattice

    def get_cartesian_position(self, global_index: int) -> np.ndarray:
        """
        指定したインデックスの原子の直交座標を返す。

        Args:
            global_index (int): 原子のグローバルインデックス（1始まり, 1-based）。

        Returns:
            np.ndarray: 直交座標 (Å)
        """
        # index is 1-based; adjust to 0-based for internal access
        return self._coords_direct[global_index - 1] @ self._lattice

    #
    # 内部座標 (site-index <--> global-index)
    #

    def get_local_index_by_global_index(self, global_idx: int) -> int:
        """
        グローバルインデックスから元素種ごとのローカルサイト番号（1始まり, 1-based）を返す。

        Args:
            global_idx (int): グローバルインデックス（1始まり）

        Returns:
            int: 元素種内のローカルインデックス（1始まり）
        """
        return self.get_element_site_indices_by_global_index(global_idx)

    def get_global_index(self, element: str, site_index: int) -> int:
        """
        指定した原子種とそのサイト番号から、グローバルインデックス（1始まり）を返す。

        Args:
            element (str): 原子種（例: "Li"）。
            site_index (int): 原子種内のサイト番号（1始まり, 1-based）。

        Returns:
            int: 全体の原子リストにおけるグローバルインデックス（1始まり, 1-based）。
        """
        # site_index is 1-based; adjust to 0-based for internal access
        return self._element_site_indices[element][site_index - 1] + 1

    #
    # element 情報(Li,P などの記号)
    #

    def get_element_by_global_index(self, global_idx: int) -> str:
        """
        グローバルインデックス（1始まり）から元素を返す。

        Args:
            global_idx (int): グローバルインデックス（1始まり）

        Returns:
            str: 元素記号（例: "Li", "P", "S"）
        """
        if global_idx < 1 or global_idx > len(self._atom_indices):
            raise IndexError(f"global_idx {global_idx} is out of bounds (1-based)")
        return self._atom_indices[global_idx - 1]

    def get_element_site_indices(self, element: str) -> List[int]:
        """
        指定された元素に対応するサイトインデックス（1始まり, 1-based）を返す。

        Args:
            element (str): 原子種（例: "Li"）

        Returns:
            list[int]: 指定原子種に対応する原子サイトのインデックス（1始まり, 1-based）
        """
        # print(
        #     f"[DEBUG] _elements[:20] = {self._elements[:20]} ... total = {len(self._elements)}"
        # )
        return [
            i + 1
            for i, e in enumerate(self._atom_indices)
            if e.strip().capitalize() == element.strip().capitalize()
        ]

    def get_element_site_indices_by_global_index(self, global_idx: int) -> int:
        """
        グローバルインデックスから元素種ごとのサイト番号（1始まり, 1-based）を返す。

        Args:
            global_idx (int): グローバルインデックス（1始まり）

        Returns:
            int: 元素種内でのサイト番号（1始まり）
        """
        symbol = self.get_element_by_global_index(global_idx)
        local_list = self._element_site_indices[symbol]
        target = global_idx - 1  # convert to 0-based
        return local_list.index(target) + 1


if __name__ == "__main__":
    #
    cal_folder = "work_100Li3PS4_eq.lammpstrj"
    # step = 100000
    step = 0
    path = f"{cal_folder}/step_{step}"

    poscar = VaspPoscar(f"{path}/POSCAR")
    print(poscar.get_cartesian_position(119))
    print(poscar.get_num_atoms())

    print("get_lattice_constant()", poscar.get_lattice_constant())
    print("get_lattice_vectors()", poscar.get_lattice_vectors())
    print("get_elements()", poscar.get_elements())
    print("get_elements_index()", poscar.get_elements_index())
    print("get_atom_indices()", poscar.get_atom_indices())
    print("is_direct", poscar.is_direct)
    print("get_num_atoms()", poscar.get_num_atoms())

    # 内部座標
    print("get_coords_direct()", poscar.get_coords_direct())
    print("get_fractional_position(1)", poscar.get_fractional_position(1))
    print("get_cartesian_position(1)", poscar.get_cartesian_position(1))
    print("")
    #
    # 元素記号・種類取り出しに関しての method
    print("get_global_index(Li,1)", poscar.get_global_index("Li", 1))
    print("get_global_index(P,1)", poscar.get_global_index("P", 1))
    print("get_element_by_global_index(1)", poscar.get_element_by_global_index(1))
    print("get_element_by_global_index(227)", poscar.get_element_by_global_index(227))
    print("get_element_site_indices(P)", poscar.get_element_site_indices("P"))
    print(
        "get_element_site_indices_by_global_index(1)",
        poscar.get_element_site_indices_by_global_index(1),
    )
    print(
        "get_element_site_indices_by_global_index(2)",
        poscar.get_element_site_indices_by_global_index(2),
    )
    print(
        "get_element_site_indices_by_global_index(226)",
        poscar.get_element_site_indices_by_global_index(226),
    )
