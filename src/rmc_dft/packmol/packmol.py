#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
make_amorphous.py

Fe–Si–B アモルファス初期構造を Packmol により生成するための
入力ファイル (packmol.inp) を作成するスクリプト。

本スクリプトは、以下の 3 点を外部入力とする：

    1. 化学量論比（整数比）
    2. 密度 [g/cm^3] または 数密度 [1/Å^3] のいずれか一方
    3. セル内の総原子数 N_tot

Packmol は密度・化学量論比の概念を持たないため、本スクリプト側で
原子数とセル一辺長 L を計算し、Packmol 形式の inside box 指定に変換する。
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import subprocess

from x_logger import XLogger

NA: float = 6.02214076e23  # アボガドロ数 [1/mol]
A3_TO_CM3: float = 1e-24  # 1 Å³ = 1e-24 cm³


# -------------------------------------------------------------
# 原子量 (g/mol)
# -------------------------------------------------------------
ATOMIC_WEIGHTS: Dict[str, float] = {
    #   "H": 1.00794,
    #   "He": 4.002602,
    #   "Li": 6.941,
    #   "Be": 9.012182,
    "B": 10.811,
    #   "C": 12.0107,
    #   "N": 14.0067,
    #   "O": 15.9994,
    #   "F": 18.9984032,
    #   "Ne": 20.1797,
    #   "Na": 22.98976928,
    #   "Mg": 24.3050,
    #   "Al": 26.9815386,
    "Si": 28.0855,
    #   "P": 30.973762,
    #   "S": 32.065,
    #   "Cl": 35.453,
    #   "Ar": 39.948,
    #   "K": 39.0983,
    #   "Ca": 40.078,
    #   "Sc": 44.955912,
    #   "Ti": 47.867,
    #   "V": 50.9415,
    #   "Cr": 51.9961,
    #   "Mn": 54.938045,
    "Fe": 55.845,
    #   "Co": 58.933195,
    #   "Ni": 58.6934,
    #   "Cu": 63.546,
    #   "Zn": 65.409,
    #   "Ga": 69.723,
    #   "Ge": 72.64,
    #   "As": 74.92160,
    #   "Se": 78.96,
    #   "Br": 79.904,
    #   "Kr": 83.798,
    #   "Rb": 85.4678,
    #   "Sr": 87.62,
    #   "Y": 88.90585,
    #   "Zr": 91.224,
    #   "Nb": 92.90638,
    #   "Mo": 95.96,
    #   "Ru": 101.07,
    #   "Rh": 102.90550,
    #   "Pd": 106.42,
    #   "Ag": 107.8682,
    #   "Cd": 112.411,
    #   "In": 114.818,
    #   "Sn": 118.710,
    #   "Sb": 121.760,
    #   "Te": 127.60,
    #   "I": 126.90447,
    #   "Xe": 131.293,
    #   "Cs": 132.9054519,
    #   "Ba": 137.327,
    #   "La": 138.90547,
    #   "Ce": 140.116,
    #   "Pr": 140.90765,
    #   "Nd": 144.242,
    #   "Sm": 150.36,
    #   "Eu": 151.964,
    #   "Gd": 157.25,
    #   "Tb": 158.92535,
    #   "Dy": 162.500,
    #   "Ho": 164.93032,
    #   "Er": 167.259,
    #   "Tm": 168.93421,
    #   "Yb": 173.04,
    #   "Lu": 174.967,
    #   "Hf": 178.49,
    #   "Ta": 180.94788,
    #   "W": 183.84,
    #   "Re": 186.207,
    #   "Os": 190.23,
    #   "Ir": 192.217,
    #   "Pt": 195.084,
    #   "Au": 196.966569,
    #   "Hg": 200.59,
    #   "Tl": 204.3833,
    #   "Pb": 207.2,
    #   "Bi": 208.98040,
}


class Packmol:
    """
    amorphous構造を作成するのに助けになるメソッドなど
    """

    def __init__(
        self,
        input_file: Optional[str] = None,  # "packmol.inp",
        output_xyz: Optional[str] = None,  # "amorphous.xyz",
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,  # "/Users/nakada/packmol/bin/packmol",
        logger: Optional[XLogger] = None,
    ) -> None:
        """

        Args:
            input_file:
            output_xyz:
            output_log:
            packmol_bin (str): bin と言いながら path 指定
            logger:
        """
        self._logger: XLogger = logger or XLogger()
        self.input_file: str = input_file or "packmol.inp"
        self.output_xyz: str = output_xyz or "amorphous.xyz"
        self.output_log: str = output_log or "packmol.log"
        self.packmol_bin = packmol_bin or "/Users/nakada/packmol/bin/packmol"

        self._logger.info(f"input_file: {self.input_file}")
        self._logger.info(f"output_xyz: {self.output_xyz}")
        self._logger.info(f"output_log: {self.output_log}")
        self._logger.info(f"packmol_bin: {self.packmol_bin}")

    def get_unit_atom_count(
        self,
        ratios: Sequence[int],
    ) -> int:
        """
        化学量論比1ユニットあたりの原子数を返す。
        例: [80, 9, 11] -> 100

        Args:
            ratios:

        Returns:

        """
        self._logger.info(f"== get_unit_atom_count()")
        total = 0
        for value in ratios:
            total = total + value
        return total

    @staticmethod
    def get_atomic_weight(
        element: str,
    ) -> float:
        """汎用

        元素記号から原子量を取得する。

        Args:
            element (str):
                元素記号（例: "Fe", "Si", "B"）。

        Returns:
            float:
                原子量 [g/mol]。

        Raises:
            KeyError:
                対応する元素記号がテーブルに存在しない場合。
        """
        return ATOMIC_WEIGHTS[element]

    def average_atomic_weight(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
    ) -> float:
        """汎用

        化学量論比から平均原子量を計算する。

        たとえば Fe80Si9B11 の場合は::

            symbols = ["Fe", "Si", "B"]
            ratios  = [80, 9, 11]

        のように与える。

        Args:
            symbols (Sequence[str]): 元素記号の並び。
            ratios (Sequence[int]): 各元素の化学量論比に対応する整数比。

        Returns:
            float:
                平均原子量 [g/mol]。
        """
        self._logger.info("== average_atomic_weight()")
        if len(symbols) != len(ratios):
            raise ValueError("symbols と ratios の長さが一致していません。")

        total_atoms: int = sum(ratios)
        if total_atoms <= 0:
            raise ValueError("ratios の合計が 0 以下です。")

        total_mass: float = 0.0
        for symbol, ratio in zip(symbols, ratios):
            atomic_weight: float = self.get_atomic_weight(symbol)
            total_mass += atomic_weight * float(ratio)

        return total_mass / float(total_atoms)

    # @staticmethod
    # def number_density_from_mass_density(
    #     M_avg: float,
    #     mass_density_g_cm3: float,
    # ) -> float:
    #     """密度から数密度を計算する。
    #     数密度 n [1/Å^3] は、平均原子量 M_avg を用いて次式で与えられる::
    #     n = mass_density * NA / M_avg * A3_TO_CM3
    #     Args:
    #         M_avg (float): 平均原子量 [g/mol]。
    #         mass_density_g_cm3 (float): 質量密度 [g/cm^3]。

    #     Returns:
    #         float:
    #             数密度 n [1/Å^3]。
    #     """
    #     return mass_density_g_cm3 * NA * A3_TO_CM3 / M_avg

    def number_density_from_mass_density(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        mass_density_g_cm3: float,
    ) -> float:
        """汎用

        質量密度から数密度 n [1/Å^3] を計算する。

        *) 旧版と仕様変更したので注意

        Args:
            symbols (Sequence[str]): 元素記号の並び。
            ratios (Sequence[int]): 各元素の化学量論比。
            mass_density_g_cm3 (float): 質量密度 ρ [g/cm^3]。

        Returns:
            float:
                数密度 n [1/Å^3]。
        """
        self._logger.info("== number_density_from_mass_density()")
        M_avg: float = self.average_atomic_weight(symbols, ratios)
        # n = mass_density * NA / M * (cm^3→Å^3 の変換係数)
        return mass_density_g_cm3 * NA * A3_TO_CM3 / M_avg

    # @staticmethod
    # def mass_density_from_number_density(
    #     M_avg: float,
    #     number_density_A3: float,
    # ) -> float:
    #     """
    #     数密度から密度を計算する。
    #     Args:
    #         M_avg (float): 平均原子量 [g/mol]。
    #         number_density_A3 (float): 数密度 n [1/Å^3]。
    #     Returns:
    #         float: 質量密度 ρ [g/cm^3]。
    #     """
    #     return number_density_A3 * M_avg / (NA * A3_TO_CM3)

    def mass_density_from_number_density(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        number_density_A3: float,
    ) -> float:
        """汎用

        数密度 n [1/Å^3] から質量密度 ρ [g/cm^3] を計算する。

        Args:
            symbols (Sequence[str]):
                元素記号の並び。
            ratios (Sequence[int]):
                各元素の化学量論比。
            number_density_A3 (float):
                数密度 n [1/Å^3]。

        Returns:
            float: 質量密度 ρ [g/cm^3]。
        """
        self._logger.info("== mass_density_from_number_density()")
        M_avg: float = self.average_atomic_weight(symbols, ratios)
        # ρ = n * M / (NA * A3_TO_CM3)
        return number_density_A3 * M_avg / (NA * A3_TO_CM3)

    def cell_length_from_number_density(
        self,
        N_tot: int,
        number_density_A3: float,
    ) -> float:
        """汎用

        総原子数と数密度から立方体セル長 L [Å] を計算する。

        数密度からセル一辺長 L を計算する。立方体セルを仮定し、

            V = N_tot / n
            L = V^(1/3)

        Args:
            N_tot (int): セル内の総原子数。
            number_density_A3 (float): 数密度 n [1/Å^3]。

        Returns:
            float: 立方体セルの一辺の長さ L [Å]。
        """
        self._logger.info("== cell_length_from_number_density()")
        if N_tot <= 0:
            raise ValueError("N_tot は正の整数である必要があります。")
        if number_density_A3 <= 0.0:
            raise ValueError("数密度 number_density_A3 は正の値である必要があります。")

        volume_A3: float = float(N_tot) / number_density_A3
        L: float = volume_A3 ** (1.0 / 3.0)
        return L

    def compute_element_counts(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        N_tot: int,
    ) -> Dict[str, int]:
        """汎用

        化学量論比と N_tot から各元素の原子数を決める。

        数値的な意味

        1. 各元素の「理想的な原子数」を
               N_tot * ratio_i / sum(ratios)
           として実数で計算する。
        2. その整数部分を「最低限その元素に入れるべき原子数」とみなす。
        3. まだ入っていない原子（remainder = N_tot - sum(floor)）を数える。
        4. 理想値の小数部分が大きい元素から順に +1 ずつ配っていく。

        これにより、

        - 合計は必ず N_tot になる
        - 各元素の原子数は「理想値」に最も近い整数に近づく

        という性質を持つ。

        Args:
            symbols (Sequence[str]):
                元素記号の列（例: ("Fe", "Si", "B")）。

            ratios (Sequence[int]):
                symbols と同じ順番の化学量論比（例: (80, 9, 11)）。

            N_tot (int):
                セル内の総原子数。

        Returns:
            Dict[str, int]: {元素記号: 原子数} の辞書。
        """
        self._logger.info(f"== compute_element_counts()")
        # 「リストの長さ」ではなく、「元素種類数と比率の個数」が一致しているかを確認
        if len(symbols) != len(ratios):
            raise ValueError(
                "元素記号の種類数と、それに対応する化学量論比の個数が一致していません。"
            )
        self._logger.info(f"symbols: {symbols}")

        if N_tot <= 0:
            raise ValueError("N_tot は正の整数で指定してください。")
        self._logger.info(f"N_tot: {N_tot}")

        # ['Fe', 'Si', 'B']
        # [80, 9, 11]
        ratio_sum: int = sum(ratios)
        if ratio_sum <= 0:
            raise ValueError("化学量論比の総和が 0 以下です。")
        self._logger.info(f"ratios: {ratios}")
        self._logger.info(f"ratio_sum: {ratio_sum}")

        # 1. 理想的な原子数（実数）を計算する
        ideal_counts: List[float] = []
        for ratio in ratios:
            ideal = N_tot * float(ratio) / float(ratio_sum)
            ideal_counts.append(ideal)
        self._logger.info(f"ideal_counts: {ideal_counts}")

        # 2. 整数部分を「最低限確保される個数」とみなす
        int_counts: List[int] = [int(x) for x in ideal_counts]

        # 3. まだ割り当てられていない原子数を数える
        used: int = sum(int_counts)
        remainder: int = N_tot - used

        # 4. 小数部分が大きい元素から順に +1 ずつ配る
        if remainder > 0:
            frac_list: List[Tuple[int, float]] = []
            for i, ideal in enumerate(ideal_counts):
                fractional = ideal - float(int_counts[i])
                frac_list.append((i, fractional))

            frac_list.sort(key=lambda x: x[1], reverse=True)

            for k in range(remainder):
                idx: int = frac_list[k][0]
                int_counts[idx] += 1

        result: Dict[str, int] = {}
        for sym, cnt in zip(symbols, int_counts):
            result[sym] = cnt

        return result

    def compute_cell_sizes(
        self,
        ratios: Sequence[int],
        max_atom_count: int,
    ) -> List[int]:
        """汎用

        化学量論比を厳密に保つセル原子数を列挙する。
        ユニット原子数と使用可能なセル原子数を出力する。

        条件:
            N = unit_atom_count * k (kは正の整数)
            N <= max_atom_count

        Args:
            ratios:
            max_atom_count:

        Returns:

        """
        self._logger.info(f"== generate_cell_sizes()")
        unit_atom_count = self.get_unit_atom_count(ratios)
        cell_sizes: List[int] = []

        multiplier = 1
        current_size = unit_atom_count * multiplier

        while current_size <= max_atom_count:
            cell_sizes.append(current_size)
            multiplier = multiplier + 1
            current_size = unit_atom_count * multiplier

        self._logger.info(f"化学量論比 = {ratios}")
        self._logger.info(f"1ユニット原子数 = {unit_atom_count}")
        self._logger.info("生成可能なセル原子数:")
        for size in cell_sizes:
            self._logger.info(size)

        return cell_sizes

    # ------------------------------------
    # packmol 用
    # ------------------------------------
    def write_single_atom_xyz(
        self,
        filename: str,
        element: str,
    ) -> None:
        """単一原子のみを含む XYZ ファイルを生成する。

        Packmol では構造ファイル内の原子配置そのものは重要ではなく、
        「この構造を number 個だけ複製する」という使い方をする。
        よって 1 原子のみを原点に置いた XYZ が最も扱いやすい。

        Args:
            filename (str):
                書き出すファイル名。

            element (str):
                化学記号（Fe, Si, B など）。
        """
        self._logger.info(f"== write_single_atom_xyz()")
        with open(filename, "w") as f:
            f.write("1\n")
            f.write(f"{element} atom template\n")
            f.write(f"{element}  0.0  0.0  0.0\n")

    def run_packmol(
        self,
        input_file: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,
    ) -> None:
        """Packmol を実行する。

        コマンドラインでの

            packmol < packmol.inp

        と全く同じことを Python から行う。

        Args:
            input_file (str):
                Packmol の入力ファイル名。

            output_log (str):
                Packmol 実行ログを書き出すファイル名。

            packmol_bin (str):
                Packmol 実行ファイルの絶対パス。
        """
        self._logger.info(f"== run_packmol()")
        if input_file is None:
            input_file = self.input_file

        if output_log is None:
            output_log = self.output_log

        if packmol_bin is None:
            packmol_bin = self.packmol_bin

        # packmol.inp をそのまま stdin にする
        with open(input_file, "r") as fin, open(output_log, "w") as flog:
            result = subprocess.run(
                [packmol_bin],
                stdin=fin,  # ここが「packmol < input」の本体
                stdout=flog,
                stderr=subprocess.STDOUT,
                text=True,
            )

        # ここでは例外で落とさず、終了コードだけ知らせる
        if result.returncode != 0:
            print(
                f"Packmol の終了ステータスが 0 ではありません (code={result.returncode})"
            )
            print(f"詳細はログ {output_log} を確認してください。")

    def xyz_to_poscar(
        self,
        xyz_file: str,
        poscar_file: str = "POSCAR",
        packmol_inp: str = "packmol.inp",
        comment: str = "packmol",
        elements: Optional[List[str]] = None,  #  =["Fe", "Si", "B"],
    ) -> None:
        """Packmol が出力した XYZ を VASP POSCAR へ変換する。

        POSCAR は以下を満たす形式で出力する：
            - 種類ごとの原子数を数える
            - 直交セル（立方体）を仮定し、make_amorphous の L を使用
            - 位置は全て Direct (分数座標) へ変換

        Args:
            xyz_file (str):
                Packmol 出力の XYZ ファイル名。

            poscar_file (str):
                書き出す POSCAR ファイル名。

            packmol_inp (str):
            comment (str): POSCAR の中のコメント
            elements (List[str]): 元素の並び順（POSCAR の行順）, None ならば書かない(VASP4)
        """
        self._logger.info(f"== xyz_to_poscar()")
        # --- XYZ 読み込み ---
        with open(xyz_file, "r") as f:
            lines = f.readlines()

        # 1行目: 原子数
        # 2行目: コメント
        xyz_atoms = []
        for line in lines[2:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            sym = parts[0]
            x, y, z = map(float, parts[1:4])
            xyz_atoms.append((sym, x, y, z))

        # make_amorphous 内で使っている L を再利用するため、
        # グローバル or 外部で保持している L を参照する。
        # ここでは packmol.inp 内の box サイズを読み直す。
        L = None
        with open(f"{packmol_inp}", "r") as f:
            for line in f:
                if "inside box" in line:
                    parts = line.split()
                    # "... inside box 0.0 0.0 0.0  L L L"
                    L = float(parts[-1])
                    break

        if L is None:
            raise RuntimeError(f"{packmol_inp} から L を取得できませんでした。")

        # --- Direct (fractional) 座標へ変換 ---
        # XYZ の座標は Å単位の絶対座標なので L で割れば Direct
        frac_atoms = [(sym, x / L, y / L, z / L) for sym, x, y, z in xyz_atoms]

        # --- 元素ごとに分類 ---
        species_counts = {s: 0 for s in elements}
        species_positions = {s: [] for s in elements}

        for sym, fx, fy, fz in frac_atoms:
            if sym in elements:
                species_counts[sym] += 1
                species_positions[sym].append((fx, fy, fz))
            else:
                raise RuntimeError(f"未知の元素シンボル: {sym}")

        # --- POSCAR 書き出し ---
        with open(poscar_file, "w") as f:
            f.write(f"{comment}\n")
            f.write("1.0\n")  # スケールファクター

            # 立方体セル
            f.write(f"{L:.10f} 0.0 0.0\n")
            f.write(f"0.0 {L:.10f} 0.0\n")
            f.write(f"0.0 0.0 {L:.10f}\n")

            # 元素名
            # f.write(" ".join(elements) + "\n")
            if elements is not None:
                # 元素行を書く
                f.write(" ".join(elements) + "\n")
                species_order: List[str] = elements
            else:
                # 元素行は書かない(VASP4)
                # 個数行の並び順だけ別に決める（ここでは dict のキー順をそのまま使う）
                species_order: List[str] = list(species_counts.keys())

            # 元素ごとの個数
            f.write(" ".join(str(species_counts[s]) for s in elements) + "\n")

            f.write("Direct\n")

            # 元素順に Direct 座標を書き込む
            for s in elements:
                for fx, fy, fz in species_positions[s]:
                    f.write(f"{fx:.10f}  {fy:.10f}  {fz:.10f}\n")
