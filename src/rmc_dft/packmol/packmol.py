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


NA: float = 6.02214076e23  # アボガドロ数 [1/mol]
A3_TO_CM3: float = 1e-24  # 1 Å³ = 1e-24 cm³


class Packmol:
    """
    amorphous構造を作成するのに助けになるメソッドなど
    """

    def __init__(
        self,
        input_file: Optional[str] = None,  # "packmol.inp",
        output_xyz: Optional[str] = None,  # "amorphous.xyz",
        output_log: Optional[str] = None,
        packmol_path: Optional[str] = None,  # "/Users/nakada/packmol/bin/packmol",
    ) -> None:
        self.input_file: str = input_file or "packmol.inp"
        self.output_xyz: str = output_xyz or "amorphous.xyz"
        self.output_log: str = output_log or "packmol.log"
        self.packmol_path = packmol_path or "/Users/nakada/packmol/bin/packmol"

    @staticmethod
    def number_density_from_rho(
        M_avg: float,
        rho_g_cm3: float,
    ) -> float:
        """密度から数密度を計算する。

        数密度 n [1/Å^3] は、平均原子量 M_avg を用いて次式で与えられる::

            n = rho * NA / M_avg * A3_TO_CM3

        Args:
            M_avg (float):
                平均原子量 [g/mol]。
            rho_g_cm3 (float):
                質量密度 [g/cm^3]。

        Returns:
            float:
                数密度 n [1/Å^3]。
        """
        return rho_g_cm3 * NA * A3_TO_CM3 / M_avg

    @staticmethod
    def rho_from_number_density(
        M_avg: float,
        n_per_A3: float,
    ) -> float:
        """数密度から密度を計算する。

        Args:
            M_avg (float):
                平均原子量 [g/mol]。
            n_per_A3 (float):
                数密度 n [1/Å^3]。

        Returns:
            float:
                質量密度 ρ [g/cm^3]。
        """
        return n_per_A3 * M_avg / (NA * A3_TO_CM3)

    @staticmethod
    def cell_length_from_number_density(
        N_tot: int,
        n_per_A3: float,
    ) -> float:
        """数密度からセル一辺長 L を計算する。

        立方体セルを仮定し、

            V = N_tot / n
            L = V^(1/3)

        により L を求める。

        Args:
            N_tot (int):
                セル内の総原子数。

            n_per_A3 (float):
                数密度 [1/Å^3]。

        Returns:
            float:
                セル一辺長 L [Å]。
        """
        V_A3 = N_tot / n_per_A3
        return V_A3 ** (1.0 / 3.0)

    # ------------------------------------
    # packmol 用
    # ------------------------------------
    @staticmethod
    def write_single_atom_xyz(
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
        with open(filename, "w") as f:
            f.write("1\n")
            f.write(f"{element} atom template\n")
            f.write(f"{element}  0.0  0.0  0.0\n")

    def run_packmol(
        self,
        input_file: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_path: Optional[str] = None,
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

            packmol_path (str):
                Packmol 実行ファイルの絶対パス。
        """
        if input_file is None:
            input_file = self.input_file

        if output_log is None:
            output_log = self.output_log

        if packmol_path is None:
            packmol_path = self.packmol_path

        # packmol.inp をそのまま stdin にする
        with open(input_file, "r") as fin, open(output_log, "w") as flog:
            result = subprocess.run(
                [packmol_path],
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

    @staticmethod
    def xyz_to_poscar(
        xyz_file: str,
        poscar_file: str = "POSCAR",
        packmol_inp: str = "packmol.inp",
        comment: str = "packmol",
        species_order=("Fe", "Si", "B"),
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
            species_order (Tuple[str]):
                元素の並び順（POSCAR の行順）。
        """
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
        species_counts = {s: 0 for s in species_order}
        species_positions = {s: [] for s in species_order}

        for sym, fx, fy, fz in frac_atoms:
            if sym in species_order:
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
            f.write(" ".join(species_order) + "\n")

            # 元素ごとの個数
            f.write(" ".join(str(species_counts[s]) for s in species_order) + "\n")

            f.write("Direct\n")

            # 元素順に Direct 座標を書き込む
            for s in species_order:
                for fx, fy, fz in species_positions[s]:
                    f.write(f"{fx:.10f}  {fy:.10f}  {fz:.10f}\n")
