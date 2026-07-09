import itertools
import os
from pathlib import Path
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from rmc_dft.rmc_pot.qn.config_error import ConfigError
from rmc_dft.rmc_pot.qn.qn_network_analysis import QnNetworkAnalysis
from rmc_dft.rmc_pot.qn.vasp_structure import VaspStructure



class RmcConstraintWriter:
    """QnNetworkAnalysis の解析結果から RMC_POT 用 FNC/topology を出力するクラス。"""

    def __init__(self, network: QnNetworkAnalysis) -> None:
        self.network = network
        self.structure = network.structure
        self.config = network.config

    def write_fnc3(
        self,
        path: str,
        title: Optional[str] = None,
    ) -> None:
        output_title = title
        if output_title is None:
            output_title = Path(path).stem
        ranges = QnNetworkAnalysis.collect_fnc3_ranges(self.config)
        RmcConstraintWriter.write_fnc(
            path,
            self.structure.atom_count,
            self.network.fnc_pairs,
            ranges,
            output_title,
        )

    def write_unit_topology(
        self,
        path: str,
    ) -> None:
        RmcConstraintWriter.write_unit_topology_file(path, self.structure, self.config)

    def write_network_topology(
        self,
        path: str,
    ) -> None:
        RmcConstraintWriter.write_topology(
            path, self.structure, self.config, self.network
        )

    def write_rmc_inputs(
        self,
        prefix: str,
    ) -> None:
        self.write_fnc3(prefix + "_rmc_fnc3.fnc", title=prefix)
        self.write_unit_topology(prefix + "_rmc_unit.top")

    @staticmethod
    def write_fnc(
        path: str,
        atom_count: int,
        typed_pairs: Sequence[Tuple[int, int, int]],
        ranges: Dict[int, Tuple[float, float]],
        title: str,
    ) -> None:
        """RMC_POT FNC=3 用 ``*.fnc`` ファイルを書く。

        ``typed_pairs`` は 0 始まり index で受け取り、ファイル出力時に 1 始まりへ変換する。
        ``ranges`` は FNC type_id -> (rmin, rmax) で、type_id は 1 から連番である必要がある。
        """
        neighbours = defaultdict(list)  # type: Dict[int, List[Tuple[int, int]]]
        for i, j, type_id in typed_pairs:
            # RMC_POT の .fnc では全 atom について neighbour_count 行を書くが、
            # 各 constrained pair 自体は一度だけ書く。
            # Packmol 由来の既存 FNC と同じく、pair_key で正規化した
            # 小さい atom index 側に neighbour を保持する。
            neighbours[i].append((j, type_id))

        max_type = 0
        for type_id in ranges.keys():
            if type_id > max_type:
                max_type = type_id

        with open(path, "w", encoding="utf-8") as f:
            # RMC_POT の .fnc は、先頭に constraint type ごとの rmin/rmax を書き、
            # その後に各 atom の neighbour index と type_id を並べる。
            f.write("Fixed neighbours constraints (.FNC) file for %s\n" % title)
            f.write("\n")
            f.write(" No. of possible rmin-rmax pairs:\n")
            f.write(" %d\n" % max_type)
            rmin_values = []
            rmax_values = []
            for type_id in range(1, max_type + 1):
                if type_id not in ranges:
                    raise ConfigError("FNC type_id が連番ではありません: %d" % type_id)
                rmin_values.append("%.8f" % ranges[type_id][0])
                rmax_values.append("%.8f" % ranges[type_id][1])
            f.write(" ".join(rmin_values) + "\n")
            f.write(" ".join(rmax_values) + "\n")
            f.write("\n")
            f.write(" %d\n" % atom_count)
            f.write("\n")
            for atom in range(atom_count):
                items = neighbours.get(atom, [])
                f.write("%d %d\n" % (atom + 1, len(items)))
                if len(items) > 0:
                    f.write(" ".join(str(item[0] + 1) for item in items) + "\n")
                    f.write(" ".join(str(item[1]) for item in items) + "\n")

    @staticmethod
    def get_topology_config(
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """RMC_POT current-network topology 用設定を取得する。

        新しい JSON では ``rmc.top.network`` を使う。
        flat な旧 JSON 名はここでは読まない。
        """
        top_root = QnNetworkAnalysis.get_top_root_config(config)
        if "network" in top_root:
            return top_root["network"]
        raise ConfigError("config に rmc.top.network がありません。")

    @staticmethod
    def get_force_field_include(
        top_config: Dict[str, Any],
    ) -> str:
        """RMC_POT が force field 名を判定するための include 名を返す。

        RMC_POT は FNC=4 topology の先頭付近にある force-field include 名から
        force field 種別を判定する。GROMACS 用の実力場を使わない RMC 専用 topology
        でも、``ffUNKNOWN_READ_PAIRS.itp`` などの認識可能な include 名が必要である。
        """
        include_name = top_config.get("force_field_include", None)
        if include_name is None:
            include_name = top_config.get("include", None)
        if include_name is None:
            include_name = "ffUNKNOWN_READ_PAIRS.itp"
        return str(include_name)

    @staticmethod
    def write_force_field_stub(
        topology_path: str,
        include_name: str,
    ) -> None:
        """RMC 専用 UNKNOWN force-field include の空 stub を必要に応じて作る。

        RMC_POT は force field 名を include 名から判定する。実際の非結合 parameter は
        ``*.dat`` 側から読むため、UNKNOWN 系では include file の中身は最小でよい。
        既存ファイルがある場合は上書きしない。
        """
        if os.path.isabs(include_name):
            include_path = include_name
        else:
            base_dir = os.path.dirname(os.path.abspath(topology_path))
            include_path = os.path.join(base_dir, include_name)

        if os.path.exists(include_path):
            return

        include_base = os.path.basename(include_name)
        if include_base not in (
            "ffUNKNOWN_READ_PAIRS.itp",
            "ffUNKNOWN_GENERATE_PAIRS.itp",
        ):
            return

        with open(include_path, "w", encoding="utf-8") as f:
            f.write("; Minimal RMC_POT force-field marker include.\n")
            f.write(
                "; RMC_POT uses the include file name to identify UNKNOWN_READ_PAIRS / UNKNOWN_GENERATE_PAIRS.\n"
            )
            f.write(
                "; Non-bonded parameters, if used, must be supplied from the RMC_POT *.dat file.\n"
            )

    @staticmethod
    def build_angles(
        poscar: VaspStructure,
        config: Dict[str, Any],
        data: QnNetworkAnalysis,
    ) -> List[Tuple[int, int, int, str]]:
        """FNC=4 topology の [ angles ] に書く angle list を作る。

        JSON の ``rmc.top.network.angles`` で source を指定する。現在対応する source は次の通り。

        * ``bridge_central_bridge``: central を中心にした bridge-central-bridge。例: O-Si-O。
        * ``central_bridge_second``: bridge を中心にした central-bridge-second。例: Si-O-Si。

        戻り値の index は 0 始まりで、最後の文字列は angle parameter 名である。
        """
        top_config = RmcConstraintWriter.get_topology_config(config)
        angle_items = top_config.get("angles", [])
        angles = []  # type: List[Tuple[int, int, int, str]]
        seen = set()  # type: Set[Tuple[int, int, int, str]]

        for item in angle_items:
            name = str(QnNetworkAnalysis.get_required(item, "name"))
            source = str(QnNetworkAnalysis.get_required(item, "source"))
            if source == "bridge_central_bridge":
                for central, bridges in data.first_map.items():
                    sorted_bridges = sorted(bridges)
                    for bridge1, bridge2 in itertools.combinations(sorted_bridges, 2):
                        key = (bridge1, central, bridge2, name)
                        if key not in seen:
                            seen.add(key)
                            angles.append(key)

            elif source == "central_bridge_second":
                for central, bridges in data.first_map.items():
                    for bridge in bridges:
                        second_hits = data.second_by_bridge_for_central[
                            (central, bridge)
                        ]
                        for second in second_hits:
                            key = (central, bridge, second, name)
                            if key not in seen:
                                seen.add(key)
                                angles.append(key)

            else:
                raise ConfigError(
                    "未知の rmc.top.network angle source です: %s" % source
                )

        return angles

    @staticmethod
    def find_angle_parameter(
        config: Dict[str, Any],
        angle_name: str,
    ) -> Dict[str, Any]:
        """angle 名に対応する FNC=4 angle パラメータを JSON 設定から探す。"""
        top_config = RmcConstraintWriter.get_topology_config(config)
        for item in top_config.get("angles", []):
            name = str(QnNetworkAnalysis.get_required(item, "name"))
            if name == angle_name:
                return item
        raise ConfigError("angle parameter が見つかりません: %s" % angle_name)

    @staticmethod
    def write_topology(
        path: str,
        poscar: VaspStructure,
        config: Dict[str, Any],
        data: QnNetworkAnalysis,
    ) -> None:
        """RMC_POT FNC=4 用 topology を書く。

        ここで書く ``*.top`` は GROMACS で MD を実行するための topology ではない。
        RMC_POT が FNC=4 で bonded potential を計算するために読む topology である。

        RMC_POT の manual では topology の記法として GROMACS 型 directive 名が使われる。
        ただし RMC が認識する directive は限定されており、この exporter では
        Qn ネットワーク保持に必要な次の 5 種類だけを書く。

        * ``[ moleculetype ]``: ネットワーク全体を 1 つの molecule として扱うための名前。
        * ``[ atoms ]``: topology 内 atom index と RMC configuration 内 atom index の対応。
        * ``[ bonds ]``: Si-O など、ネットワーク edge に対する harmonic bond。
        * ``[ angles ]``: O-Si-O や Si-O-Si など、ネットワーク angle に対する harmonic angle。
        * ``[ system ]`` / ``[ molecules ]``: topology の末尾に必要な system 情報。

        ``[ atoms ]`` の行末にある ``; first_RMC_index second_RMC_index`` は RMC_POT 固有情報である。
        GROMACS ではコメントだが、RMC_POT はこの情報を使って topology atom と
        RMC configuration atom を対応付ける。ここでは 1 つの network molecule として書くため、
        first と second は同じ index にしている。

        ``[ bonds ]`` と ``[ angles ]`` は「結合がある」という幾何学的な宣言だけではない。
        RMC_POT は harmonic potential として使うため、平衡値、力定数、sigma が必要である。
        そのため、topology 用 JSON には最低限 ``bond.length_nm``、``bond.force_kj_mol_nm2``、
        ``bond.sigma``、および各 angle の ``theta_degree``、``force_kj_mol_rad2``、``sigma`` を置く。
        """
        top_config = RmcConstraintWriter.get_topology_config(config)

        molecule_name = str(top_config.get("molecule_name", "QNNET"))
        residue_name = str(top_config.get("residue_name", "QNN"))
        nrexcl = int(top_config.get("nrexcl", 2))

        atom_type_prefix = str(top_config.get("atom_type_prefix", ""))

        bond_config = top_config.get("bond", {})
        bond_length_nm = float(
            bond_config.get("length_nm", top_config.get("bond_length_nm", 0.161))
        )
        bond_force = float(
            bond_config.get(
                "force_kj_mol_nm2", top_config.get("bond_force_kj_mol_nm2", 10000.0)
            )
        )
        bond_sigma = float(bond_config.get("sigma", top_config.get("bond_sigma", 10.0)))

        angles = RmcConstraintWriter.build_angles(poscar, config, data)
        data.angles = angles

        include_name = RmcConstraintWriter.get_force_field_include(top_config)
        RmcConstraintWriter.write_force_field_stub(path, include_name)

        with open(path, "w", encoding="utf-8") as f:
            f.write("; RMC_POT FNC=4 topology generated by qn_network.py\n")
            f.write("; This is an RMC_POT topology, not a GROMACS MD topology.\n")
            f.write("; The current Qn network is treated as one flexible molecule.\n")
            f.write("; Tune force constants and sigmas by short RMC_POT test runs.\n")
            f.write('#include "%s"\n' % str(include_name))
            f.write("\n[ moleculetype ]\n")
            f.write("; molname nrexcl ; RMCindex_offset\n")
            f.write("%s %d ; 0\n\n" % (molecule_name, nrexcl))

            f.write("[ atoms ]\n")
            f.write(
                "; nr type resnr residue atom cgnr charge mass ; first_RMC_index second_RMC_index\n"
            )
            for i, label in enumerate(poscar.labels):
                if atom_type_prefix:
                    atom_type = "%s_%s" % (atom_type_prefix, label)
                else:
                    atom_type = label
                charge, mass = QnNetworkAnalysis.get_top_atom_parameter(config, label)
                atom_name = "%s%d" % (label, i + 1)
                f.write(
                    "%6d %-10s 1 %-6s %-8s %6d % .8f % .8f ; %d %d\n"
                    % (
                        i + 1,
                        atom_type,
                        residue_name,
                        atom_name,
                        i + 1,
                        charge,
                        mass,
                        i + 1,
                        i + 1,
                    )
                )

            f.write("\n[ bonds ]\n")
            f.write("; i j funct b_nm kb_kJ_mol_nm2 ; sigma\n")
            for i, j in sorted(data.bond_pairs):
                f.write(
                    "%6d %6d 1 %.8f %.8f ; %.8f\n"
                    % (i + 1, j + 1, bond_length_nm, bond_force, bond_sigma)
                )

            f.write("\n[ angles ]\n")
            f.write("; i j k funct theta_deg ktheta_kJ_mol_rad2 ; sigma ; name\n")
            for i, j, k, angle_name in angles:
                param = RmcConstraintWriter.find_angle_parameter(config, angle_name)
                theta = float(QnNetworkAnalysis.get_required(param, "theta_degree"))
                force = float(
                    QnNetworkAnalysis.get_required(param, "force_kj_mol_rad2")
                )
                sigma = float(QnNetworkAnalysis.get_required(param, "sigma"))
                f.write(
                    "%6d %6d %6d 1 %.8f %.8f ; %.8f ; %s\n"
                    % (i + 1, j + 1, k + 1, theta, force, sigma, angle_name)
                )

            f.write("\n[ system ]\n")
            f.write("Qn network generated from RMC/POSCAR structure\n\n")
            f.write("[ molecules ]\n")
            f.write("%s 1\n" % molecule_name)

    @staticmethod
    def get_unit_topology_config(
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """独立 unit topology 用設定を取得する。

        unit assignment は TOP と FNC で共通に使うため、``network.unit`` を基準にする。
        ``rmc.top.unit`` には TOP 出力固有の molecule 名、bond、angle などだけを置く。

        戻り値は ``network.unit`` と ``rmc.top.unit`` を結合した dict である。
        同じ key がある場合は ``rmc.top.unit`` を優先する。
        """
        network_config = QnNetworkAnalysis.get_network_config(config)
        unit_assignment_config = network_config.get("unit", {})

        top_root = QnNetworkAnalysis.get_top_root_config(config)
        top_unit_config = top_root.get("unit", {})

        merged = {}
        for key, value in unit_assignment_config.items():
            merged[key] = value
        for key, value in top_unit_config.items():
            merged[key] = value

        if len(merged) == 0:
            raise ConfigError(
                "config に network.unit または rmc.top.unit がありません。"
            )

        return merged

    @staticmethod
    def _select_unit_neighbor_candidates(
        poscar: VaspStructure,
        central_indices: Sequence[int],
        neighbor_indices: Sequence[int],
        min_distance: float,
        max_distance: float,
    ) -> List[Tuple[float, int, int]]:
        """central-neighbor 候補を距離順に並べて返す。

        戻り値は ``(distance, central_index, neighbor_index)`` の list である。
        ``build_independent_unit_molecules`` の最近接排他的割当で使う。
        """
        candidates = []
        for central in central_indices:
            for neighbor in neighbor_indices:
                distance = QnNetworkAnalysis.pbc_distance(
                    central, neighbor, poscar.frac, poscar.cell
                )
                if distance >= min_distance and distance <= max_distance:
                    candidates.append((distance, central, neighbor))
        candidates.sort()
        return candidates

    @staticmethod
    def build_independent_unit_molecules(
        poscar: VaspStructure,
        config: Dict[str, Any],
    ) -> List[Tuple[str, List[int], List[Tuple[int, int]], List[Tuple[int, int, int]]]]:
        """RMC_POT FNC=4 用の独立分子・独立フラグメント一覧を作る。

        この関数は、初期構造から検出したネットワーク全体を 1 つの molecule として固定しない。
        代わりに、central atom と一定数の neighbor atom から成る独立 unit を作る。
        たとえば SiO2 の Packmol 初期配置に対応させるなら、Si 1 個 + O 2 個を 1 unit とする。

        重要な設計意図は次である。

        * unit 内の bond/angle は RMC_POT の bonded potential で保つ。
        * unit 間には bond/angle を張らない。
        * したがって、RMC は unit 間配置を実験データに合わせて探索できる。
        * 個別の Si-O-Si ネットワーク全体を固定しない。

        JSON の ``rmc.top.unit`` で使う主な項目:

        * ``central_types``: unit 中心 atom type。例: ["Si"]。
        * ``neighbor_types``: unit に含める周辺 atom type。例: ["O"]。
        * ``neighbor_count``: central 1 個あたりに割り当てる neighbor 数。SiO2 unit なら 2。
        * ``distance_min`` / ``distance_max``: 割当候補とする central-neighbor 距離範囲。
        * ``assignment``: 現在は ``nearest_exclusive`` のみ。neighbor を複数 unit に重複所属させない。

        注意:
            この方法は「独立分子単位の保持」であり、共有酸素を持つ無限 Si-O-Si network を
            表現するものではない。共有ネットワークを固定したい場合は ``write_network_topology`` を使う。
        """
        unit_config = RmcConstraintWriter.get_unit_topology_config(config)
        central_types = unit_config.get("central_types", None)
        neighbor_types = unit_config.get("neighbor_types", None)

        if central_types is None:
            qn_config = QnNetworkAnalysis.get_network_config(config)
            central_types = qn_config.get("central_types", [])
        if neighbor_types is None:
            qn_config = QnNetworkAnalysis.get_network_config(config)
            neighbor_types = qn_config.get("bridge_types", [])

        neighbor_count = int(
            QnNetworkAnalysis.get_required(unit_config, "neighbor_count")
        )
        min_distance = float(unit_config.get("distance_min", 0.0))
        max_distance = float(unit_config.get("distance_max", 99.0))
        assignment = str(unit_config.get("assignment", "nearest_exclusive"))
        allow_incomplete = bool(unit_config.get("allow_incomplete", False))
        include_unassigned_atoms = bool(
            unit_config.get("include_unassigned_atoms", True)
        )
        molecule_name_prefix = str(unit_config.get("molecule_name", "UNIT"))
        generate_angles = bool(unit_config.get("generate_angles", True))

        if assignment != "nearest_exclusive":
            raise ConfigError(
                "rmc.top.unit.assignment は nearest_exclusive のみ対応しています。"
            )

        central_indices = QnNetworkAnalysis.select_indices(poscar.labels, central_types)
        neighbor_indices = QnNetworkAnalysis.select_indices(
            poscar.labels, neighbor_types
        )
        if len(central_indices) == 0:
            raise ConfigError("rmc.top.unit.central_types に対応する原子がありません。")
        if len(neighbor_indices) == 0:
            raise ConfigError(
                "rmc.top.unit.neighbor_types に対応する原子がありません。"
            )

        needs = {}
        assigned = defaultdict(list)  # type: Dict[int, List[int]]
        for central in central_indices:
            needs[central] = neighbor_count

        used_neighbors = set()  # type: Set[int]
        candidates = RmcConstraintWriter._select_unit_neighbor_candidates(
            poscar,
            central_indices,
            neighbor_indices,
            min_distance,
            max_distance,
        )

        # 距離が短い central-neighbor 候補から順に採用する。
        # neighbor は一度だけ使うので、unit 間で atom を共有しない。
        for distance, central, neighbor in candidates:
            if neighbor in used_neighbors:
                continue
            if needs[central] <= 0:
                continue
            assigned[central].append(neighbor)
            used_neighbors.add(neighbor)
            needs[central] = needs[central] - 1

        missing = []
        for central in central_indices:
            if needs[central] > 0:
                missing.append((central, needs[central]))
        if len(missing) > 0 and not allow_incomplete:
            raise ConfigError(
                "independent unit 作成で neighbor 数が不足しました。"
                "distance range または neighbor_count を見直してください。"
            )

        molecules = []  # type: List[Tuple[str, List[int], List[Tuple[int, int]], List[Tuple[int, int, int]]]]
        molecule_index = 1
        included_atoms = set()  # type: Set[int]

        for central in sorted(central_indices):
            neighbors = sorted(assigned.get(central, []))

            atom_indices = [central]
            for neighbor in neighbors:
                atom_indices.append(neighbor)

            bonds = []  # type: List[Tuple[int, int]]
            for local_neighbor_index in range(1, len(atom_indices)):
                bonds.append((0, local_neighbor_index))

            angles = []  # type: List[Tuple[int, int, int]]
            if generate_angles:
                local_neighbor_indices = list(range(1, len(atom_indices)))
                for local_i, local_k in itertools.combinations(
                    local_neighbor_indices, 2
                ):
                    angles.append((local_i, 0, local_k))

            molecule_name = "%s%06d" % (molecule_name_prefix, molecule_index)
            molecules.append((molecule_name, atom_indices, bonds, angles))
            for atom_index in atom_indices:
                included_atoms.add(atom_index)
            molecule_index = molecule_index + 1

        if include_unassigned_atoms:
            for atom_index in range(poscar.atom_count):
                if atom_index in included_atoms:
                    continue
                molecule_name = "%s%06d" % (molecule_name_prefix, molecule_index)
                molecules.append((molecule_name, [atom_index], [], []))
                included_atoms.add(atom_index)
                molecule_index = molecule_index + 1

        return molecules

    @staticmethod
    def write_unit_topology_file(
        path: str,
        poscar: VaspStructure,
        config: Dict[str, Any],
    ) -> None:
        """独立分子・独立フラグメント型の RMC_POT topology を書く。

        ``write_topology`` は、検出した current network を 1 つの flexible molecule として書く。
        それに対して、この関数は unit 間をつながない。各 unit を別々の molecule type として書き、
        unit 内の bond/angle だけを RMC_POT の bonded potential に渡す。

        RMC_POT の観点では、この topology も FNC=4 用である。ただし、拘束の意味は次のように違う。

        * full network topology: 初期構造の個別 Si-O-Si 接続を固定する方向。
        * independent unit topology: SiO2, SiO4 などの unit 内形状だけを保持する方向。

        ユーザーが RMC の自由度を重視する場合、まずはこちらを試す方が安全である。
        """
        unit_config = RmcConstraintWriter.get_unit_topology_config(config)
        molecules = RmcConstraintWriter.build_independent_unit_molecules(poscar, config)

        residue_name = str(unit_config.get("residue_name", "UNIT"))
        nrexcl = int(unit_config.get("nrexcl", 2))
        atom_type_prefix = str(unit_config.get("atom_type_prefix", ""))

        bond_config = unit_config.get("bond", {})
        bond_length_nm = float(QnNetworkAnalysis.get_required(bond_config, "length_nm"))
        bond_force = float(
            QnNetworkAnalysis.get_required(bond_config, "force_kj_mol_nm2")
        )
        bond_sigma = float(QnNetworkAnalysis.get_required(bond_config, "sigma"))

        angle_config = unit_config.get("angle", {})
        angle_theta = float(angle_config.get("theta_degree", 109.47))
        angle_force = float(angle_config.get("force_kj_mol_rad2", 100.0))
        angle_sigma = float(angle_config.get("sigma", 10.0))

        include_name = RmcConstraintWriter.get_force_field_include(unit_config)
        RmcConstraintWriter.write_force_field_stub(path, include_name)

        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "; RMC_POT FNC=4 independent-unit topology generated by qn_network.py\n"
            )
            f.write(
                "; This file keeps only intramolecular / intra-fragment geometry.\n"
            )
            f.write("; No bonds or angles are written between different units.\n")
            f.write(
                "; It is intended to preserve local units while leaving RMC freedom between units.\n"
            )
            f.write('#include "%s"\n' % str(include_name))
            f.write("\n")

            molecule_names = []
            for molecule_name, atom_indices, bonds, angles in molecules:
                molecule_names.append(molecule_name)
                f.write("[ moleculetype ]\n")
                f.write("; molname nrexcl ; RMCindex_offset\n")
                f.write("%s %d ; 0\n\n" % (molecule_name, nrexcl))

                f.write("[ atoms ]\n")
                f.write(
                    "; nr type resnr residue atom cgnr charge mass ; first_RMC_index second_RMC_index\n"
                )
                for local_index, global_index in enumerate(atom_indices):
                    label = poscar.labels[global_index]
                    if atom_type_prefix:
                        atom_type = "%s_%s" % (atom_type_prefix, label)
                    else:
                        atom_type = label
                    charge, mass = QnNetworkAnalysis.get_top_atom_parameter(
                        config, label
                    )
                    atom_name = "%s%d" % (label, global_index + 1)
                    rmc_index = global_index + 1
                    f.write(
                        "%6d %-10s 1 %-6s %-8s %6d % .8f % .8f ; %d %d\n"
                        % (
                            local_index + 1,
                            atom_type,
                            residue_name,
                            atom_name,
                            local_index + 1,
                            charge,
                            mass,
                            rmc_index,
                            rmc_index,
                        )
                    )

                f.write("\n[ bonds ]\n")
                f.write("; i j funct b_nm kb_kJ_mol_nm2 ; sigma\n")
                for local_i, local_j in bonds:
                    f.write(
                        "%6d %6d 1 %.8f %.8f ; %.8f\n"
                        % (
                            local_i + 1,
                            local_j + 1,
                            bond_length_nm,
                            bond_force,
                            bond_sigma,
                        )
                    )

                if len(angles) > 0:
                    f.write("\n[ angles ]\n")
                    f.write("; i j k funct theta_deg ktheta_kJ_mol_rad2 ; sigma\n")
                    for local_i, local_j, local_k in angles:
                        f.write(
                            "%6d %6d %6d 1 %.8f %.8f ; %.8f\n"
                            % (
                                local_i + 1,
                                local_j + 1,
                                local_k + 1,
                                angle_theta,
                                angle_force,
                                angle_sigma,
                            )
                        )
                f.write("\n")

            f.write("[ system ]\n")
            f.write("Independent local units generated from RMC/POSCAR structure\n\n")
            f.write("[ molecules ]\n")
            for molecule_name in molecule_names:
                f.write("%s 1\n" % molecule_name)
