#!/usr/bin/env python
"""
K.NAKADA
kengo.nakada@mat.shimane-u.ac.jp
kengo.nakada@gmail.com
"""

import os
import numpy as np
from numpy import floating
from typing import List, Tuple, Optional, Any


from rmc_dft.vasp.vasp_poscar import VaspPoscar
from x_logger import XLogger


class VaspPoscarAnalyzer:
    """
    VASP POSCARファイルの解析を行うクラス。
    """

    def __init__(
        self,
        poscar: VaspPoscar,
        logger: Optional[XLogger] = None,
    ) -> None:
        """
        POSCARAnalyzerの初期化。

        Args:
            poscar (VaspPoscar): VaspPoscar instance
        """
        self.poscar = poscar
        self._logger = logger or XLogger()

    def get_jump_distance(
        self,
        other_analyzer: "VaspPoscarAnalyzer",
        site_index: int,
        pbc: bool = True,
    ):
        """
        指定した原子サイトの2つのMDステップ間（step1→step2）のジャンプ距離（移動距離）を計算する。
        同じグローバルインデックスの原子について、2つの構造間の移動距離を評価する。

        Args:
            other_analyzer (VaspPoscarAnalyzer): 比較対象の構造（step2）。
            site_index (int): グローバル原子インデックス（1始まり）。
            pbc (bool): 周期境界条件を適用するか（デフォルト: True）。

        Returns:
            float: 指定サイトにおける2ステップ間の実際のジャンプ距離（Å）。
        """
        d1 = self.poscar.get_direct_position(site_index)
        d2 = other_analyzer.poscar.get_direct_position(site_index)

        if pbc:
            vec_direct = self.poscar.get_shortest_pbc_direct_vector(d1, d2)
            # vec_direct = d2 - d1
            # vec_direct = self.poscar.apply_pbc_shortest_direct_vector(vec_direct)
        else:
            vec_direct = d2 - d1

        vec_car = vec_direct @ self.poscar.get_lattice_vectors()
        return np.linalg.norm(vec_car)

    def get_interatomic_distance(
        self,
        site_idx1: int,
        site_idx2: int,
        pbc: bool = True,
    ) -> floating:
        """
        2つの原子（グローバルサイトインデックス指定）の間の距離（オングストローム単位）を計算します。

        Args:
            site_idx1 (int): 原子1のグローバルサイトインデックス（1始まり）。
            site_idx2 (int): 原子2のグローバルサイトインデックス（1始まり）。
            pbc (bool): 周期境界条件を適用するかどうか（デフォルト: True）。

        Returns:
            float: cartesian norm, 原子1と原子2の間の距離（オングストローム）。
        """
        d1 = self.poscar.get_coords_direct(site_idx1)
        d2 = self.poscar.get_coords_direct(site_idx2)

        if pbc:
            vec_direct = self.poscar.get_shortest_pbc_direct_vector(d1, d2)
            # direct_pbc_d1 = self.poscar.apply_pbc_direct(d1)
            # direct_pbc_d2 = self.poscar.apply_pbc_direct(d2)
        else:
            vec_direct = d2 - d1
            # direct_pbc_d1 = d1
            # direct_pbc_d2 = d2

        # diff_direct = direct_pbc_d2 - direct_pbc_d1
        diff_car = vec_direct @ self.poscar.get_lattice_vectors()
        # diff_car = self.poscar.conv_direct_to_cartesian(diff_direct)

        return np.linalg.norm(diff_car)

    def get_distance_vector(
        self,
        index1: int,
        index2: int,
        pbc: bool = True,
    ):
        """
        周期境界条件を考慮した2点間の距離ベクトルと距離を計算する。

        Args:
            index1 (int): 原子1のグローバルインデックス（1始まり, 1-based）。
            index2 (int): 原子2のグローバルインデックス（1始まり, 1-based）。
            pbc (bool): 周期境界条件を考慮するかどうか（デフォルト: True）。

        Returns:
            Tuple[np.ndarray, float]: cartesian_norm, 距離ベクトルとそのノルム。
        """
        # index1, index2 are 1-based; adjust to 0-based for internal access
        # dvec = self.coords_direct[index2 - 1] - self.coords_direct[index1 - 1]
        # dvec = self.poscar.get_coords_direct(index2) - self.poscar.get_coords_direct( index1
        # )
        # if pbc:
        #     dvec -= np.round(dvec)
        # cartesian_vec = dvec @ self.poscar.get_lattice_vectors()
        # return cartesian_vec, np.linalg.norm(cartesian_vec)

        d1 = self.poscar.get_coords_direct(index2)
        d2 = self.poscar.get_coords_direct(index1)

        if pbc:
            vec_direct = self.poscar.get_shortest_pbc_direct_vector(d1, d2)
            # direct_pbc_d1 = self.poscar.apply_pbc_direct(d1)
            # direct_pbc_d2 = self.poscar.apply_pbc_direct(d2)
        else:
            vec_direct = d2 - d1
            # direct_pbc_d1 = d1
            # direct_pbc_d2 = d2

        # diff_direct = direct_pbc_d2 - direct_pbc_d1

        # diff_car = self.poscar.conv_direct_to_cartesian(diff_direct)
        diff_car = vec_direct @ self.poscar.get_lattice_vectors()
        diff_car_norm = np.linalg.norm(diff_car)

        return diff_car, diff_car_norm

    def is_jump(
        self,
        other,
        site_index,
        threshold,
        pbc=True,
    ) -> bool:
        """
        指定サイトが他のMDステップでジャンプしたかを判定する。

        Args:
            other (VaspPoscarAnalyzer): 比較対象のPOSCARAnalyzer
            site_index (int): サイト番号（1始まり, 1-based）
            threshold (float): 距離のしきい値（Å）
            pbc (bool): 周期境界条件を考慮するか（デフォルト: True）

        Returns:
            bool: ジャンプと判定された場合はTrue、そうでなければFalse
        """
        # site_index is 1-based
        distance = self.get_jump_distance(other, site_index, pbc=pbc)
        return distance > threshold

    def get_neighbors(
        self,
        center_global_idx: int,
        nn: int,
        target_elements: Optional[list] = None,
    ) -> list:
        """
        指定した中心原子から対象元素のみ近接原子を探索する。

        Args:
            center_global_idx (int): 中心原子のグローバルインデックス（1始まり）。
            nn (int): 取得する近接原子数。
            target_elements (Optional[list]): 対象元素のリスト。Noneなら全元素を対象。

        Returns:
            list: (距離, 元素, サイト番号, グローバル番号, 直交座標) のリスト。
        """
        # center_frac = self.poscar.get_fractional_position(center_global_idx)
        center_direct = self.poscar.get_fractional_position(center_global_idx)
        neighbors_with_distance = []

        for other_global_idx in range(1, self.poscar.get_num_atoms() + 1):
            if other_global_idx == center_global_idx:
                continue

            element = self.poscar.get_element_by_global_index(other_global_idx)
            if target_elements is not None and element not in target_elements:
                continue  # 対象元素フィルタ

            # other_frac = self.poscar.get_fractional_position(other_global_idx)
            # delta_frac = other_frac - center_frac
            # delta_frac -= np.round(delta_frac)  # PBC補正
            # delta_cart = delta_frac @ self.poscar.get_lattice_vectors()
            # distance = np.linalg.norm(delta_cart)
            # other_cart = self.poscar.get_cartesian_position(other_global_idx)

            other_car = self.poscar.get_cartesian_position(other_global_idx)
            other_direct = self.poscar.get_fractional_position(other_global_idx)

            # PBC補正
            other_pbc_direct = self.poscar.apply_pbc_direct(other_direct)
            center_pbc_direct = self.poscar.apply_pbc_direct(center_direct)

            delta_car = self.poscar.get_shortest_pbc_direct_vector(
                center_pbc_direct, other_pbc_direct
            )
            # delta_direct = other_pbc_direct - center_pbc_direct
            # delta_car = delta_direct @ self.poscar.get_lattice_vectors()

            # distance (cartesian norm)
            distance = np.linalg.norm(delta_car)

            site_no = self.poscar.get_element_site_indices_by_global_index(
                other_global_idx
            )

            neighbors_with_distance.append(
                (distance, element, site_no, other_global_idx, other_car)
            )

        neighbors_with_distance.sort(key=lambda x: x[0])
        return neighbors_with_distance[:nn]

    def get_nearest_neighbors(
        self,
        center_element: str,
        center_local_site_index: int,
        max_neighbors: int = 5,
        neighbor_element: Optional[str] = None,
        pbc: bool = True,
        filter_by_element: bool = False,
        cutoff_distance: Optional[float] = None,
    ) -> list:
        """
        指定原子からの近接原子を検索する。

        Args:
            center_element (str): 中心原子の種類。
            center_local_site_index (int): 中心原子のサイト番号（1始まり, 1-based）。
            max_neighbors (int): 取得する近接原子数。
            cutoff_distance (float): 閾値(max_neighborsが使われなくて、かつ cutoff_distance が選ばれた時に使われる)
            neighbor_element (Optional[str]): 対象とする原子種（Noneなら全て）。
            pbc (bool): 周期境界条件を考慮するかどうか（デフォルト: True）。
            filter_by_element (bool): Trueの場合、中心元素と同じ元素のみを対象にする（デフォルト: False）。

        Returns:
            list: (元素, サイト番号, グローバル番号, 距離, ベクトル) のリスト。
        """
        # 中心原子
        # center_local_site_index is 1-based
        center_idx = self.poscar.get_global_index(
            center_element, center_local_site_index
        )
        center_coord_direct = self.poscar.get_coords_direct(center_idx)

        candidates = []

        # zip 後
        #    [('Li', [0.1, 0.2, 0.3]), ('Li', [0.2, 0.5, 0.6]), ('P', [0.9, 0.8, 0.1]), ...]

        ################################################################################
        # 中心原子の近接nnを探す (600個原子があったら 600ループ)
        #
        # i および引数なし coords_direct() は0base系
        # 	- self.poscar.get_atom_indices()（全ての原子の元素記号リスト）と
        #   - self.poscar.get_coords_direct()（全ての原子の直交座標（分率座標）リスト）
        #
        for i, (symbol, coord_direct) in enumerate(
            zip(self.poscar.get_atom_indices(), self.poscar.get_coords_direct())
        ):
            ################################################################################
            # 中心原子0番目は除外(center_idxは1ベースなので -1 にしている)
            if i == center_idx - 1:
                continue
            if filter_by_element and symbol != center_element:
                continue
            if neighbor_element and symbol != neighbor_element:
                continue

            # i は 0base なので get_element_site_indices にあわせて 1base にする
            site_number = self.poscar.get_element_site_indices(symbol).index(i + 1) + 1

            # if pbc:
            #     direct_pbc_d1 = self.poscar.apply_pbc_direct(center_coord_direct)
            #     direct_pbc_d2 = self.poscar.apply_pbc_direct(coord_direct)
            # else:
            #     direct_pbc_d1 = center_coord_direct
            #     direct_pbc_d2 = coord_direct
            # dvec_direct = direct_pbc_d2 - direct_pbc_d1
            # dvec_cart = self.poscar.conv_direct_to_cartesian(dvec_direct)
            # dist = np.linalg.norm(dvec_cart)
            dvec_direct = self.poscar.get_shortest_pbc_direct_vector(
                center_coord_direct, coord_direct
            )
            dvec_cart = self.poscar.conv_direct_to_cartesian(dvec_direct)
            dvec_cart_norm = np.linalg.norm(dvec_cart)

            # 中心原子の近接の候補リストに詰める
            candidates.append((symbol, site_number, i + 1, dvec_cart_norm, dvec_cart))

        # 結果を近接距離x[3]列でソートする
        candidates.sort(key=lambda x: x[3])

        if cutoff_distance is not None:
            # 距離の閾値でフィルタ（昇順ソート済みなので[:max_neighbors]は不要）
            return [c for c in candidates if c[3] <= cutoff_distance]
        else:
            # デフォルトは隣接原子数で取り出す
            return candidates[:max_neighbors]

    def get_sorted_neighbors(
        self,
        center_element: str,
        center_site: int,
        max_neighbors: int = 4,
        pbc: bool = True,
    ) -> list:
        """
        指定原子の近接原子を距離順に取得する。

        Args:
            center_element (str): 中心原子種。
            center_site (int): サイト番号（1始まり, 1-based）。
            max_neighbors (int): 出力する近接原子数。
            pbc (bool): 周期境界条件を考慮するかどうか（デフォルト: True）。

        Returns:
            list: 近接原子のリスト。
        """
        # center_local_site_index is 1-based
        center_idx = self.poscar.get_global_index(center_element, center_site)
        center_coord_direct = self.poscar.get_coords_direct(center_idx)

        neighbors = []

        # zip 後
        #    [('Li', [0.1, 0.2, 0.3]), ('Li', [0.2, 0.5, 0.6]), ('P', [0.9, 0.8, 0.1]), ...]
        # i および引数なし coords_direct() は0base系
        for i, coord_direct in enumerate(self.poscar.get_coords_direct()):
            if i == center_idx - 1:
                continue

            coord_direct = np.array(coord_direct, dtype=np.float64)
            center_coord_direct = np.array(center_coord_direct, dtype=np.float64)

            if pbc:
                vec_direct = self.poscar.get_shortest_pbc_direct_vector(
                    center_coord_direct, coord_direct
                )
            else:
                vec_direct = center_coord_direct - coord_direct

            # if pbc:
            #     direct_pbc_d1 = self.poscar.apply_pbc_direct(center_coord_direct)
            #     direct_pbc_d2 = self.poscar.apply_pbc_direct(coord_direct)
            # else:
            #     direct_pbc_d1 = center_coord_direct
            #     direct_pbc_d2 = coord_direct
            # dvec_direct = direct_pbc_d2 - direct_pbc_d1
            # dvec_cart = self.poscar.conv_direct_to_cartesian(dvec_direct)

            dvec_cart = self.poscar.conv_direct_to_cartesian(vec_direct)
            # 実距離なので、dvec_cart ベース
            dist = np.linalg.norm(dvec_cart)

            symbol = self.poscar.get_atom_indices()[i + 1]
            symbol_list = self.poscar.get_element_site_indices(symbol)
            site_no = symbol_list.index(i + 1) + 1
            neighbors.append((symbol, site_no, i + 1, dist, dvec_cart))

        neighbors.sort(key=lambda x: x[3])
        return neighbors[:max_neighbors]

    def print_jump_distances(
        self,
        other_analyzer: "VaspPoscarAnalyzer",
        element: str,
        start_site: int,
        end_site: int,
        threshold: float,
        show_non_jumps: bool = True,
        pbc: bool = True,
    ) -> None:
        """
        2つの構造間での原子のジャンプ距離を表示する。
        この関数では周期境界条件（PBC）を考慮して、原子の移動を実際の最短経路として評価する。
        この関数で指定の start から end まで調べて、ジャンプ距離を表示する

        Args:
            other_analyzer (VaspPoscarAnalyzer): 比較対象のPOSCARAnalyzer。
            element (str): 対象原子種。
            start_site (int): 開始サイト番号（1始まり）。
            end_site (int): 終了サイト番号（1始まり）。
            threshold (float): しきい値（Å）。
            show_non_jumps (bool): しきい値以下の距離を表示するかどうか。
            pbc (bool): 周期境界条件を考慮するかどうか（デフォルト: True）。
        """
        site_indices = self.poscar.get_element_site_indices(element)[
            start_site - 1 : end_site
        ]
        # print(
        #     f"[DEBUG] site_indices[:10] = {site_indices[:10]} ... total = {len(site_indices)}"
        # )
        for i, idx in enumerate(site_indices):
            # print(f"[DEBUG] loop i = {i}, global idx = {idx}")
            dist = self.get_jump_distance(other_analyzer, idx, pbc=pbc)
            # print(f"[DEBUG] distance for idx {idx} = {dist:.6f}")
            site_number = start_site + i

            jumped = dist > threshold
            if jumped:
                print(
                    f"{element:>3} site #{site_number}: distance moved = {dist:.6f} threshold crossed: True"
                )
            elif show_non_jumps:
                print(f"{element:>3} site #{site_number}: distance moved = {dist:.6f}")

    def get_jump_distance_distribution(
        self,
        other_analyzer: "VaspPoscarAnalyzer",
        element: str,
        start_site: int,
        end_site: int,
        pbc: bool = True,
    ) -> List[float]:
        """
        指定された範囲の原子における、2つのMDステップ間のジャンプ距離（分布）を計算する。

        この分布は、2つのMDステップ（構造）間で各原子サイトがどれだけジャンプ（移動）したか、すなわちジャンプ距離（Å）を返す。
        ここでの距離は、一般的な移動距離ではなく「2つのMDステップ間でのジャンプ距離」に限定される。

        Args:
            other_analyzer (VaspPoscarAnalyzer): 比較対象。
            element (str): 対象原子種。
            start_site (int): 開始サイト番号（1始まり）。
            end_site (int): 終了サイト番号（1始まり）。
            pbc (bool): 周期境界条件を考慮するかどうか。

        Returns:
            List[float]: 指定範囲内の各原子に対するジャンプ距離（Å）のリスト。
        """
        site_indices = self.poscar.get_element_site_indices(element)[
            start_site - 1 : end_site
        ]
        jump_distances = [
            self.get_jump_distance(other_analyzer, idx, pbc=pbc) for idx in site_indices
        ]
        return jump_distances

    @staticmethod
    def scan_md_series_for_jumps(
        folder_path: str,
        file_template: str = "POSCAR_{}",
        step_min: int = 0,
        step_max: int = 100000,
        element: str = "Li",
        start_site: int = 1,
        end_site: int = 208,
        threshold: float = 4.0,
        show_non_jumps: bool = True,
    ) -> list[tuple[int, int, Any]]:
        """
        連続するMDステップ間で指定原子のジャンプを調査する（周期境界条件を考慮）。

        Args:
            folder_path (str): POSCARファイルのあるディレクトリ。
            file_template (str): ファイル名のテンプレート（例: "POSCAR_{}"）。
            step_min (int): 比較を始めるMDステップ。
            step_max (int): 比較を終えるMDステップ。
            element (str): 対象とする原子種。
            start_site (int): サイト範囲の開始（1始まり）。
            end_site (int): サイト範囲の終了（1始まり）。
            threshold (float): ジャンプとみなす距離のしきい値。
            show_non_jumps (bool): しきい値以下の距離を表示するかどうか。

        Returns:
            list[tuple[int, int, Any]]: ジャンプの情報を含むリスト。
        """
        for step in range(step_min, step_max):
            file1 = os.path.join(folder_path, file_template.format(step))
            file2 = os.path.join(folder_path, file_template.format(step + 1))

            if not os.path.exists(file1) or not os.path.exists(file2):
                print(f"Skipping step {step} → {step + 1}: POSCAR file missing.")
                continue

            a1 = VaspPoscarAnalyzer(Poscar(file1))
            a2 = VaspPoscarAnalyzer(Poscar(file2))

            print(f"\nStep {step} → {step + 1}")
            a1.print_jump_distances(
                a2,
                element=element,
                start_site=start_site,
                end_site=end_site,
                threshold=threshold,
                show_non_jumps=show_non_jumps,
            )

        jump_records = []

        for step in range(step_min, step_max):
            file1 = os.path.join(folder_path, file_template.format(step))
            file2 = os.path.join(folder_path, file_template.format(step + 1))

            if not os.path.exists(file1) or not os.path.exists(file2):
                print(f"Skipping step {step} → {step + 1}: POSCAR file missing.")
                continue

            poscar1 = Poscar(file1)
            poscar2 = Poscar(file2)
            a1 = VaspPoscarAnalyzer(poscar1)
            a2 = VaspPoscarAnalyzer(poscar2)

            print(f"\nStep {step} → {step + 1}")
            site_indices = poscar1.get_element_site_indices(element)[
                start_site - 1 : end_site
            ]
            for i, idx in enumerate(site_indices):
                dist = a1.get_jump_distance(a2, idx, pbc=True)
                site_number = start_site + i
                jumped = dist > threshold
                if jumped:
                    print(
                        f"{element} site #{site_number}: distance moved = {dist:.6f} threshold crossed: True"
                    )
                    jump_records.append((step, site_number, dist))
                elif show_non_jumps:
                    print(f"{element} site #{site_number}: distance moved = {dist:.6f}")

        print("\nSummary of Jumps:")
        for step, site, dist in jump_records:
            print(
                f"Step {step}: {element} site #{site} jumped, distance = {dist:.6f} Å"
            )
        return jump_records

    @staticmethod
    def check_jump_between_two_steps(
        poscar1_path: str,
        poscar2_path: str,
        element: str = "Li",
        start_site: int = 1,
        end_site: int = 208,
        threshold: float = 4.0,
        show_non_jumps: bool = True,
    ) -> None:
        """
        2つのPOSCARファイル間でジャンプを検出し表示するユーティリティ。

        Args:
            poscar1_path (str): 1つ目のPOSCARファイル。
            poscar2_path (str): 2つ目のPOSCARファイル。
            element (str): 対象の原子種。
            start_site (int): サイト範囲の開始（1始まり）。
            end_site (int): サイト範囲の終了（1始まり）。
            threshold (float): ジャンプ判定の距離しきい値（Å）。
            show_non_jumps (bool): しきい値以下の距離を表示するかどうか。
        """
        a1 = VaspPoscarAnalyzer(Poscar(poscar1_path))
        a2 = VaspPoscarAnalyzer(Poscar(poscar2_path))

        print(f"\nJump Check Between Two Steps")
        a1.print_jump_distances(
            a2,
            element=element,
            start_site=start_site,
            end_site=end_site,
            threshold=threshold,
            show_non_jumps=show_non_jumps,
        )

    @staticmethod
    def trace_site_motion_over_md_steps(
        folder_path: str,
        site_index: int,
        element: str = "Li",
        step_min: int = 0,
        step_max: int = 100000,
        file_template: str = "POSCAR_{}",
        threshold: float = 4.0,
        show_non_jumps: bool = False,
    ) -> None:
        """
        指定したサイトの原子が、各MDステップ間でどれだけ動いたかを追跡表示する。

        Args:
            folder_path (str): POSCARファイルのディレクトリ。
            site_index (int): 追跡するグローバル原子インデックス（1始まり）。
            element (str): 原子種（例: "Li"）。
            step_min (int): 開始ステップ番号。
            step_max (int): 終了ステップ番号。
            file_template (str): ファイル名テンプレート（例: "POSCAR_{}"）。
            threshold (float): ジャンプとみなす距離のしきい値（Å）。
            show_non_jumps (bool): しきい値以下の距離を表示するかどうか。
        """
        print(
            f"\nTracing motion for {element} site #{site_index} from step {step_min} to {step_max}\n"
        )
        for step in range(step_min, step_max):
            file1 = os.path.join(folder_path, file_template.format(step))
            file2 = os.path.join(folder_path, file_template.format(step + 1))

            if not os.path.exists(file1) or not os.path.exists(file2):
                print(f"Skipping step {step} → {step + 1}: missing POSCAR file.")
                continue

            a1 = VaspPoscarAnalyzer(Poscar(file1))
            a2 = VaspPoscarAnalyzer(Poscar(file2))
            dist = a1.get_jump_distance(a2, site_index, pbc=True)
            if dist > threshold:
                print(
                    f"Step {step} → {step + 1}:"
                    f" {element} site #{site_index}, displacement = {dist:.6f} Å (JUMP)"
                )
            elif show_non_jumps:
                print(
                    f"Step {step} → {step + 1}:"
                    f" {element} site #{site_index}, displacement = {dist:.6f} Å"
                )
