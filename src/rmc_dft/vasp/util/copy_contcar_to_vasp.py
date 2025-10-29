#!/usr/bin/env python
from x_logger import XLogger


def copy_contcar_to_vasp(
    name: str,
    logger: XLogger = None,
) -> bool:
    """
    CONTCAR ファイルを {name}.vasp にコピーする

    Args:
        name (str): 出力ファイル名（拡張子なし）
        logger (XLogger):

    Returns:
        bool:

    """
    if not logger:
        logger = XLogger()

    src = Path("CONTCAR")
    dst = Path(f"{name}.vasp")

    if not src.exists():
        logger.error("Error: CONTCAR ファイルが見つかりません。")
        return False

    shutil.copyfile(src, dst)
    logger.info(f"{src} --> {dst} にコピーしました")
    return True
