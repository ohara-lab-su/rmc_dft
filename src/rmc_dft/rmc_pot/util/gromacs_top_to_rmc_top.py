#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

GROMACS topology を RMC_POT topology へ変換する補助モジュール。

目的
----
既存の GROMACS 用 ``*.top`` と GROMACS 構造 ``*.gro`` から、RMC_POT が読むための
追加 index 情報を付加した topology を生成する。

このモジュールは、GROMACS の force field を物理的に変換するものではない。
主に以下を行う。

* ``[ moleculetype ]`` のデータ行へ RMC 用 ``RMCindex_offset`` を付加する。
* ``[ atoms ]`` のデータ行へ RMC 用 index をコメントとして付加する。
* ``[ molecules ]`` と ``*.gro`` の原子数を照合する。
* 必要に応じて force-field ``#include`` 行を RMC_POT が読める名前へ置換する。

制限
----
GROMACS の preprocessor を完全には実装しない。``#include`` は、必要に応じて
ローカル ``*.itp`` を展開する簡易処理だけを提供する。
``#ifdef`` などの条件分岐の評価は行わず、入力の行を保持する。

RMC index の前提
----------------
RMC index は、RMC_POT に渡す ``*.cfg`` またはそれと同じ順序の構造ファイルにおける
1 始まりの原子番号である。本モジュールでは ``*.gro`` の原子順をそのまま RMC index
として扱う。
"""

import argparse
import os
import re
import sys
from collections import OrderedDict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple


class TopologyConvertError(Exception):
    """GROMACS topology から RMC_POT topology への変換に失敗した場合の例外。"""


class GroAtom(object):
    """GROMACS gro ファイルの 1 原子分の情報。"""

    def __init__(self, index: int, residue_name: str, atom_name: str) -> None:
        self.index = index
        self.residue_name = residue_name
        self.atom_name = atom_name


class MoleculeType(object):
    """topology 中の molecule type 定義。"""

    def __init__(self, name: str, nrexcl: str) -> None:
        self.name = name
        self.nrexcl = nrexcl
        self.atom_count = 0


class TopologyInfo(object):
    """topology の変換に必要な最小情報。"""

    def __init__(self) -> None:
        self.molecule_types = OrderedDict()  # type: OrderedDict[str, MoleculeType]
        self.molecules = []  # type: List[Tuple[str, int]]


_SECTION_RE = re.compile(r"^\s*\[\s*([^\]]+)\s*\]")
_INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]')


def _strip_comment(line: str) -> str:
    """semicolon 以降をコメントとして除いた文字列を返す。"""
    parts = line.split(";", 1)
    return parts[0].strip()


def _is_data_line(line: str) -> bool:
    """topology の directive 内で実データ行として扱うべき行かどうかを返す。"""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(";"):
        return False
    if stripped.startswith("#"):
        return False
    if stripped.startswith("["):
        return False
    return True


def _section_name(line: str) -> Optional[str]:
    """section header 行なら section 名を小文字で返す。"""
    match = _SECTION_RE.match(line)
    if match is None:
        return None
    return match.group(1).strip().lower()


def read_text_lines(path: str) -> List[str]:
    """テキストファイルを行末付きで読む。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_text_lines(path: str, lines: Sequence[str]) -> None:
    """テキストファイルを書き出す。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            if line.endswith("\n"):
                f.write(line)
            else:
                f.write(line + "\n")


def read_gro(path: str) -> List[GroAtom]:
    """GROMACS gro ファイルを読み、原子順を返す。

    gro の原子番号欄は 99999 で wrap することがあるため、ここではファイル内の出現順を
    1 始まり index として扱う。
    """
    lines = read_text_lines(path)
    if len(lines) < 3:
        raise TopologyConvertError("gro ファイルとして行数が不足しています: " + path)

    try:
        atom_count = int(lines[1].strip())
    except ValueError:
        raise TopologyConvertError(
            "gro ファイルの 2 行目から原子数を読めません: " + path
        )

    if len(lines) < atom_count + 3:
        raise TopologyConvertError("gro ファイルの原子行数が不足しています: " + path)

    atoms = []
    for i in range(atom_count):
        line = lines[i + 2].rstrip("\n")
        residue_name = ""
        atom_name = ""
        if len(line) >= 20:
            residue_name = line[5:10].strip()
            atom_name = line[10:15].strip()
        if not atom_name:
            tokens = line.split()
            if len(tokens) >= 2:
                residue_name = tokens[0]
                atom_name = tokens[1]
        atoms.append(GroAtom(i + 1, residue_name, atom_name))

    return atoms


def _should_expand_include(include_name: str, expand_local_itp: bool) -> bool:
    """ローカル include を展開するかどうかを判定する。"""
    if not expand_local_itp:
        return False
    base = os.path.basename(include_name)
    lower = base.lower()
    if not lower.endswith(".itp"):
        return False
    if lower.startswith("ff"):
        return False
    return True


def expand_local_includes(
    top_path: str,
    lines: Sequence[str],
    include_dirs: Optional[Sequence[str]] = None,
    expand_local_itp: bool = False,
    _seen: Optional[set] = None,
) -> List[str]:
    """ローカル分子定義用 itp を必要に応じて展開する。

    force-field include らしい ``ff*.itp`` は展開せず、そのまま残す。
    """
    if _seen is None:
        _seen = set()

    result = []  # type: List[str]
    base_dir = os.path.dirname(os.path.abspath(top_path))
    search_dirs = [base_dir]
    if include_dirs is not None:
        for include_dir in include_dirs:
            search_dirs.append(os.path.abspath(include_dir))

    for line in lines:
        match = _INCLUDE_RE.match(line)
        if match is None:
            result.append(line)
            continue

        include_name = match.group(1)
        if not _should_expand_include(include_name, expand_local_itp):
            result.append(line)
            continue

        include_path = None
        for search_dir in search_dirs:
            candidate = os.path.join(search_dir, include_name)
            if os.path.exists(candidate):
                include_path = candidate
                break

        if include_path is None:
            result.append(line)
            continue

        real_path = os.path.realpath(include_path)
        if real_path in _seen:
            raise TopologyConvertError("include が循環しています: " + include_path)
        _seen.add(real_path)

        result.append("; BEGIN expanded include: " + include_name + "\n")
        included_lines = read_text_lines(include_path)
        expanded = expand_local_includes(
            include_path,
            included_lines,
            include_dirs=include_dirs,
            expand_local_itp=expand_local_itp,
            _seen=_seen,
        )
        result.extend(expanded)
        result.append("; END expanded include: " + include_name + "\n")

    return result


def parse_topology_info(lines: Sequence[str]) -> TopologyInfo:
    """topology から molecule type と molecules 数を読む。"""
    info = TopologyInfo()
    section = None  # type: Optional[str]
    current_molecule_type = None  # type: Optional[MoleculeType]

    for line in lines:
        found_section = _section_name(line)
        if found_section is not None:
            section = found_section
            if section != "atoms":
                current_molecule_type = current_molecule_type
            continue

        if not _is_data_line(line):
            continue

        data = _strip_comment(line)
        tokens = data.split()
        if not tokens:
            continue

        if section == "moleculetype":
            if len(tokens) < 2:
                raise TopologyConvertError(
                    "[ moleculetype ] のデータ行が不完全です: " + line.strip()
                )
            name = tokens[0]
            nrexcl = tokens[1]
            current_molecule_type = MoleculeType(name, nrexcl)
            info.molecule_types[name] = current_molecule_type
            continue

        if section == "atoms":
            if current_molecule_type is not None:
                current_molecule_type.atom_count += 1
            continue

        if section == "molecules":
            if len(tokens) < 2:
                raise TopologyConvertError(
                    "[ molecules ] のデータ行が不完全です: " + line.strip()
                )
            name = tokens[0]
            try:
                count = int(tokens[1])
            except ValueError:
                raise TopologyConvertError(
                    "[ molecules ] の分子数が整数ではありません: " + line.strip()
                )
            info.molecules.append((name, count))
            continue

    if not info.molecule_types:
        raise TopologyConvertError("[ moleculetype ] が見つかりません。")
    if not info.molecules:
        raise TopologyConvertError("[ molecules ] が見つかりません。")

    for name, count in info.molecules:
        if name not in info.molecule_types:
            raise TopologyConvertError(
                "[ molecules ] にある molecule type が未定義です: " + name
            )
        if info.molecule_types[name].atom_count <= 0:
            raise TopologyConvertError(
                "molecule type に [ atoms ] がありません: " + name
            )

    return info


def build_rmc_index_map(
    info: TopologyInfo,
) -> Tuple[Dict[str, int], Dict[Tuple[str, int], List[int]], int]:
    """molecule type ごとの offset と local atom ごとの RMC index を作る。

    戻り値:
        offsets: molecule type -> その type の最初の RMC index の直前までの原子数。
        index_map: (molecule type, local atom index) -> occurrence ごとの RMC index list。
        total_atoms: topology から期待される総原子数。
    """
    offsets = OrderedDict()  # type: OrderedDict[str, int]
    index_map = {}  # type: Dict[Tuple[str, int], List[int]]
    current_index = 1

    for name, mol_count in info.molecules:
        mol_type = info.molecule_types[name]
        if name not in offsets:
            offsets[name] = current_index - 1

        for occurrence in range(mol_count):
            for local_index in range(1, mol_type.atom_count + 1):
                key = (name, local_index)
                if key not in index_map:
                    index_map[key] = []
                index_map[key].append(current_index)
                current_index += 1

    return offsets, index_map, current_index - 1


def _format_moleculetype_line(
    tokens: Sequence[str], offset: int, original_line: str
) -> str:
    """[ moleculetype ] のデータ行へ RMCindex_offset を付加する。"""
    if len(tokens) >= 3:
        return original_line
    return "{0:<20s} {1:<8s} {2:d}\n".format(tokens[0], tokens[1], offset)


def _format_atoms_line(
    tokens: Sequence[str],
    original_line: str,
    molecule_type_name: str,
    index_map: Dict[Tuple[str, int], List[int]],
) -> str:
    """[ atoms ] のデータ行へ RMC index コメントを付加する。"""
    if len(tokens) < 1:
        return original_line

    try:
        local_index = int(tokens[0])
    except ValueError:
        return original_line

    key = (molecule_type_name, local_index)
    if key not in index_map:
        return original_line

    rmc_indices = index_map[key]
    if len(rmc_indices) >= 2:
        rmc_text = "{0:d} {1:d}".format(rmc_indices[0], rmc_indices[1])
    else:
        rmc_text = "{0:d}".format(rmc_indices[0])

    data = _strip_comment(original_line)
    return "{0:<72s} ; {1}\n".format(data, rmc_text)


def replace_force_field_include(
    lines: Sequence[str], force_field_include: Optional[str]
) -> List[str]:
    """force-field include を必要に応じて置換する。

    ``force_field_include`` が None なら何もしない。
    既存の ``#include \"ff*.itp\"`` があれば最初の 1 個を置換する。
    無ければ ``[ defaults ]`` ブロックの直後に挿入する。
    """
    if force_field_include is None:
        return list(lines)

    include_line = '#include "' + force_field_include + '"\n'
    result = []  # type: List[str]
    replaced = False

    for line in lines:
        match = _INCLUDE_RE.match(line)
        if match is not None:
            base = os.path.basename(match.group(1)).lower()
            if base.startswith("ff") and not replaced:
                result.append(include_line)
                replaced = True
                continue
        result.append(line)

    if replaced:
        return result

    inserted = []  # type: List[str]
    section = None  # type: Optional[str]
    defaults_seen = False
    inserted_include = False
    for line in result:
        found_section = _section_name(line)
        if found_section is not None:
            if defaults_seen and not inserted_include and found_section != "defaults":
                inserted.append("\n")
                inserted.append(include_line)
                inserted.append("\n")
                inserted_include = True
            section = found_section
            if section == "defaults":
                defaults_seen = True
        inserted.append(line)

    if not inserted_include:
        inserted.insert(0, include_line)

    return inserted


def convert_topology_lines(
    top_lines: Sequence[str],
    gro_atoms: Sequence[GroAtom],
    force_field_include: Optional[str] = None,
) -> Tuple[List[str], TopologyInfo]:
    """GROMACS topology 行列を RMC_POT 用 topology 行列へ変換する。"""
    working_lines = replace_force_field_include(top_lines, force_field_include)
    info = parse_topology_info(working_lines)
    offsets, index_map, expected_atoms = build_rmc_index_map(info)

    if len(gro_atoms) != expected_atoms:
        raise TopologyConvertError(
            "topology と gro の原子数が一致しません: topology={0:d}, gro={1:d}".format(
                expected_atoms,
                len(gro_atoms),
            )
        )

    result = []  # type: List[str]
    section = None  # type: Optional[str]
    current_molecule_type = None  # type: Optional[str]

    for line in working_lines:
        found_section = _section_name(line)
        if found_section is not None:
            section = found_section
            result.append(line)
            continue

        if not _is_data_line(line):
            result.append(line)
            continue

        data = _strip_comment(line)
        tokens = data.split()
        if not tokens:
            result.append(line)
            continue

        if section == "moleculetype":
            name = tokens[0]
            current_molecule_type = name
            offset = 0
            if name in offsets:
                offset = offsets[name]
            result.append(_format_moleculetype_line(tokens, offset, line))
            continue

        if section == "atoms" and current_molecule_type is not None:
            result.append(
                _format_atoms_line(tokens, line, current_molecule_type, index_map)
            )
            continue

        result.append(line)

    return result, info


def convert_gromacs_top_to_rmc_top(
    top_path: str,
    gro_path: str,
    output_path: str,
    force_field_include: Optional[str] = None,
    include_dirs: Optional[Sequence[str]] = None,
    expand_local_itp: bool = False,
) -> TopologyInfo:
    """GROMACS ``*.top`` と ``*.gro`` から RMC_POT 用 ``*.top`` を生成する。"""
    top_lines = read_text_lines(top_path)
    top_lines = expand_local_includes(
        top_path,
        top_lines,
        include_dirs=include_dirs,
        expand_local_itp=expand_local_itp,
    )
    gro_atoms = read_gro(gro_path)
    converted_lines, info = convert_topology_lines(
        top_lines,
        gro_atoms,
        force_field_include=force_field_include,
    )
    write_text_lines(output_path, converted_lines)
    return info


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI 用 argument parser を作る。"""
    parser = argparse.ArgumentParser(
        description="Convert a GROMACS topology and gro structure to an RMC_POT topology."
    )
    parser.add_argument("--top", required=True, help="Input GROMACS .top file.")
    parser.add_argument(
        "--gro", required=True, help="Input GROMACS .gro file with the RMC atom order."
    )
    parser.add_argument("--out", required=True, help="Output RMC_POT .top file.")
    parser.add_argument(
        "--force-field-include",
        default=None,
        help="Replace or insert a force-field include, e.g. ffoplsaa.itp. Omit to keep the input.",
    )
    parser.add_argument(
        "--include-dir",
        action="append",
        default=None,
        help="Additional directory for local .itp include expansion. Can be specified multiple times.",
    )
    parser.add_argument(
        "--expand-local-itp",
        action="store_true",
        help="Expand local non-ff*.itp includes into the output topology.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        info = convert_gromacs_top_to_rmc_top(
            top_path=args.top,
            gro_path=args.gro,
            output_path=args.out,
            force_field_include=args.force_field_include,
            include_dirs=args.include_dir,
            expand_local_itp=args.expand_local_itp,
        )
    except TopologyConvertError as exc:
        sys.stderr.write("ERROR: " + str(exc) + "\n")
        return 1

    sys.stdout.write("Wrote RMC_POT topology: " + args.out + "\n")
    sys.stdout.write("Molecule types:\n")
    for name, mol_type in info.molecule_types.items():
        sys.stdout.write(
            "  {0}: atoms_per_molecule={1:d}\n".format(name, mol_type.atom_count)
        )
    sys.stdout.write("Molecules:\n")
    for name, count in info.molecules:
        sys.stdout.write("  {0}: count={1:d}\n".format(name, count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
