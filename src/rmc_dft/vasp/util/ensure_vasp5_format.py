#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from x_logger import XLogger


def ensure_vasp5_format(
    poscar_name: str,
    element_info: Optional[Union[str, Sequence[str]]] = None,
    logger: Optional[XLogger] = XLogger(),
) -> bool:
    """
    VASPファイルの6行目にラベルを設定する
    VASP4 type POSCAR to VASP5 type POSCAR
    繰り返し実行しても副作用はない

    RMC pot の cfg 形式は元素名がないために、POSCAR 形式に変換したときに困る場合があるので
    VASP5 形式にする (cfg2poscar は element 情報がない VASP4 形式)

    Args:
        poscar_name (str): POSCAR
        element_info (str): element 情報があるファイル名 or element のリスト
        logger (XLogger):

    Returns:
        bool: True/False
    """
    if element_info is None:
        element_info = "label.txt"

    logger.info(f"element_info: {element_info}")

    # ラベル行の内容の決定
    if isinstance(element_info, str):
        # ファイル名として扱う
        try:
            with open(element_info, "r", encoding="utf-8") as file:
                label_line: str = file.readline().strip()
        except FileNotFoundError:
            logger.error("element info file not found.")
            return False
    else:
        # Sequence[str] として扱う
        # すべて str であることを軽く確認
        if not all(isinstance(e, str) for e in element_info):
            logger.error("element_info must be a sequence of str.")
            return False
        label_line = " ".join(element_info)

    # VASP の POSCAR 読み込み
    with open(poscar_name, "r") as file:
        lines = file.readlines()
        label_place = 6

    #  VASP の POSCAR 更新(VASP4 -> VASP5)
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
