#!/usr/bin/env python3
"""RMC_POT *.dat の固定形式 / 自由形式 自動切替ラッパークラス。"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_dat_free import RmcPotDatFree
from rmc_dft.rmc_pot.rmc_pot_dat_fixed import RmcPotDatFixed
from x_logger import XLogger


class RmcPotDat:
    """固定形式と自由形式の RmcPotDat を統一して扱う透明なラッパークラス。"""

    def __init__(
        self,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
        *,
        cfg_name: Optional[str] = None,
        auto_write: bool = True,
        use_free_format: Optional[bool] = None,
    ) -> None:
        """RmcPotDat インスタンスを初期化し、内部の実装クラスへ処理を委譲する。

        Args:
            config: Config インスタンス。
            logger: XLogger インスタンス。
            cfg_name: *.dat の拡張子を除いたファイル名。
            auto_write: 自動保存フラグ。
            use_free_format: 明示的に自由形式(True)/固定形式(False)を指定。
                None の場合は既存ファイルの先頭行(#002/#003)から自動判定する。
        """
        self._logger = logger or XLogger()
        self._config = config or Config()
        self._cfg_name = cfg_name or self._config.cfg_name
        self._auto_write = auto_write

        target_path = Path(f"{self._cfg_name}.dat")

        # 1. 形式の自動判定（True/False）
        is_free = use_free_format
        if is_free is None:
            if target_path.exists():
                is_free = self._detect_if_free_format(target_path)
            else:
                is_free = True  # 新規作成時のデフォルト

        # 2. 内部クラスの生成（version は RmcPotDatFree 側のデフォルト値に任せる）
        if is_free:
            self._impl = RmcPotDatFree(
                config=self._config,
                logger=self._logger,
                cfg_name=self._cfg_name,
                auto_write=self._auto_write,
            )
        else:
            self._impl = RmcPotDatFixed(
                config=self._config,
                logger=self._logger,
                cfg_name=self._cfg_name,
                auto_write=self._auto_write,
            )

    @staticmethod
    def _detect_if_free_format(path: Path) -> bool:
        """ファイル先頭行を見て自由形式(#002/#003)かどうか判定する。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                return first_line in {"#002", "#003"}
        except Exception:
            return False

    @property
    def is_free_format(self) -> bool:
        """現在使用中の実体が自由形式かどうかを返す。"""
        return isinstance(self._impl, RmcPotDatFree)

    def __getattr__(self, name: str) -> Any:
        """未定義の属性・メソッド呼び出しを全て内部実装へ転送する。"""
        return getattr(self._impl, name)
