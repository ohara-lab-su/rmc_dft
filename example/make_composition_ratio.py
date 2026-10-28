"""
指定された組成比を整数組成比へ変換し、指定したセル原子数で
組成比を近似した場合の原子数と組成誤差を計算する。

COMPOSITION には各元素の組成比を指定する。
CELL_SIZE には作成するセルの総原子数を指定する。
"""

from fractions import Fraction
from math import sqrt
from typing import Dict, List, Tuple


# 目的とする組成比。
# 元素数および元素名は任意に変更できる。
COMPOSITION: Dict[str, float] = {
    "Li": 0.431,
    "S": 0.392,
    "P": 0.044,
    "C": 0.133,
}

# 作成するセルの総原子数。
CELL_SIZE: int = 500


def gcd_int(a: int, b: int) -> int:
    """2つの整数の最大公約数を返す。"""
    while b != 0:
        remainder: int = a % b
        a = b
        b = remainder

    return abs(a)


def lcm(a: int, b: int) -> int:
    """2つの整数の最小公倍数を返す。"""
    divisor: int = gcd_int(a, b)
    return abs(a * b) // divisor


def get_exact_ratio(composition: Dict[str, float]) -> Dict[str, int]:
    """
    組成比を厳密な最小整数比へ変換する。

    浮動小数点値を文字列化して Fraction に変換し、入力された
    10進小数をそのまま有理数として扱う。

    Parameters
    ----------
    composition : Dict[str, float]
        元素名をキー、組成比を値とする辞書。

    Returns
    -------
    Dict[str, int]
        元素名をキー、最小整数比を値とする辞書。
    """
    fractions: Dict[str, Fraction] = {}

    # 入力された10進小数を正確な有理数へ変換する。
    element: str
    value: float
    for element, value in composition.items():
        fractions[element] = Fraction(str(value))

    # 全元素の分母の最小公倍数を順番に求める。
    denominator: int = 1
    fraction_value: Fraction
    for fraction_value in fractions.values():
        denominator = lcm(denominator, fraction_value.denominator)

    # 共通分母を用いて各組成を整数へ変換する。
    ratio: Dict[str, int] = {}
    for element, fraction_value in fractions.items():
        numerator: int = fraction_value.numerator
        fraction_denominator: int = fraction_value.denominator
        ratio[element] = numerator * denominator // fraction_denominator

    # 全元素に共通する最大公約数を順番に求める。
    divisor: int = 0
    count: int
    for count in ratio.values():
        if divisor == 0:
            divisor = count
        else:
            divisor = gcd_int(divisor, count)

    # 最大公約数で割り、最小整数比にする。
    for element in ratio:
        ratio[element] //= divisor

    return ratio


def get_cell_composition(
    exact_ratio: Dict[str, int],
    cell_size: int,
) -> Dict[str, int]:
    """
    指定したセル原子数に対する各元素の整数原子数を求める。

    厳密な整数組成比から各元素の理想原子数を計算し、整数部分を
    割り当てた後、不足する原子を小数部分が大きい元素から順に
    1原子ずつ割り当てる。

    Parameters
    ----------
    exact_ratio : Dict[str, int]
        各元素の厳密な整数組成比。
    cell_size : int
        セル内の総原子数。

    Returns
    -------
    Dict[str, int]
        指定したセルサイズに対する各元素の整数原子数。
    """
    exact_total: int = 0
    count: int
    for count in exact_ratio.values():
        exact_total += count

    ideal_counts: Dict[str, float] = {}
    atom_counts: Dict[str, int] = {}

    element: str
    for element, count in exact_ratio.items():
        ideal_count: float = count * cell_size / exact_total
        ideal_counts[element] = ideal_count
        atom_counts[element] = int(ideal_count)

    assigned_atoms: int = 0
    for count in atom_counts.values():
        assigned_atoms += count

    remaining: int = cell_size - assigned_atoms

    fractional_parts: Dict[str, float] = {}
    for element in exact_ratio:
        fractional_parts[element] = (
            ideal_counts[element] - atom_counts[element]
        )

    # sorted() の比較キーが float であることを明示する。
    order: List[str] = sorted(
        fractional_parts.keys(),
        key=lambda item: fractional_parts[item],
        reverse=True,
    )

    index: int
    for index in range(remaining):
        element = order[index]
        atom_counts[element] += 1

    return atom_counts


def calculate_error(
    composition: Dict[str, float],
    atom_counts: Dict[str, int],
    cell_size: int,
) -> Tuple[float, float]:
    """
    整数化したセル組成と目的組成との誤差を計算する。

    Parameters
    ----------
    composition : Dict[str, float]
        目的とする各元素の組成比。
    atom_counts : Dict[str, int]
        セル内の各元素の原子数。
    cell_size : int
        セル内の総原子数。

    Returns
    -------
    Tuple[float, float]
        RMS 組成誤差と最大組成誤差。
    """
    squared_error: float = 0.0
    max_error: float = 0.0

    element: str
    target: float
    for element, target in composition.items():
        actual: float = atom_counts[element] / cell_size
        error: float = actual - target

        squared_error += error ** 2

        if abs(error) > max_error:
            max_error = abs(error)

    rms_error: float = sqrt(squared_error / len(composition))

    return rms_error, max_error


def print_result(
    composition: Dict[str, float],
    exact_ratio: Dict[str, int],
    atom_counts: Dict[str, int],
    cell_size: int,
    rms_error: float,
    max_error: float,
) -> None:
    """組成、セル内原子数、および組成誤差を標準出力へ表示する。"""
    print("Target composition")

    element: str
    value: float
    for element, value in composition.items():
        print(f"{element:<2} = {value:.6f}")

    print()

    # 厳密な最小整数組成比を入力された元素順で表示する。
    ratio_parts: List[str] = []
    for element in exact_ratio:
        ratio_parts.append(str(exact_ratio[element]))

    ratio_text: str = " : ".join(ratio_parts)

    print(f"Exact integer ratio = {ratio_text}")
    print()

    print(f"{cell_size}-atom cell")
    print("-" * 40)
    print(f"{'Element':<10}{'Atoms':>10}{'Composition':>20}")
    print("-" * 40)

    total_atoms: int = 0
    for element in composition:
        count: int = atom_counts[element]
        actual: float = count / cell_size
        total_atoms += count

        print(f"{element:<10}{count:>10d}{actual:>20.6f}")

    print("-" * 40)
    print(f"{'Total':<10}{total_atoms:>10d}{1.0:>20.6f}")

    print()
    print(f"RMS composition error = {rms_error:.8f}")
    print(f"Max composition error = {max_error:.8f}")


def main() -> None:
    """組成比の整数化、セル内原子数の決定、誤差評価、結果表示を実行する。"""
    exact_ratio: Dict[str, int] = get_exact_ratio(COMPOSITION)

    atom_counts: Dict[str, int] = get_cell_composition(
        exact_ratio,
        CELL_SIZE,
    )

    rms_error: float
    max_error: float
    rms_error, max_error = calculate_error(
        COMPOSITION,
        atom_counts,
        CELL_SIZE,
    )

    print_result(
        COMPOSITION,
        exact_ratio,
        atom_counts,
        CELL_SIZE,
        rms_error,
        max_error,
    )


if __name__ == "__main__":
    main()
