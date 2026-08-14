#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RMC_POT ``*.snc`` 出力ファイル解析クラス。
"""

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


class RmcPotSnc:
    """RMC_POT の Second Neighbour Constraint 出力を読み取る。"""

    def __init__(self, path: str) -> None:
        """``*.snc`` を読み込む。

        Args:
            path: 解析する ``*.snc`` ファイル。
        """
        self.path = Path(path)
        self.constraints: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """ファイルを読み直し、制約情報と中心原子ごとの配位数を保持する。

        Raises:
            FileNotFoundError: 指定ファイルが存在しない場合。
            ValueError: ``*.snc`` の必須部分を解釈できない場合。
        """
        if not self.path.is_file():
            raise FileNotFoundError(f"{self.path} が見つかりません。")

        lines = self.path.read_text(encoding="utf-8").splitlines()
        number_of_constraints = self._read_number_of_constraints(lines)
        property_rows = self._read_constraint_properties(lines, number_of_constraints)
        coordination_blocks = self._read_coordination_blocks(lines)

        if len(coordination_blocks) != number_of_constraints:
            raise ValueError(
                "*.snc の制約数と配位数ブロック数が一致しません: "
                f"constraints={number_of_constraints}, "
                f"blocks={len(coordination_blocks)}"
            )

        self.constraints = []
        for index in range(number_of_constraints):
            constraint = property_rows[index]
            block = coordination_blocks[index]
            constraint["coordination_numbers"] = block["coordination_numbers"]
            constraint["reported_satisfying_count"] = block["reported_satisfying_count"]

            calculated_satisfying_count = 0
            target_qn = constraint["coordination_number"]
            for value in constraint["coordination_numbers"].values():
                if value == target_qn:
                    calculated_satisfying_count += 1

            constraint["calculated_satisfying_count"] = calculated_satisfying_count
            constraint["satisfying_count_matches"] = (
                calculated_satisfying_count
                == constraint["reported_satisfying_count"]
            )
            self.constraints.append(constraint)

    def get_qn_counts(self, constraint_index: int = 0) -> Dict[int, int]:
        """指定制約ブロックに記録された中心原子の Qn 分布を返す。

        Args:
            constraint_index: 0 始まりの制約番号。

        Returns:
            Qn をキー、中心原子数を値とする辞書。
        """
        constraint = self.constraints[constraint_index]
        counter = Counter(constraint["coordination_numbers"].values())
        return {int(qn): int(counter[qn]) for qn in sorted(counter)}

    def get_common_qn_counts(self) -> Dict[int, int]:
        """全制約に同じ配位数列が保存されていることを確認して分布を返す。

        Returns:
            Qn をキー、中心原子数を値とする辞書。

        Raises:
            ValueError: 制約ごとの中心原子配位数が一致しない場合。
        """
        if not self.constraints:
            return {}

        reference = self.constraints[0]["coordination_numbers"]
        for index, constraint in enumerate(self.constraints[1:], start=1):
            if constraint["coordination_numbers"] != reference:
                raise ValueError(
                    "*.snc の制約ごとに中心原子の配位数が一致しません: "
                    f"constraint_index={index}"
                )
        return self.get_qn_counts(0)

    @staticmethod
    def _read_number_of_constraints(lines: List[str]) -> int:
        for line in lines:
            match = re.match(r"^\s*(\d+)\s+number of constraints", line)
            if match is not None:
                return int(match.group(1))
        raise ValueError("*.snc から number of constraints を取得できません。")

    @staticmethod
    def _read_constraint_properties(
        lines: List[str],
        number_of_constraints: int,
    ) -> List[Dict[str, Any]]:
        start_index: Optional[int] = None
        for index, line in enumerate(lines):
            if "number of cenral atoms satisfying the constraint" in line:
                start_index = index + 1
                break

        if start_index is None:
            raise ValueError("*.snc の constraint properties を取得できません。")

        rows: List[Dict[str, Any]] = []
        for line in lines[start_index:]:
            tokens = line.split()
            if not tokens:
                continue
            if not tokens[0].isdigit():
                if rows:
                    break
                continue

            second_type_count = int(tokens[5])
            expected_length = 12 + second_type_count
            if len(tokens) != expected_length:
                raise ValueError(
                    "*.snc の constraint properties の列数が不正です: "
                    f"line={line}"
                )

            second_type_start = 6
            second_type_end = second_type_start + second_type_count
            second_types = [
                int(value) for value in tokens[second_type_start:second_type_end]
            ]
            second_minimum = float(tokens[second_type_end])
            second_maximum = float(tokens[second_type_end + 1])

            rows.append(
                {
                    "index": int(tokens[0]),
                    "central_type": int(tokens[1]),
                    "first_neighbor_type": int(tokens[2]),
                    "first_neighbor_minimum": float(tokens[3]),
                    "first_neighbor_maximum": float(tokens[4]),
                    "second_neighbor_types": second_types,
                    "second_neighbor_minimum": second_minimum,
                    "second_neighbor_maximum": second_maximum,
                    "coordination_number": int(tokens[second_type_end + 2]),
                    "fraction": float(tokens[second_type_end + 3]),
                    "sigma": float(tokens[second_type_end + 4]),
                    "central_atom_count": int(tokens[second_type_end + 5]),
                }
            )
            if len(rows) == number_of_constraints:
                break

        if len(rows) != number_of_constraints:
            raise ValueError(
                "*.snc の constraint properties 行数が不足しています: "
                f"expected={number_of_constraints}, actual={len(rows)}"
            )
        return rows

    @staticmethod
    def _read_coordination_blocks(lines: List[str]) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for line in lines:
            constraint_match = re.match(r"^\s*(\d+)-th constraint\s*$", line)
            if constraint_match is not None:
                if current is not None:
                    blocks.append(current)
                current = {
                    "index": int(constraint_match.group(1)),
                    "reported_satisfying_count": None,
                    "coordination_numbers": {},
                }
                continue

            if current is None:
                continue

            satisfy_match = re.match(
                r"^\s*nsatisfy/constraint\s+(\d+)\s*$",
                line,
            )
            if satisfy_match is not None:
                current["reported_satisfying_count"] = int(satisfy_match.group(1))
                continue

            atom_match = re.match(r"^\s*(\d+)\s+(\d+)\s*$", line)
            if atom_match is not None:
                atom_index = int(atom_match.group(1))
                coordination_number = int(atom_match.group(2))
                current["coordination_numbers"][atom_index] = coordination_number

        if current is not None:
            blocks.append(current)

        for block in blocks:
            if block["reported_satisfying_count"] is None:
                raise ValueError(
                    "*.snc の nsatisfy/constraint を取得できません: "
                    f"constraint={block['index']}"
                )
        return blocks
