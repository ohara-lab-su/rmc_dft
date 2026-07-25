#!/usr/bin/env python3
"""RMC_POT GROMACS-type topology (``*.top``/``*.itp``) support.

Topology files are independent of whether the accompanying ``*.dat`` file uses
fixed or free format.  Bonded topology uses local GROMACS serial indices, while
``[ atoms ]`` carries the first/second RMC indices that map each local atom to
the final ``*.cfg`` ordering.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from x_logger import XLogger

Number = Union[int, float]


@dataclass
class TopologySection:
    name: str
    lines: List[str] = field(default_factory=list)


class RmcPotDatTop:
    """Create, read, edit, validate, and write RMC_POT TOP/ITP files.

    Low-level section methods can represent every directive recognised by
    RMC_POT.  Typed methods cover the recognised topology records.  Convenience
    methods build reusable molecule templates or one explicit whole-cell
    network molecule.
    """

    KNOWN_SECTIONS = {
        "moleculetype",
        "atoms",
        "pairs",
        "bonds",
        "angles",
        "dihedrals",
        "exclusions",
        "virtual_sites2",
        "virtual_sites3",
        "virtual_sites4",
        "system",
        "molecules",
    }

    def __init__(
        self,
        name: str,
        *,
        auto_write: bool = True,
        logger: Optional[XLogger] = None,
    ) -> None:
        self._path = self._resolve_path(name)
        self._auto_write = bool(auto_write)
        self._logger = logger or XLogger()
        self._items: List[Union[str, TopologySection]] = []
        if self._path.exists():
            self.load()

    @staticmethod
    def _resolve_path(name: str) -> Path:
        path = Path(name)
        if path.suffix.lower() not in (".top", ".itp"):
            path = Path(str(path) + ".top")
        return path

    @property
    def path(self) -> Path:
        return self._path

    def clear(self, *, auto_write: Optional[bool] = None) -> None:
        self._items = []
        self._write_if_requested(auto_write)

    def load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(str(self._path))
        self._items = []
        current: Optional[TopologySection] = None
        for source_line in self._path.read_text(encoding="utf-8").splitlines():
            stripped = source_line.strip()
            if stripped.startswith("[") and "]" in stripped:
                name = stripped[1:stripped.index("]")].strip().lower()
                current = TopologySection(name)
                self._items.append(current)
                continue
            if current is None:
                self._items.append(source_line)
            else:
                current.lines.append(source_line)
        self._logger.info("[rmc_pot_dat_top] load %s" % self._path)

    def write(self, out_name: Optional[str] = None) -> None:
        self.validate()
        path = self._path if out_name is None else self._resolve_path(out_name)
        output: List[str] = []
        for item in self._items:
            if isinstance(item, str):
                output.append(item)
            else:
                output.append("[ %s ]" % item.name)
                output.extend(item.lines)
        path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
        self._logger.info("[rmc_pot_dat_top] write %s" % path)

    def add_raw_line(self, line: str = "", *, auto_write: Optional[bool] = None) -> None:
        self._items.append(str(line))
        self._write_if_requested(auto_write)

    def add_comment(self, comment: str, *, auto_write: Optional[bool] = None) -> None:
        text = str(comment)
        if not text.startswith(";"):
            text = "; " + text
        self.add_raw_line(text, auto_write=auto_write)

    def add_include(self, filename: str, *, auto_write: Optional[bool] = None) -> None:
        self.add_raw_line('#include "%s"' % str(filename), auto_write=auto_write)

    def add_ifdef(self, symbol: str, *, auto_write: Optional[bool] = None) -> None:
        self.add_raw_line("#ifdef %s" % str(symbol), auto_write=auto_write)

    def add_ifndef(self, symbol: str, *, auto_write: Optional[bool] = None) -> None:
        self.add_raw_line("#ifndef %s" % str(symbol), auto_write=auto_write)

    def add_else(self, *, auto_write: Optional[bool] = None) -> None:
        self.add_raw_line("#else", auto_write=auto_write)

    def add_endif(self, *, auto_write: Optional[bool] = None) -> None:
        self.add_raw_line("#endif", auto_write=auto_write)

    def add_section(
        self,
        name: str,
        *,
        auto_write: Optional[bool] = None,
    ) -> TopologySection:
        section = TopologySection(str(name).strip().lower())
        self._items.append(section)
        self._write_if_requested(auto_write)
        return section

    def get_sections(self, name: Optional[str] = None) -> List[TopologySection]:
        sections = [item for item in self._items if isinstance(item, TopologySection)]
        if name is None:
            return sections
        target = str(name).strip().lower()
        return [section for section in sections if section.name == target]

    def get_last_section(self, name: str) -> TopologySection:
        sections = self.get_sections(name)
        if not sections:
            raise ValueError("section がありません: %s" % name)
        return sections[-1]

    def add_section_line(
        self,
        section_name: str,
        line: str,
        *,
        create: bool = True,
        auto_write: Optional[bool] = None,
    ) -> None:
        sections = self.get_sections(section_name)
        if sections:
            section = sections[-1]
        elif create:
            section = self.add_section(section_name, auto_write=False)
        else:
            raise ValueError("section がありません: %s" % section_name)
        section.lines.append(str(line))
        self._write_if_requested(auto_write)

    def remove_sections(self, name: str, *, auto_write: Optional[bool] = None) -> None:
        target = str(name).strip().lower()
        self._items = [
            item for item in self._items
            if not isinstance(item, TopologySection) or item.name != target
        ]
        self._write_if_requested(auto_write)

    def begin_molecule_type(
        self,
        name: str,
        exclusions: int,
        *,
        index_offset: Optional[int] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        section = self.add_section("moleculetype", auto_write=False)
        line = "%s %d" % (str(name), int(exclusions))
        if index_offset is not None:
            line += " ; %d" % int(index_offset)
        section.lines.append(line)
        self._write_if_requested(auto_write)

    def add_atom(
        self,
        serial: int,
        atom_type: str,
        residue_number: int,
        residue_name: str,
        atom_name: str,
        charge_group: int,
        charge: float,
        mass: Optional[float],
        first_rmc_index: int,
        second_rmc_index: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        tokens = [
            str(int(serial)), str(atom_type), str(int(residue_number)),
            str(residue_name), str(atom_name), str(int(charge_group)),
            self._number(charge),
        ]
        if mass is not None:
            tokens.append(self._number(mass))
        line = " ".join(tokens) + " ; %d %d" % (
            int(first_rmc_index), int(second_rmc_index)
        )
        self.add_section_line("atoms", line, auto_write=auto_write)

    def add_virtual_atom(
        self,
        serial: int,
        atom_type: str,
        residue_number: int,
        residue_name: str,
        atom_name: str,
        charge_group: int,
        charge: float,
        *,
        mass: float = 0.0,
        auto_write: Optional[bool] = None,
    ) -> None:
        self.add_atom(
            serial, atom_type, residue_number, residue_name, atom_name,
            charge_group, charge, mass, 0, 0, auto_write=auto_write,
        )

    def add_pair(
        self,
        atom_i: int,
        atom_j: int,
        *,
        function_type: int = 1,
        v_parameter: Optional[float] = None,
        w_parameter: Optional[float] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        values: List[Union[int, float]] = [atom_i, atom_j, function_type]
        if (v_parameter is None) != (w_parameter is None):
            raise ValueError("V/W parameter は両方指定するか両方省略してください。")
        if v_parameter is not None and w_parameter is not None:
            values.extend([v_parameter, w_parameter])
        self.add_section_line("pairs", self._join(values), auto_write=auto_write)

    def add_bond(
        self,
        atom_i: int,
        atom_j: int,
        equilibrium_nm: float,
        force_constant: float,
        sigma: Optional[float] = None,
        *,
        function_type: int = 1,
        rmc_parameters_after_semicolon: bool = False,
        auto_write: Optional[bool] = None,
    ) -> None:
        base = self._join([atom_i, atom_j, function_type])
        parameters = self._join([equilibrium_nm, force_constant])
        if sigma is not None:
            parameters += " " + self._number(sigma)
        line = base + (" ; " if rmc_parameters_after_semicolon else " ") + parameters
        self.add_section_line("bonds", line, auto_write=auto_write)

    def add_angle(
        self,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        equilibrium_degree: float,
        force_constant: float,
        sigma: Optional[float] = None,
        *,
        function_type: int = 1,
        rmc_parameters_after_semicolon: bool = False,
        auto_write: Optional[bool] = None,
    ) -> None:
        base = self._join([atom_i, atom_j, atom_k, function_type])
        parameters = self._join([equilibrium_degree, force_constant])
        if sigma is not None:
            parameters += " " + self._number(sigma)
        line = base + (" ; " if rmc_parameters_after_semicolon else " ") + parameters
        self.add_section_line("angles", line, auto_write=auto_write)

    def add_periodic_dihedral(
        self,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        atom_l: int,
        equilibrium_degree: float,
        force_constant: float,
        multiplicity: int,
        sigma: Optional[float] = None,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        values: List[Number] = [
            atom_i, atom_j, atom_k, atom_l, 1,
            equilibrium_degree, force_constant, multiplicity,
        ]
        if sigma is not None:
            values.append(sigma)
        self.add_section_line("dihedrals", self._join(values), auto_write=auto_write)

    def add_harmonic_dihedral(
        self,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        atom_l: int,
        equilibrium_degree: float,
        force_constant: float,
        sigma: Optional[float] = None,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        values: List[Number] = [
            atom_i, atom_j, atom_k, atom_l, 2,
            equilibrium_degree, force_constant,
        ]
        if sigma is not None:
            values.append(sigma)
        self.add_section_line("dihedrals", self._join(values), auto_write=auto_write)

    def add_rb_dihedral(
        self,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        atom_l: int,
        coefficients: Sequence[float],
        sigma: Optional[float] = None,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        if len(coefficients) != 6:
            raise ValueError("RB dihedral は C0～C5 の6係数が必要です。")
        values: List[Number] = [atom_i, atom_j, atom_k, atom_l, 3]
        values.extend(coefficients)
        if sigma is not None:
            values.append(sigma)
        self.add_section_line("dihedrals", self._join(values), auto_write=auto_write)

    def add_exclusion(
        self,
        centre_atom: int,
        excluded_atoms: Sequence[int],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        if not excluded_atoms:
            raise ValueError("excluded_atoms は1個以上必要です。")
        self.add_section_line(
            "exclusions",
            self._join([int(centre_atom)] + [int(value) for value in excluded_atoms]),
            auto_write=auto_write,
        )

    def add_virtual_site2(
        self,
        site: int,
        atom_i: int,
        atom_j: int,
        a: float,
        *,
        host_atom: Optional[int] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        values: List[Number] = [site, atom_i, atom_j, 1, a]
        line = self._join(values)
        if host_atom is not None:
            line += " ; %d" % int(host_atom)
        self.add_section_line("virtual_sites2", line, auto_write=auto_write)

    def add_virtual_site3(
        self,
        site: int,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        function_type: int,
        parameters: Sequence[float],
        *,
        host_atom: Optional[int] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        expected = {1: 2, 2: 2, 3: 2, 4: 3}
        type_id = int(function_type)
        if type_id not in expected or len(parameters) != expected[type_id]:
            raise ValueError("virtual_sites3 のfunction typeまたはparameter数が不正です。")
        values: List[Number] = [site, atom_i, atom_j, atom_k, type_id]
        values.extend(parameters)
        line = self._join(values)
        if host_atom is not None:
            line += " ; %d" % int(host_atom)
        self.add_section_line("virtual_sites3", line, auto_write=auto_write)

    def add_virtual_site4(
        self,
        site: int,
        atom_i: int,
        atom_j: int,
        atom_k: int,
        atom_l: int,
        a: float,
        b: float,
        c_nm: float,
        *,
        host_atom: Optional[int] = None,
        auto_write: Optional[bool] = None,
    ) -> None:
        line = self._join([site, atom_i, atom_j, atom_k, atom_l, 2, a, b, c_nm])
        if host_atom is not None:
            line += " ; %d" % int(host_atom)
        self.add_section_line("virtual_sites4", line, auto_write=auto_write)

    def set_system(self, name: str, *, auto_write: Optional[bool] = None) -> None:
        self.remove_sections("system", auto_write=False)
        section = self.add_section("system", auto_write=False)
        section.lines.append(str(name))
        self._write_if_requested(auto_write)

    def set_molecules(
        self,
        molecules: Sequence[Tuple[str, int]],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        self.remove_sections("molecules", auto_write=False)
        section = self.add_section("molecules", auto_write=False)
        for name, count in molecules:
            if int(count) < 1:
                raise ValueError("molecule count は1以上です。")
            section.lines.append("%s %d" % (str(name), int(count)))
        self._write_if_requested(auto_write)

    def add_molecule_template(
        self,
        molecule_name: str,
        atoms: Sequence[Mapping[str, object]],
        first_instance_indices: Mapping[int, int],
        second_instance_indices: Mapping[int, int],
        *,
        exclusions: int = 3,
        index_offset: Optional[int] = None,
        bonds: Sequence[Mapping[str, object]] = (),
        angles: Sequence[Mapping[str, object]] = (),
        periodic_dihedrals: Sequence[Mapping[str, object]] = (),
        harmonic_dihedrals: Sequence[Mapping[str, object]] = (),
        rb_dihedrals: Sequence[Mapping[str, object]] = (),
        pairs: Sequence[Mapping[str, object]] = (),
        explicit_exclusions: Sequence[Tuple[int, Sequence[int]]] = (),
        auto_write: Optional[bool] = None,
    ) -> None:
        """Add one reusable molecule type with explicit first/second RMC mapping."""
        self.begin_molecule_type(
            molecule_name, exclusions, index_offset=index_offset, auto_write=False
        )
        self.add_section("atoms", auto_write=False)
        for atom in atoms:
            serial = int(atom["serial"])
            if serial not in first_instance_indices or serial not in second_instance_indices:
                raise ValueError("first/second instance mapping が不足しています。")
            self.add_atom(
                serial=serial,
                atom_type=str(atom["atom_type"]),
                residue_number=int(atom.get("residue_number", 1)),
                residue_name=str(atom.get("residue_name", molecule_name)),
                atom_name=str(atom.get("atom_name", "A%d" % serial)),
                charge_group=int(atom.get("charge_group", 1)),
                charge=float(atom.get("charge", 0.0)),
                mass=None if atom.get("mass") is None else float(atom["mass"]),
                first_rmc_index=int(first_instance_indices[serial]),
                second_rmc_index=int(second_instance_indices[serial]),
                auto_write=False,
            )
        for item in pairs:
            self.add_pair(auto_write=False, **item)
        for item in bonds:
            self.add_bond(auto_write=False, **item)
        for item in angles:
            self.add_angle(auto_write=False, **item)
        for item in periodic_dihedrals:
            self.add_periodic_dihedral(auto_write=False, **item)
        for item in harmonic_dihedrals:
            self.add_harmonic_dihedral(auto_write=False, **item)
        for item in rb_dihedrals:
            self.add_rb_dihedral(auto_write=False, **item)
        for centre, excluded in explicit_exclusions:
            self.add_exclusion(centre, excluded, auto_write=False)
        self._write_if_requested(auto_write)

    def add_explicit_network_molecule(
        self,
        molecule_name: str,
        atoms: Sequence[Mapping[str, object]],
        *,
        exclusions: int = 2,
        bonds: Sequence[Mapping[str, object]] = (),
        angles: Sequence[Mapping[str, object]] = (),
        periodic_dihedrals: Sequence[Mapping[str, object]] = (),
        harmonic_dihedrals: Sequence[Mapping[str, object]] = (),
        rb_dihedrals: Sequence[Mapping[str, object]] = (),
        auto_write: Optional[bool] = None,
    ) -> None:
        """Represent an arbitrary whole-cell network as one molecule.

        Each local serial is mapped to one final RMC index.  Because only one
        molecule instance exists, the first and second RMC indices are written
        identically.  This is the explicit-numbering route for irregular Qn
        networks or any topology that cannot be repeated by a molecule template.
        """
        first: Dict[int, int] = {}
        for atom in atoms:
            serial = int(atom["serial"])
            first[serial] = int(atom.get("rmc_index", serial))
        self.add_molecule_template(
            molecule_name,
            atoms,
            first,
            first,
            exclusions=exclusions,
            bonds=bonds,
            angles=angles,
            periodic_dihedrals=periodic_dihedrals,
            harmonic_dihedrals=harmonic_dihedrals,
            rb_dihedrals=rb_dihedrals,
            auto_write=False,
        )
        self.set_system(molecule_name, auto_write=False)
        self.set_molecules([(molecule_name, 1)], auto_write=False)
        self._write_if_requested(auto_write)

    @staticmethod
    def validate_rmc_index_progression(
        first_instance: Mapping[int, int],
        second_instance: Mapping[int, int],
        all_instances: Sequence[Mapping[int, int]],
    ) -> None:
        """Check that later instances follow the first/second index progression."""
        if len(all_instances) < 2:
            raise ValueError("progression検証には2個以上のinstanceが必要です。")
        serials = sorted(first_instance)
        if serials != sorted(second_instance):
            raise ValueError("first/second instanceのlocal serialが一致しません。")
        for instance_number, mapping in enumerate(all_instances, start=1):
            if sorted(mapping) != serials:
                raise ValueError("instanceのlocal serialが一致しません。")
            for serial in serials:
                step = int(second_instance[serial]) - int(first_instance[serial])
                expected = int(first_instance[serial]) + (instance_number - 1) * step
                if int(mapping[serial]) != expected:
                    raise ValueError(
                        "RMC index progressionが成立しません: instance=%d serial=%d expected=%d actual=%d"
                        % (instance_number, serial, expected, int(mapping[serial]))
                    )

    def validate(self) -> None:
        self._validate_preprocessor()
        molecule_types: List[str] = []
        current_serials: Optional[set] = None
        serial_sets: List[set] = []
        molecules: List[Tuple[str, int]] = []
        system_count = 0

        for item in self._items:
            if not isinstance(item, TopologySection):
                continue
            if item.name == "moleculetype":
                lines = self._data_lines(item)
                if len(lines) != 1:
                    raise ValueError("各[moleculetype] sectionには1行必要です。")
                tokens = self._tokens(lines[0], keep_after_semicolon=True)
                if len(tokens) < 2:
                    raise ValueError("[moleculetype] 行が不正です。")
                molecule_types.append(tokens[0])
                current_serials = set()
                serial_sets.append(current_serials)
            elif item.name == "atoms":
                if current_serials is None:
                    raise ValueError("[atoms]の前に[moleculetype]が必要です。")
                for line in self._data_lines(item):
                    before, after = self._split_semicolon(line)
                    tokens = before.split()
                    mapping = after.split()
                    if len(tokens) < 7 or len(mapping) < 2:
                        raise ValueError("[atoms]にはfirst/second RMC indexが必要です。")
                    serial = int(tokens[0])
                    if serial in current_serials:
                        raise ValueError("atom serialが重複しています: %d" % serial)
                    current_serials.add(serial)
                    first = int(mapping[0])
                    second = int(mapping[1])
                    if first < 0 or second < 0:
                        raise ValueError("RMC indexは0以上です。")
            elif item.name in ("pairs", "bonds", "angles", "dihedrals", "exclusions"):
                if current_serials is None:
                    raise ValueError("interaction sectionの前に[moleculetype]が必要です。")
                self._validate_local_indices(item, current_serials)
            elif item.name.startswith("virtual_sites"):
                if current_serials is None:
                    raise ValueError("virtual site sectionの前に[moleculetype]が必要です。")
                self._validate_local_indices(item, current_serials)
            elif item.name == "system":
                system_count += 1
            elif item.name == "molecules":
                for line in self._data_lines(item):
                    tokens = line.split(";", 1)[0].split()
                    if len(tokens) < 2:
                        raise ValueError("[molecules] 行が不正です。")
                    molecules.append((tokens[0], int(tokens[1])))

        if self._path.suffix.lower() == ".top":
            if system_count != 1:
                raise ValueError("TOPには[system]が1つ必要です。")
            if not molecules:
                raise ValueError("TOPには[molecules]が必要です。")
            for name, count in molecules:
                if name not in molecule_types:
                    raise ValueError("未定義のmolecule typeです: %s" % name)
                if count < 1:
                    raise ValueError("molecule countは1以上です。")

    def _validate_local_indices(self, section: TopologySection, serials: set) -> None:
        required = {
            "pairs": 2,
            "bonds": 2,
            "angles": 3,
            "dihedrals": 4,
            "exclusions": 1,
            "virtual_sites2": 3,
            "virtual_sites3": 4,
            "virtual_sites4": 5,
        }[section.name]
        for line in self._data_lines(section):
            before = line.split(";", 1)[0]
            tokens = before.split()
            if len(tokens) < required:
                raise ValueError("[%s] 行が短すぎます。" % section.name)
            for token in tokens[:required]:
                if int(token) not in serials:
                    raise ValueError(
                        "[%s]が未定義atom serialを参照しています: %s"
                        % (section.name, token)
                    )

    def _validate_preprocessor(self) -> None:
        stack: List[str] = []
        for item in self._items:
            if not isinstance(item, str):
                continue
            line = item.strip()
            if line.startswith("#ifdef ") or line.startswith("#ifndef "):
                stack.append(line)
            elif line == "#else":
                if not stack:
                    raise ValueError("対応する#ifのない#elseです。")
            elif line == "#endif":
                if not stack:
                    raise ValueError("対応する#ifのない#endifです。")
                stack.pop()
        if stack:
            raise ValueError("閉じられていない#ifdef/#ifndefがあります。")

    @staticmethod
    def _data_lines(section: TopologySection) -> List[str]:
        return [
            line.strip() for line in section.lines
            if line.strip() and not line.lstrip().startswith(";")
        ]

    @staticmethod
    def _split_semicolon(line: str) -> Tuple[str, str]:
        if ";" not in line:
            return line.strip(), ""
        before, after = line.split(";", 1)
        return before.strip(), after.strip()

    @staticmethod
    def _tokens(line: str, *, keep_after_semicolon: bool = False) -> List[str]:
        text = line.replace(";", " ") if keep_after_semicolon else line.split(";", 1)[0]
        return text.split()

    @staticmethod
    def _number(value: Number) -> str:
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return "%.12g" % number

    @classmethod
    def _join(cls, values: Iterable[Union[str, Number]]) -> str:
        result = []
        for value in values:
            result.append(str(value) if isinstance(value, str) else cls._number(value))
        return " ".join(result)

    def _write_if_requested(self, auto_write: Optional[bool]) -> None:
        enabled = self._auto_write if auto_write is None else bool(auto_write)
        if enabled:
            self.write()


class RmcPotDatItp(RmcPotDatTop):
    """Explicit class name for include-topology files."""
