#!/usr/bin/env python3
"""ゼオライト型 Si/Al/O フレームワークの構造解析ユーティリティ。

RMC の回折プロファイル適合度とは独立に、原子座標から
「ゼオライト型フレームワークとして成立しているか」を評価する。

本モジュールでは、特定の IZA framework type への一致は要求しない。
未知構造探索を妨げないため、以下を独立に評価する。

- Si/Al (T atom) の O 配位数分布
- O の T=(Si, Al) 配位数分布
- TO4 fraction
- bridging-O fraction
- T-O bond length
- O-T-O tetrahedral angle
- T-O-T hinge angle
- T-O network の連結性
- 周期境界をまたぐ network dimensionality (0D-3D)
- T-T network の shortest-ring 統計
- framework density
- Al-O-Al の割合

``is_zeolite_like`` は RMC 構造のスクリーニング用であり、
IZA による framework type の正式な同定ではない。
判定閾値は ``ZeoliteCriteria`` で明示的に変更できる。
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import ast
from pathlib import Path
import re
from dataclasses import asdict, dataclass
from itertools import combinations
from math import acos, degrees
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np
from pymatgen.core import Structure


Vector3i = Tuple[int, int, int]
BondRange = Tuple[float, float]


@dataclass(frozen=True)
class ZeoliteCutoffs:
    """ゼオライト骨格の結合判定距離 [Å]。

    Notes:
        デフォルト値は現在の RMC 設定に合わせている。
        これは「実在ゼオライトの許容結合長範囲」を定義するものではなく、
        どの原子を bonded neighbour とみなすかの解析 cutoff である。
    """

    si_o: BondRange = (1.40, 1.90)
    al_o: BondRange = (1.55, 2.10)

    def range_for_t(self, symbol: str) -> BondRange:
        """T 原子種に対応する T-O cutoff を返す。"""
        if symbol == "Si":
            return self.si_o
        if symbol == "Al":
            return self.al_o
        raise ValueError(f"T atom ではありません: {symbol}")


@dataclass(frozen=True)
class ZeoliteRmcConfig:
    """RMC 設定から取得したゼオライト解析用パラメータ。

    ``source`` は値を取得した ``*.dat`` または ``rmc_init*.py`` を示す。
    ``element_info`` は RMC type の順序で、1-origin の type 番号を元素へ
    対応付けるために使用する。

    ``ZeoliteCutoffs`` に変換するときは、COORD に指定された
    Si->O / Al->O の neighbour range をそのまま解析 bond range として使う。
    """

    source: str
    element_info: Tuple[str, ...]
    si_o: Optional[BondRange] = None
    al_o: Optional[BondRange] = None


def _strip_rmc_comment(line: str) -> str:
    """RMC free-format のコメントを除いて strip する。"""
    # RMC_POT free-format では # / ! をコメントとして扱う入力が存在するため、
    # 解析側ではどちらも行末コメントとして安全側に除去する。
    for marker in ("#", "!"):
        if marker in line:
            line = line.split(marker, 1)[0]
    return line.strip()


def _parse_free_format_sections(text: str) -> List[Tuple[str, List[str]]]:
    """RMC_POT free-format ``[ TAG ]`` セクションを順序保持で読む。"""
    sections: List[Tuple[str, List[str]]] = []
    current_name: Optional[str] = None
    current_lines: List[str] = []

    section_pattern = re.compile(r"^\s*\[\s*([A-Za-z0-9_-]+)\s*\]\s*$")

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name is not None:
            sections.append((current_name.upper(), current_lines))
        current_name = None
        current_lines = []

    for raw_line in text.splitlines():
        match = section_pattern.match(raw_line)
        if match:
            flush()
            current_name = match.group(1)
            continue

        if current_name is not None:
            line = _strip_rmc_comment(raw_line)
            if line:
                current_lines.append(line)

    flush()
    return sections


def _split_key_values(line: str) -> Tuple[str, List[str]]:
    """RMC free-format の KEY value... または KEY = value... を分解する。"""
    cleaned = line.replace("=", " ").replace(":", " ")
    tokens = cleaned.split()
    if not tokens:
        return "", []
    return tokens[0].upper(), tokens[1:]


def load_zeolite_rmc_config_from_dat(path: str | Path) -> ZeoliteRmcConfig:
    """RMC_POT free-format ``*.dat`` から解析用パラメータを取得する。

    取得対象:
        - ``[ GENERAL ] / CHEMICAL-SYMBOLS``
        - ``[ COORD ] / CENT-TYPE``
        - ``[ COORD ] / NEIGH-TYPE_FROM_TO``

    Si->O および Al->O の COORD neighbour range をゼオライト解析の
    T-O bond range として使用する。

    Raises:
        ValueError: 必要な element 情報または COORD range が取得できない場合。
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = _parse_free_format_sections(text)

    element_info: Optional[Tuple[str, ...]] = None

    for section_name, lines in sections:
        if section_name != "GENERAL":
            continue
        for line in lines:
            key, values = _split_key_values(line)
            if key == "CHEMICAL-SYMBOLS" and values:
                element_info = tuple(values)

    if not element_info:
        raise ValueError(
            f"{path}: [ GENERAL ] CHEMICAL-SYMBOLS を取得できません。"
        )

    type_to_element = {
        index + 1: symbol
        for index, symbol in enumerate(element_info)
    }

    ranges: Dict[str, BondRange] = {}

    for section_name, lines in sections:
        if section_name != "COORD":
            continue

        central_type: Optional[int] = None
        neighbors: List[Tuple[int, float, float]] = []

        for line in lines:
            key, values = _split_key_values(line)

            if key == "CENT-TYPE" and values:
                central_type = int(values[0])

            elif key == "NEIGH-TYPE_FROM_TO" and len(values) >= 3:
                neighbors.append(
                    (
                        int(values[0]),
                        float(values[1]),
                        float(values[2]),
                    )
                )

        if central_type is None:
            continue

        central_element = type_to_element.get(central_type)

        for neighbor_type, minimum, maximum in neighbors:
            neighbor_element = type_to_element.get(neighbor_type)

            if central_element == "Si" and neighbor_element == "O":
                ranges["Si"] = (minimum, maximum)
            elif central_element == "Al" and neighbor_element == "O":
                ranges["Al"] = (minimum, maximum)

    if "Si" not in ranges:
        raise ValueError(f"{path}: COORD の Si -> O range を取得できません。")
    if "Al" not in ranges:
        raise ValueError(f"{path}: COORD の Al -> O range を取得できません。")

    return ZeoliteRmcConfig(
        source=str(path),
        element_info=element_info,
        si_o=ranges["Si"],
        al_o=ranges["Al"],
    )


def _ast_literal(node: ast.AST) -> object:
    """安全に評価可能な Python literal のみ取り出す。"""
    return ast.literal_eval(node)


def _active_method_calls(
    tree: ast.AST,
    method_name: str,
) -> List[ast.Call]:
    """コメントアウトされていない指定メソッド呼び出しを AST から取得する。"""
    calls: List[ast.Call] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == method_name
        ):
            calls.append(node)

    calls.sort(key=lambda call: getattr(call, "lineno", 0))
    return calls


def _keyword_literal(call: ast.Call, name: str) -> object:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _ast_literal(keyword.value)
    raise KeyError(name)


def load_zeolite_rmc_config_from_init(path: str | Path) -> ZeoliteRmcConfig:
    """``rmc_init*.py`` の有効な RmcPotDat 設定から解析条件を取得する。

    Python ファイルは実行しない。AST で、
    ``set_element_info()`` と ``set_coord_constraint()`` の
    コメントアウトされていない呼び出しだけを読む。

    これにより rmc_init 自体に副作用があっても解析時には実行されない。
    """
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    element_calls = _active_method_calls(tree, "set_element_info")
    if not element_calls:
        raise ValueError(f"{path}: set_element_info() が見つかりません。")

    # rmc_init では過去設定がコメントとして残るため、AST に現れる
    # 最後の有効 call を現在設定として採用する。
    element_call = element_calls[-1]
    if not element_call.args:
        raise ValueError(f"{path}: set_element_info() の引数を取得できません。")

    element_info = tuple(str(x) for x in _ast_literal(element_call.args[0]))
    type_to_element = {
        index + 1: symbol
        for index, symbol in enumerate(element_info)
    }

    ranges: Dict[str, BondRange] = {}

    for call in _active_method_calls(tree, "set_coord_constraint"):
        try:
            central_type = int(_keyword_literal(call, "central_type"))
            neighbors = _keyword_literal(call, "neighbors")
        except (KeyError, ValueError, TypeError):
            continue

        central_element = type_to_element.get(central_type)

        for neighbor in neighbors:
            if len(neighbor) < 3:
                continue

            neighbor_type = int(neighbor[0])
            minimum = float(neighbor[1])
            maximum = float(neighbor[2])
            neighbor_element = type_to_element.get(neighbor_type)

            if central_element == "Si" and neighbor_element == "O":
                ranges["Si"] = (minimum, maximum)
            elif central_element == "Al" and neighbor_element == "O":
                ranges["Al"] = (minimum, maximum)

    if "Si" not in ranges:
        raise ValueError(
            f"{path}: active set_coord_constraint() から Si -> O range を取得できません。"
        )
    if "Al" not in ranges:
        raise ValueError(
            f"{path}: active set_coord_constraint() から Al -> O range を取得できません。"
        )

    return ZeoliteRmcConfig(
        source=str(path),
        element_info=element_info,
        si_o=ranges["Si"],
        al_o=ranges["Al"],
    )


def rmc_config_to_cutoffs(config: ZeoliteRmcConfig) -> ZeoliteCutoffs:
    """RMC 設定を ``ZeoliteCutoffs`` に変換する。"""
    if config.si_o is None or config.al_o is None:
        raise ValueError(
            f"{config.source}: Si-O / Al-O の両 range が必要です。"
        )

    return ZeoliteCutoffs(
        si_o=config.si_o,
        al_o=config.al_o,
    )


def find_rmc_parameter_source(
    directory: str | Path = ".",
) -> Optional[Path]:
    """解析ディレクトリから RMC parameter source を自動探索する。

    優先順位:
        1. ``*.dat``
        2. ``rmc_init.py``
        3. ``rmc_init*.py``

    ``*.dat`` が複数ある場合は basename が ``aaa.dat`` のものを優先し、
    それ以外は名前順の最初を返す。
    """
    directory = Path(directory)

    dat_files = sorted(directory.glob("*.dat"))
    if dat_files:
        for path in dat_files:
            if path.name == "aaa.dat":
                return path
        return dat_files[0]

    exact_init = directory / "rmc_init.py"
    if exact_init.exists():
        return exact_init

    init_files = sorted(directory.glob("rmc_init*.py"))
    if init_files:
        return init_files[0]

    return None


def load_zeolite_rmc_config(
    source: str | Path,
) -> ZeoliteRmcConfig:
    """``*.dat`` または ``rmc_init*.py`` を拡張子から自動判定して読む。"""
    source = Path(source)

    if source.suffix.lower() == ".dat":
        return load_zeolite_rmc_config_from_dat(source)

    if source.suffix.lower() == ".py":
        return load_zeolite_rmc_config_from_init(source)

    raise ValueError(
        f"未対応の RMC parameter source です: {source} "
        "(*.dat または *.py を指定してください)"
    )


@dataclass(frozen=True)
class ZeoliteCriteria:
    """RMC 構造を zeolite-like と判定するための明示的閾値。

    Notes:
        これらは IZA の正式な定義値ではない。
        RMC 途中構造を「ゼオライト型構造空間から逸脱していないか」
        スクリーニングするための実務的閾値である。

        binary 判定だけでなく、必ず各連続量も確認すること。
    """

    min_t4_fraction: float = 0.90
    min_bridging_o_fraction: float = 0.90
    min_largest_component_fraction: float = 0.95
    require_3d_periodic_network: bool = True


@dataclass(frozen=True)
class PeriodicEdge:
    """周期グラフの無向 edge。

    shift は node_u のセルから見た node_v の周期像を表す整数格子ベクトル。
    """

    node_u: int
    node_v: int
    shift: Vector3i


def _validate_range(distance_range: BondRange, name: str) -> None:
    minimum, maximum = distance_range
    if minimum < 0.0:
        raise ValueError(f"{name}: minimum は 0 以上で指定してください。")
    if maximum <= minimum:
        raise ValueError(f"{name}: maximum は minimum より大きくしてください。")


def _symbol(structure: Structure, index: int) -> str:
    return structure[index].specie.symbol


def _t_indices(structure: Structure) -> List[int]:
    return [
        i
        for i, site in enumerate(structure)
        if site.specie.symbol in {"Si", "Al"}
    ]


def _o_indices(structure: Structure) -> List[int]:
    return [
        i
        for i, site in enumerate(structure)
        if site.specie.symbol == "O"
    ]


def validate_framework_elements(structure: Structure) -> None:
    """Si/Al/O を含む構造であることを確認する。

    Na や H などの非骨格元素が含まれていてもよい。
    """
    elements = {site.specie.symbol for site in structure}

    if "O" not in elements:
        raise ValueError("構造中に O がありません。")

    if not ({"Si", "Al"} & elements):
        raise ValueError("構造中に Si または Al がありません。")


def _distance_and_image(
    structure: Structure,
    index_i: int,
    index_j: int,
) -> Tuple[float, Vector3i]:
    """i から見た j の最近接周期像までの距離と image を返す。"""
    frac_i = structure[index_i].frac_coords
    frac_j = structure[index_j].frac_coords
    distance, image = structure.lattice.get_distance_and_image(
        frac_i,
        frac_j,
    )
    image_tuple = tuple(int(x) for x in np.asarray(image, dtype=int))
    return float(distance), image_tuple


def build_to_bonds(
    structure: Structure,
    cutoffs: ZeoliteCutoffs = ZeoliteCutoffs(),
) -> List[PeriodicEdge]:
    """T=(Si,Al)-O bond を cutoff から作る。

    Returns:
        T 原子を node_u、O を node_v とする PeriodicEdge の一覧。
    """
    _validate_range(cutoffs.si_o, "Si-O")
    _validate_range(cutoffs.al_o, "Al-O")
    validate_framework_elements(structure)

    edges: List[PeriodicEdge] = []
    oxygens = _o_indices(structure)

    for t_index in _t_indices(structure):
        t_symbol = _symbol(structure, t_index)
        minimum, maximum = cutoffs.range_for_t(t_symbol)

        for o_index in oxygens:
            distance, image = _distance_and_image(
                structure,
                t_index,
                o_index,
            )
            if minimum <= distance <= maximum:
                edges.append(
                    PeriodicEdge(
                        node_u=t_index,
                        node_v=o_index,
                        shift=image,
                    )
                )

    return edges


def _to_neighbor_maps(
    edges: Sequence[PeriodicEdge],
) -> Tuple[Dict[int, List[Tuple[int, Vector3i]]], Dict[int, List[Tuple[int, Vector3i]]]]:
    """T->O と O->T の周期 image 付き近接辞書を作る。"""
    t_to_o: Dict[int, List[Tuple[int, Vector3i]]] = defaultdict(list)
    o_to_t: Dict[int, List[Tuple[int, Vector3i]]] = defaultdict(list)

    for edge in edges:
        t_index = edge.node_u
        o_index = edge.node_v
        shift = edge.shift
        t_to_o[t_index].append((o_index, shift))
        o_to_t[o_index].append(
            (
                t_index,
                (-shift[0], -shift[1], -shift[2]),
            )
        )

    return dict(t_to_o), dict(o_to_t)


def coordination_distributions(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[str, object]:
    """Si/Al の O 配位数と O の T 配位数分布を計算する。"""
    t_to_o, o_to_t = _to_neighbor_maps(edges)

    si_counts: Counter[int] = Counter()
    al_counts: Counter[int] = Counter()
    o_counts: Counter[int] = Counter()

    t_details: List[Dict[str, object]] = []
    o_details: List[Dict[str, object]] = []

    for t_index in _t_indices(structure):
        symbol = _symbol(structure, t_index)
        count = len(t_to_o.get(t_index, []))

        if symbol == "Si":
            si_counts[count] += 1
        elif symbol == "Al":
            al_counts[count] += 1

        t_details.append(
            {
                "index": t_index,
                "vasp_index": t_index + 1,
                "element": symbol,
                "o_coordination": count,
            }
        )

    for o_index in _o_indices(structure):
        count = len(o_to_t.get(o_index, []))
        o_counts[count] += 1
        o_details.append(
            {
                "index": o_index,
                "vasp_index": o_index + 1,
                "t_coordination": count,
            }
        )

    total_t = len(_t_indices(structure))
    total_o = len(_o_indices(structure))
    t4_count = si_counts.get(4, 0) + al_counts.get(4, 0)
    o2_count = o_counts.get(2, 0)

    t4_fraction = t4_count / total_t if total_t else 0.0
    bridging_o_fraction = o2_count / total_o if total_o else 0.0

    return {
        "si_o_coordination": dict(sorted(si_counts.items())),
        "al_o_coordination": dict(sorted(al_counts.items())),
        "o_t_coordination": dict(sorted(o_counts.items())),
        "total_t": total_t,
        "total_o": total_o,
        "t4_count": t4_count,
        "t4_fraction": t4_fraction,
        "bridging_o_count": o2_count,
        "bridging_o_fraction": bridging_o_fraction,
        "t_details": t_details,
        "o_details": o_details,
    }


def _vector_to_image(
    structure: Structure,
    center_index: int,
    neighbor_index: int,
    image: Vector3i,
) -> np.ndarray:
    """center から指定周期像の neighbor への Cartesian vector を返す。"""
    frac_center = np.asarray(structure[center_index].frac_coords, dtype=float)
    frac_neighbor = np.asarray(structure[neighbor_index].frac_coords, dtype=float)
    delta_frac = frac_neighbor + np.asarray(image, dtype=float) - frac_center
    return np.asarray(structure.lattice.get_cartesian_coords(delta_frac), dtype=float)


def _angle_degrees(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    norm_a = float(np.linalg.norm(vector_a))
    norm_b = float(np.linalg.norm(vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("ゼロ長ベクトルから角度は計算できません。")

    cosine = float(np.dot(vector_a, vector_b) / (norm_a * norm_b))
    cosine = max(-1.0, min(1.0, cosine))
    return degrees(acos(cosine))


def _summary(values: Sequence[float]) -> Dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "minimum": None,
            "maximum": None,
        }

    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "std": float(array.std(ddof=0)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def bond_length_statistics(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[str, object]:
    """Si-O / Al-O bond length の統計を返す。"""
    values: Dict[str, List[float]] = {
        "Si-O": [],
        "Al-O": [],
    }

    for edge in edges:
        t_symbol = _symbol(structure, edge.node_u)
        vector = _vector_to_image(
            structure,
            edge.node_u,
            edge.node_v,
            edge.shift,
        )
        values[f"{t_symbol}-O"].append(float(np.linalg.norm(vector)))

    return {
        "Si-O": _summary(values["Si-O"]),
        "Al-O": _summary(values["Al-O"]),
        "values": values,
    }


def angle_statistics(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[str, object]:
    """O-T-O と T-O-T の角度分布を計算する。"""
    t_to_o, o_to_t = _to_neighbor_maps(edges)

    o_si_o: List[float] = []
    o_al_o: List[float] = []
    si_o_si: List[float] = []
    si_o_al: List[float] = []
    al_o_al: List[float] = []

    for t_index, neighbors in t_to_o.items():
        target = o_si_o if _symbol(structure, t_index) == "Si" else o_al_o

        for (o_i, image_i), (o_j, image_j) in combinations(neighbors, 2):
            vector_i = _vector_to_image(structure, t_index, o_i, image_i)
            vector_j = _vector_to_image(structure, t_index, o_j, image_j)
            target.append(_angle_degrees(vector_i, vector_j))

    for o_index, neighbors in o_to_t.items():
        for (t_i, image_i), (t_j, image_j) in combinations(neighbors, 2):
            vector_i = _vector_to_image(structure, o_index, t_i, image_i)
            vector_j = _vector_to_image(structure, o_index, t_j, image_j)
            angle = _angle_degrees(vector_i, vector_j)

            pair = tuple(sorted((_symbol(structure, t_i), _symbol(structure, t_j))))
            if pair == ("Si", "Si"):
                si_o_si.append(angle)
            elif pair == ("Al", "Si"):
                si_o_al.append(angle)
            elif pair == ("Al", "Al"):
                al_o_al.append(angle)

    return {
        "O-Si-O": _summary(o_si_o),
        "O-Al-O": _summary(o_al_o),
        "Si-O-Si": _summary(si_o_si),
        "Si-O-Al": _summary(si_o_al),
        "Al-O-Al": _summary(al_o_al),
        "values": {
            "O-Si-O": o_si_o,
            "O-Al-O": o_al_o,
            "Si-O-Si": si_o_si,
            "Si-O-Al": si_o_al,
            "Al-O-Al": al_o_al,
        },
    }


def _framework_adjacency(
    edges: Sequence[PeriodicEdge],
) -> Dict[int, List[Tuple[int, Vector3i]]]:
    adjacency: Dict[int, List[Tuple[int, Vector3i]]] = defaultdict(list)

    for edge in edges:
        u = edge.node_u
        v = edge.node_v
        sx, sy, sz = edge.shift
        adjacency[u].append((v, (sx, sy, sz)))
        adjacency[v].append((u, (-sx, -sy, -sz)))

    return dict(adjacency)


def _integer_rank(vectors: Sequence[Vector3i]) -> int:
    if not vectors:
        return 0

    matrix = np.asarray(vectors, dtype=float)
    return int(np.linalg.matrix_rank(matrix, tol=1.0e-10))


def periodic_network_statistics(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[str, object]:
    """T-O framework の連結成分と周期次元を求める。

    周期次元は periodic graph の spanning tree を作り、
    non-tree edge が生成する格子並進ベクトルの rank から求める。

    rank=3 なら、骨格は a,b,c の独立3方向へ周期的に連結している。
    """
    framework_nodes = set(_t_indices(structure)) | set(_o_indices(structure))
    adjacency = _framework_adjacency(edges)

    visited_global: Set[int] = set()
    components: List[Dict[str, object]] = []

    for start in sorted(framework_nodes):
        if start in visited_global:
            continue

        offsets: Dict[int, np.ndarray] = {
            start: np.zeros(3, dtype=int)
        }
        queue: deque[int] = deque([start])
        component_nodes: Set[int] = set()
        cycle_translations: List[Vector3i] = []

        while queue:
            u = queue.popleft()
            component_nodes.add(u)
            visited_global.add(u)

            for v, shift_tuple in adjacency.get(u, []):
                shift = np.asarray(shift_tuple, dtype=int)
                proposed = offsets[u] + shift

                if v not in offsets:
                    offsets[v] = proposed
                    queue.append(v)
                else:
                    residual = proposed - offsets[v]
                    if np.any(residual != 0):
                        cycle_translations.append(
                            tuple(int(x) for x in residual)
                        )

        dimension = _integer_rank(cycle_translations)
        components.append(
            {
                "size": len(component_nodes),
                "nodes": sorted(component_nodes),
                "periodic_dimension": dimension,
                "cycle_translations": sorted(set(cycle_translations)),
            }
        )

    components.sort(key=lambda item: int(item["size"]), reverse=True)

    total_framework = len(framework_nodes)
    largest_size = int(components[0]["size"]) if components else 0
    largest_fraction = (
        largest_size / total_framework
        if total_framework
        else 0.0
    )
    largest_dimension = (
        int(components[0]["periodic_dimension"])
        if components
        else 0
    )

    return {
        "component_count": len(components),
        "largest_component_size": largest_size,
        "largest_component_fraction": largest_fraction,
        "largest_component_periodic_dimension": largest_dimension,
        "components": components,
    }


def build_tt_graph(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[int, Set[int]]:
    """bridging O を edge とみなした T-T quotient graph を作る。

    Notes:
        O が2個以上の T に結合している場合、その全組合せを T-T edge にする。
        ring 解析は原子番号だけからなる有限周期セルの quotient graph 上で行う。
        IZA の strict primitive-ring / vertex-symbol 解析とは異なる。
    """
    _, o_to_t = _to_neighbor_maps(edges)
    graph: Dict[int, Set[int]] = {
        index: set()
        for index in _t_indices(structure)
    }

    for neighbors in o_to_t.values():
        t_indices = sorted({index for index, _ in neighbors})
        for t_i, t_j in combinations(t_indices, 2):
            if t_i == t_j:
                continue
            graph[t_i].add(t_j)
            graph[t_j].add(t_i)

    return graph


def _shortest_path_without_edge(
    graph: Mapping[int, Set[int]],
    start: int,
    goal: int,
    removed_edge: Tuple[int, int],
    max_edges: int,
) -> Optional[List[int]]:
    queue: deque[List[int]] = deque([[start]])
    visited_depth: Dict[int, int] = {start: 0}
    u_removed, v_removed = removed_edge

    while queue:
        path = queue.popleft()
        u = path[-1]
        depth = len(path) - 1

        if depth >= max_edges:
            continue

        for v in graph.get(u, set()):
            if (
                (u == u_removed and v == v_removed)
                or (u == v_removed and v == u_removed)
            ):
                continue

            new_path = path + [v]
            if v == goal:
                return new_path

            new_depth = depth + 1
            previous_depth = visited_depth.get(v)
            if previous_depth is None or new_depth < previous_depth:
                visited_depth[v] = new_depth
                queue.append(new_path)

    return None


def shortest_ring_statistics(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
    max_ring_size: int = 16,
) -> Dict[str, object]:
    """T-T network の shortest-ring 統計を近似的に求める。

    各 T-T edge を一度除去し、その両端を結ぶ最短経路を探索する。
    edge + shortest path を一つの shortest ring とみなす。

    同じ原子集合を持つ ring は一つにまとめる。
    """
    if max_ring_size < 3:
        raise ValueError("max_ring_size は 3 以上で指定してください。")

    graph = build_tt_graph(structure, edges)
    unique_rings: Set[Tuple[int, ...]] = set()

    undirected_edges = sorted(
        {
            tuple(sorted((u, v)))
            for u, neighbors in graph.items()
            for v in neighbors
            if u != v
        }
    )

    for u, v in undirected_edges:
        path = _shortest_path_without_edge(
            graph=graph,
            start=u,
            goal=v,
            removed_edge=(u, v),
            max_edges=max_ring_size - 1,
        )
        if path is None:
            continue

        ring_size = len(path)
        if 3 <= ring_size <= max_ring_size:
            ring_nodes = tuple(sorted(set(path)))
            if len(ring_nodes) == ring_size:
                unique_rings.add(ring_nodes)

    counts: Counter[int] = Counter(len(ring) for ring in unique_rings)

    return {
        "max_ring_size": max_ring_size,
        "ring_counts": dict(sorted(counts.items())),
        "ring_count_total": len(unique_rings),
        "rings": sorted(unique_rings, key=lambda ring: (len(ring), ring)),
    }


def loewenstein_statistics(
    structure: Structure,
    edges: Sequence[PeriodicEdge],
) -> Dict[str, object]:
    """bridging O の T-T 組から Al-O-Al の割合を求める。"""
    _, o_to_t = _to_neighbor_maps(edges)

    total_pairs = 0
    al_o_al_pairs = 0
    si_o_al_pairs = 0
    si_o_si_pairs = 0

    for neighbors in o_to_t.values():
        unique_t = sorted({index for index, _ in neighbors})

        for t_i, t_j in combinations(unique_t, 2):
            total_pairs += 1
            pair = tuple(sorted((_symbol(structure, t_i), _symbol(structure, t_j))))

            if pair == ("Al", "Al"):
                al_o_al_pairs += 1
            elif pair == ("Al", "Si"):
                si_o_al_pairs += 1
            elif pair == ("Si", "Si"):
                si_o_si_pairs += 1

    fraction = al_o_al_pairs / total_pairs if total_pairs else 0.0

    return {
        "total_t_o_t_pairs": total_pairs,
        "Si-O-Si": si_o_si_pairs,
        "Si-O-Al": si_o_al_pairs,
        "Al-O-Al": al_o_al_pairs,
        "al_o_al_fraction": fraction,
    }


def framework_density(structure: Structure) -> float:
    """framework density [T atoms / 1000 Å^3] を返す。"""
    total_t = len(_t_indices(structure))
    return 1000.0 * total_t / float(structure.volume)


def evaluate_zeolite_like(
    coordination: Mapping[str, object],
    network: Mapping[str, object],
    criteria: ZeoliteCriteria = ZeoliteCriteria(),
) -> Dict[str, object]:
    """連続指標から zeolite-like screening 判定を行う。"""
    t4_fraction = float(coordination["t4_fraction"])
    bridging_o_fraction = float(coordination["bridging_o_fraction"])
    largest_fraction = float(network["largest_component_fraction"])
    periodic_dimension = int(network["largest_component_periodic_dimension"])

    checks = {
        "t4_fraction": t4_fraction >= criteria.min_t4_fraction,
        "bridging_o_fraction": (
            bridging_o_fraction >= criteria.min_bridging_o_fraction
        ),
        "largest_component_fraction": (
            largest_fraction >= criteria.min_largest_component_fraction
        ),
        "periodic_network": (
            periodic_dimension == 3
            if criteria.require_3d_periodic_network
            else True
        ),
    }

    return {
        "is_zeolite_like": all(checks.values()),
        "checks": checks,
        "criteria": asdict(criteria),
    }


def analyze_zeolite(
    structure: Structure,
    *,
    cutoffs: ZeoliteCutoffs = ZeoliteCutoffs(),
    criteria: ZeoliteCriteria = ZeoliteCriteria(),
    max_ring_size: int = 16,
    calculate_rings: bool = True,
) -> Dict[str, object]:
    """ゼオライト型フレームワークを一括解析する。

    Args:
        structure: pymatgen ``Structure``。
        cutoffs: Si-O / Al-O bond 判定距離。
        criteria: zeolite-like screening の閾値。
        max_ring_size: shortest-ring 探索の最大員環。
        calculate_rings: False なら ring 解析を省略する。

    Returns:
        解析結果をまとめた辞書。
    """
    validate_framework_elements(structure)

    edges = build_to_bonds(
        structure=structure,
        cutoffs=cutoffs,
    )
    coordination = coordination_distributions(
        structure=structure,
        edges=edges,
    )
    bond_lengths = bond_length_statistics(
        structure=structure,
        edges=edges,
    )
    angles = angle_statistics(
        structure=structure,
        edges=edges,
    )
    network = periodic_network_statistics(
        structure=structure,
        edges=edges,
    )
    loewenstein = loewenstein_statistics(
        structure=structure,
        edges=edges,
    )

    if calculate_rings:
        rings = shortest_ring_statistics(
            structure=structure,
            edges=edges,
            max_ring_size=max_ring_size,
        )
    else:
        rings = {
            "max_ring_size": max_ring_size,
            "ring_counts": {},
            "ring_count_total": 0,
            "rings": [],
            "calculated": False,
        }

    screening = evaluate_zeolite_like(
        coordination=coordination,
        network=network,
        criteria=criteria,
    )

    return {
        "atom_count": len(structure),
        "volume_A3": float(structure.volume),
        "framework_density_T_per_1000A3": framework_density(structure),
        "cutoffs": asdict(cutoffs),
        "coordination": coordination,
        "bond_lengths": bond_lengths,
        "angles": angles,
        "network": network,
        "rings": rings,
        "loewenstein": loewenstein,
        "screening": screening,
    }
