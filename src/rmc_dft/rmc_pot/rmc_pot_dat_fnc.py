#!/usr/bin/env python3
"""RMC_POT Fixed Neighbour Constraint (``*.fnc``) file support.

The FNC file is independent of whether the accompanying ``*.dat`` file uses
fixed or free format.  Atom indices in this file are one-based RMC indices in
the final ``*.cfg`` configuration.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from x_logger import XLogger


@dataclass(frozen=True)
class FncNeighbour:
    """One neighbour entry in an RMC_POT FNC file."""

    atom_index: int
    constraint_type: int


class RmcPotDatFnc:
    """Create, read, edit, validate, and write an RMC_POT ``*.fnc`` file.

    The low-level methods operate on final one-based RMC atom indices.  The
    template methods expand local molecule indices to final RMC indices, but
    they never infer connectivity from element names or distances.
    """

    def __init__(
        self,
        name: str,
        *,
        atom_count: Optional[int] = None,
        auto_write: bool = True,
        logger: Optional[XLogger] = None,
    ) -> None:
        self._path = self._resolve_path(name)
        self._auto_write = bool(auto_write)
        self._logger = logger or XLogger()
        self._title = "Fixed neighbours constraints (.FNC) file"
        self._ranges: Dict[int, Tuple[float, float]] = {}
        self._atoms: Dict[int, List[FncNeighbour]] = {}
        self._atom_count = 0

        if self._path.exists():
            self.load()
        elif atom_count is not None:
            self.initialize(atom_count, auto_write=auto_write)

    @staticmethod
    def _resolve_path(name: str) -> Path:
        path = Path(name)
        if path.suffix.lower() != ".fnc":
            path = Path(str(path) + ".fnc")
        return path

    @property
    def path(self) -> Path:
        return self._path

    def initialize(
        self,
        atom_count: int,
        *,
        title: Optional[str] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        count = int(atom_count)
        if count < 1:
            raise ValueError("atom_count は1以上である必要があります。")
        self._atom_count = count
        self._atoms = {index: [] for index in range(1, count + 1)}
        self._ranges = {}
        if title is not None:
            self._title = str(title)
        self._write_if_requested(auto_write)

    def load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(str(self._path))

        lines = self._path.read_text(encoding="utf-8").splitlines()
        if not lines:
            raise ValueError("FNCファイルが空です。")
        self._title = lines[0].strip()

        marker = None
        for index, line in enumerate(lines):
            if "No. of possible rmin-rmax pairs" in line:
                marker = index
                break
        if marker is None:
            raise ValueError("FNC type header が見つかりません。")

        try:
            type_count = int(lines[marker + 1].split()[0])
            rmins = [float(value) for value in lines[marker + 2].split()]
            rmaxs = [float(value) for value in lines[marker + 3].split()]
        except (IndexError, ValueError) as exc:
            raise ValueError("FNC type header を読み取れません。") from exc
        if len(rmins) != type_count or len(rmaxs) != type_count:
            raise ValueError("FNC type数とrmin/rmax数が一致しません。")
        self._ranges = {
            index: (rmins[index - 1], rmaxs[index - 1])
            for index in range(1, type_count + 1)
        }

        cursor = marker + 4
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            raise ValueError("FNC atom_count が見つかりません。")
        self._atom_count = int(lines[cursor].split()[0])
        cursor += 1
        self._atoms = {}

        while len(self._atoms) < self._atom_count:
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            if cursor >= len(lines):
                raise ValueError("FNC atom entry が不足しています。")
            tokens = lines[cursor].split()
            cursor += 1
            if len(tokens) < 2:
                raise ValueError("FNC atom header が不正です。")
            atom_index = int(tokens[0])
            neighbour_count = int(tokens[1])
            neighbours: List[FncNeighbour] = []
            if neighbour_count:
                if cursor + 1 >= len(lines):
                    raise ValueError("FNC neighbour entry が不足しています。")
                indices = [int(value) for value in lines[cursor].split()]
                types = [int(value) for value in lines[cursor + 1].split()]
                cursor += 2
                if len(indices) != neighbour_count or len(types) != neighbour_count:
                    raise ValueError("FNC neighbour数がheaderと一致しません。")
                neighbours = [
                    FncNeighbour(index, constraint_type)
                    for index, constraint_type in zip(indices, types)
                ]
            self._atoms[atom_index] = neighbours

        self.validate()
        self._logger.info("[rmc_pot_dat_fnc] load %s" % self._path)

    def write(self, out_name: Optional[str] = None) -> None:
        self.validate()
        path = self._path if out_name is None else self._resolve_path(out_name)
        type_count = len(self._ranges)
        output = [
            self._title,
            "",
            " No. of possible rmin-rmax pairs:",
            " %d" % type_count,
            " ".join(self._format_float(self._ranges[index][0]) for index in range(1, type_count + 1)),
            " ".join(self._format_float(self._ranges[index][1]) for index in range(1, type_count + 1)),
            "",
            " %d" % self._atom_count,
            "",
        ]
        for atom_index in range(1, self._atom_count + 1):
            neighbours = self._atoms[atom_index]
            output.append("%d %d" % (atom_index, len(neighbours)))
            if neighbours:
                output.append(" ".join(str(item.atom_index) for item in neighbours))
                output.append(" ".join(str(item.constraint_type) for item in neighbours))
        path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
        self._logger.info("[rmc_pot_dat_fnc] write %s" % path)

    @staticmethod
    def _format_float(value: float) -> str:
        return "%.12g" % float(value)

    def set_title(self, title: str, *, auto_write: Optional[bool] = None) -> None:
        self._title = str(title)
        self._write_if_requested(auto_write)

    def get_title(self) -> str:
        return self._title

    def get_atom_count(self) -> int:
        return self._atom_count

    def set_distance_range(
        self,
        constraint_type: int,
        rmin: float,
        rmax: float,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        type_id = int(constraint_type)
        if type_id < 1:
            raise ValueError("constraint_type は1以上です。")
        if type_id > len(self._ranges) + 1 and type_id not in self._ranges:
            raise ValueError("constraint_type は1から連番で追加してください。")
        lower = float(rmin)
        upper = float(rmax)
        if lower >= upper:
            raise ValueError("rmin は rmax より小さい必要があります。")
        self._ranges[type_id] = (lower, upper)
        self._write_if_requested(auto_write)

    def set_distance_ranges(
        self,
        ranges: Union[Mapping[int, Tuple[float, float]], Sequence[Tuple[float, float]]],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        items = ranges.items() if isinstance(ranges, Mapping) else enumerate(ranges, 1)
        new_ranges: Dict[int, Tuple[float, float]] = {}
        for type_id, pair in items:
            if len(pair) != 2:
                raise ValueError("range は (rmin, rmax) で指定してください。")
            lower = float(pair[0])
            upper = float(pair[1])
            if lower >= upper:
                raise ValueError("rmin は rmax より小さい必要があります。")
            new_ranges[int(type_id)] = (lower, upper)
        if sorted(new_ranges) != list(range(1, len(new_ranges) + 1)):
            raise ValueError("constraint_type は1から連番である必要があります。")
        self._ranges = new_ranges
        self._write_if_requested(auto_write)

    def get_distance_ranges(self) -> Dict[int, Tuple[float, float]]:
        return dict(self._ranges)

    def set_atom_neighbours(
        self,
        atom_index: int,
        neighbours: Iterable[Union[FncNeighbour, Tuple[int, int]]],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        atom = self._check_atom_index(atom_index)
        converted: List[FncNeighbour] = []
        for value in neighbours:
            item = value if isinstance(value, FncNeighbour) else FncNeighbour(int(value[0]), int(value[1]))
            self._check_atom_index(item.atom_index)
            self._check_constraint_type(item.constraint_type)
            converted.append(item)
        self._atoms[atom] = self._unique_neighbours(converted)
        self._write_if_requested(auto_write)

    def get_atom_neighbours(self, atom_index: int) -> List[FncNeighbour]:
        atom = self._check_atom_index(atom_index)
        return list(self._atoms[atom])

    def add_neighbour(
        self,
        atom_index: int,
        neighbour_index: int,
        constraint_type: int,
        *,
        reciprocal: bool = False,
        auto_write: Optional[bool] = None,
    ) -> None:
        atom = self._check_atom_index(atom_index)
        neighbour = self._check_atom_index(neighbour_index)
        type_id = self._check_constraint_type(constraint_type)
        if atom == neighbour:
            raise ValueError("自己参照FNC pairは指定できません。")
        self._append_unique(atom, FncNeighbour(neighbour, type_id))
        if reciprocal:
            self._append_unique(neighbour, FncNeighbour(atom, type_id))
        self._write_if_requested(auto_write)

    def add_pair(
        self,
        atom_index1: int,
        atom_index2: int,
        constraint_type: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        self.add_neighbour(
            atom_index1,
            atom_index2,
            constraint_type,
            reciprocal=True,
            auto_write=auto_write,
        )

    def add_pairs(
        self,
        pairs: Iterable[Tuple[int, int, int]],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        for atom1, atom2, type_id in pairs:
            self.add_pair(atom1, atom2, type_id, auto_write=False)
        self._write_if_requested(auto_write)

    def remove_pair(
        self,
        atom_index1: int,
        atom_index2: int,
        *,
        reciprocal: bool = True,
        auto_write: Optional[bool] = None,
    ) -> None:
        atom1 = self._check_atom_index(atom_index1)
        atom2 = self._check_atom_index(atom_index2)
        self._atoms[atom1] = [item for item in self._atoms[atom1] if item.atom_index != atom2]
        if reciprocal:
            self._atoms[atom2] = [item for item in self._atoms[atom2] if item.atom_index != atom1]
        self._write_if_requested(auto_write)

    def clear_atom_neighbours(
        self,
        atom_index: int,
        *,
        reciprocal: bool = True,
        auto_write: Optional[bool] = None,
    ) -> None:
        atom = self._check_atom_index(atom_index)
        old = list(self._atoms[atom])
        self._atoms[atom] = []
        if reciprocal:
            for item in old:
                self._atoms[item.atom_index] = [
                    other for other in self._atoms[item.atom_index]
                    if other.atom_index != atom
                ]
        self._write_if_requested(auto_write)

    def add_template_instance(
        self,
        local_pairs: Iterable[Tuple[int, int, int]],
        local_to_rmc: Mapping[int, int],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """Expand one local molecular template to final RMC atom indices."""
        for local1, local2, type_id in local_pairs:
            if int(local1) not in local_to_rmc or int(local2) not in local_to_rmc:
                raise ValueError("local pair に対応するRMC indexがありません。")
            self.add_pair(
                int(local_to_rmc[int(local1)]),
                int(local_to_rmc[int(local2)]),
                int(type_id),
                auto_write=False,
            )
        self._write_if_requested(auto_write)

    def add_template_instances(
        self,
        local_pairs: Iterable[Tuple[int, int, int]],
        instances: Iterable[Mapping[int, int]],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        pairs = list(local_pairs)
        for mapping in instances:
            self.add_template_instance(pairs, mapping, auto_write=False)
        self._write_if_requested(auto_write)

    def add_group_complete_graph(
        self,
        atom_indices: Sequence[int],
        constraint_type: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """Constrain every pair within an explicitly supplied atom group."""
        values = [self._check_atom_index(value) for value in atom_indices]
        for i, atom1 in enumerate(values):
            for atom2 in values[i + 1:]:
                self.add_pair(atom1, atom2, constraint_type, auto_write=False)
        self._write_if_requested(auto_write)

    def validate(self, *, require_reciprocal: bool = True) -> None:
        if self._atom_count < 1:
            raise ValueError("atom_count が設定されていません。")
        if sorted(self._ranges) != list(range(1, len(self._ranges) + 1)):
            raise ValueError("constraint_type は1から連番である必要があります。")
        if sorted(self._atoms) != list(range(1, self._atom_count + 1)):
            raise ValueError("FNC atom entry は1からatom_countまで必要です。")
        for atom_index, neighbours in self._atoms.items():
            seen = set()
            for item in neighbours:
                self._check_atom_index(item.atom_index)
                self._check_constraint_type(item.constraint_type)
                key = (item.atom_index, item.constraint_type)
                if key in seen:
                    raise ValueError("FNC neighbourが重複しています: atom=%d" % atom_index)
                seen.add(key)
                if require_reciprocal:
                    reverse = FncNeighbour(atom_index, item.constraint_type)
                    if reverse not in self._atoms[item.atom_index]:
                        raise ValueError(
                            "FNC pairが相互登録されていません: %d-%d type=%d"
                            % (atom_index, item.atom_index, item.constraint_type)
                        )

    def as_pairs(self, *, unique: bool = True) -> List[Tuple[int, int, int]]:
        result: List[Tuple[int, int, int]] = []
        for atom_index in range(1, self._atom_count + 1):
            for item in self._atoms[atom_index]:
                if unique and atom_index > item.atom_index:
                    continue
                result.append((atom_index, item.atom_index, item.constraint_type))
        return result

    def _check_atom_index(self, atom_index: int) -> int:
        value = int(atom_index)
        if value < 1 or value > self._atom_count:
            raise ValueError("RMC atom indexが範囲外です: %d" % value)
        return value

    def _check_constraint_type(self, constraint_type: int) -> int:
        value = int(constraint_type)
        if value not in self._ranges:
            raise ValueError("未定義のFNC constraint_typeです: %d" % value)
        return value

    def _append_unique(self, atom_index: int, neighbour: FncNeighbour) -> None:
        current = self._atoms[atom_index]
        for item in current:
            if item.atom_index == neighbour.atom_index:
                if item.constraint_type != neighbour.constraint_type:
                    raise ValueError(
                        "同じFNC pairへ異なるconstraint_typeを重複指定しています。"
                    )
                return
        current.append(neighbour)
        current.sort(key=lambda item: (item.atom_index, item.constraint_type))

    @staticmethod
    def _unique_neighbours(values: Iterable[FncNeighbour]) -> List[FncNeighbour]:
        result: List[FncNeighbour] = []
        seen = set()
        for item in values:
            key = (item.atom_index, item.constraint_type)
            if key not in seen:
                seen.add(key)
                result.append(item)
        result.sort(key=lambda item: (item.atom_index, item.constraint_type))
        return result

    def _write_if_requested(self, auto_write: Optional[bool]) -> None:
        enabled = self._auto_write if auto_write is None else bool(auto_write)
        if enabled:
            self.write()
