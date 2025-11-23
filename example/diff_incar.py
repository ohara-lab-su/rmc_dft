#!/usr/bin/env python
import sys
from rmc_dft import VaspIncar


def main() -> None:
    """
    2つの INCAR ファイルを引数として受け取り、
    diff_with による差分を表示する。
    """
    if len(sys.argv) != 3:
        print("Usage: incar_diff.py <INCAR_A> <INCAR_B>")
        sys.exit(1)

    path_a = sys.argv[1]
    path_b = sys.argv[2]

    incar_a = VaspIncar(path_a, auto_write=False)
    incar_b = VaspIncar(path_b, auto_write=False)

    diff = incar_a.diff_with(incar_b)

    print(f"     {path_a} --> {path_b}")
    for tag, (v1, v2) in diff.items():
        print(f"{tag}: {v1}  ->  {v2}")


if __name__ == "__main__":
    main()

# # 例: 2つの INCAR を読み込む
# incar_a = VaspIncar("INCAR")
# incar_b = VaspIncar("mistake/incarGGAU_1")
#
# # 差分を取得
# diff = incar_a.diff_with(incar_b)
#
# # 結果を表示
# for tag, (v1, v2) in diff.items():
#     print(f"{tag}: {v1}  ->  {v2}")
