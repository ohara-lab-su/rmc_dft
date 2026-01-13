#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import sys
from rmc_dft import VaspIncar


def main() -> None:
    """
    2つの INCAR ファイルを比較し、値が異なるタグだけを
    整形して表示するスクリプト。
    """
    if len(sys.argv) != 3:
        print("Usage: diff_incar.py <INCAR_A> <INCAR_B>")
        sys.exit(1)

    path_a = sys.argv[1]
    path_b = sys.argv[2]

    # INCAR 読み込み
    incar_a = VaspIncar(path_a, auto_write=False)
    incar_b = VaspIncar(path_b, auto_write=False)

    dict_a = incar_a.export_dict()
    dict_b = incar_b.export_dict()

    # 差分のタグを追加するリスト
    diff_list = []

    keys = set(dict_a.keys()) | set(dict_b.keys())
    for tag in sorted(keys):
        v1 = dict_a.get(tag, None)
        v2 = dict_b.get(tag, None)

        # v1 → 文字列化
        if v1 is None:
            s1 = "None"
        else:
            s1 = str(v1)

        # v2 → 文字列化
        if v2 is None:
            s2 = "None"
        else:
            s2 = str(v2)

        # 差分があるときだけ保持
        if s1 != s2:
            diff_list.append((tag, s1, s2))

    print(f"{path_a} --> {path_b}")

    if len(diff_list) == 0:
        print("差分はありません。")
        return

    # カラム幅計算
    max_tag_len = 0
    max_old_len = 0
    max_new_len = 0

    for tag, old, new in diff_list:
        if len(tag) > max_tag_len:
            max_tag_len = len(tag)
        if len(old) > max_old_len:
            max_old_len = len(old)
        if len(new) > max_new_len:
            max_new_len = len(new)

    # 整形出力
    for tag, old, new in diff_list:
        print(
            f"{tag:<{max_tag_len}} : " f"{old:<{max_old_len}}  ->  {new:<{max_new_len}}"
        )


if __name__ == "__main__":
    main()
