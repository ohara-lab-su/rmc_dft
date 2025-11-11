#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from pathlib import Path

from x_logger import XLogger


def copy_vasp_to_poscar(
    vasp_name: str,
    logger: Optional[XLogger] = XLogger(),
) -> bool:
    """
    {vasp_name}.vasp ファイルを POSCAR にコピーする

    Args:
        vasp_name (str): 入力ファイル名（拡張子なし）
        logger (XLogger): ロガー（未指定の場合は新規生成）

    Returns:
        bool: 成功時 True、失敗時 False
    """
    src = Path(f"{vasp_name}.vasp")
    dst = Path("POSCAR")

    if not src.exists():
        logger.error(f"Error: {src} が見つかりません。")
        return False

    try:
        shutil.copyfile(src, dst)
        logger.info(f"{src} --> {dst} にコピーしました")
        return True
    except Exception as e:
        logger.error(f"Error: コピーに失敗しました ({e})")
        return False
