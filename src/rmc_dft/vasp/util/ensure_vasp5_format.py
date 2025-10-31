#!/usr/bin/env python

from x_logger import XLogger


def ensure_vasp5_format(
    poscar_name: str,
    element_info: str | None = None,
    logger: XLogger = None,
) -> bool:
    """
    VASPファイルの6行目にラベルを設定する
    VASP4 type POSCAR to VASP5 type POSCAR
    繰り返し実行しても副作用はない

    RMC pot の cfg 形式は元素名がないために、POSCAR 形式に変換したときに困る場合があるので
    VASP5 形式にする (cfg2poscar は element 情報がない VASP4 形式)

    Args:
        poscar_name (str): POSCARファイル名
        element_info (str): element 情報があるファイル名
        logger (XLogger):

    Returns:
        bool: True/False
    """
    if not logger:
        logger = XLogger()

    if element_info is None:
        element_info = "label.txt"

    logger.info(f"element_info: {element_info}")

    # element 情報があるファイルを開く
    try:
        with open(element_info, "r") as file:
            label_line = file.readline().strip()
    except FileNotFoundError:
        logger.error(f"element info file not found.")
        return False

    with open(poscar_name, "r") as file:
        lines = file.readlines()
        label_place = 6
    if 1 <= label_place <= len(lines):
        lines[label_place - 1] = label_line + "\n"  # 改行を付けて置換

        # ファイルに上書き保存
        with open(poscar_name, "w") as file:
            file.writelines(lines)
        logger.info(f"{poscar_name} label back.")
    else:
        logger.error("error: line number out of range.")
        return False

    return True
