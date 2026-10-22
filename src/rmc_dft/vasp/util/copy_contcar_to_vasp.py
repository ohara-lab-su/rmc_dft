#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""

from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

import shutil
from pathlib import Path
from x_logger import XLogger


def copy_contcar_to_vasp(
    vasp_name: str,
    logger: Optional[XLogger] = XLogger(),
) -> bool:
    """
    CONTCAR ファイルを {name}.vasp にコピーする

    Args:
        vasp_name (str): 出力ファイル名（拡張子なし）
        logger (XLogger):

    Returns:
        bool:

    """
    src = Path("CONTCAR")
    dst = Path(f"{vasp_name}.vasp")

    if not src.exists():
        logger.error("Error: CONTCAR ファイルが見つかりません。")
        return False

    shutil.copyfile(src, dst)
    logger.info(f"{src} --> {dst} にコピーしました")
    return True
