#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

VaspKpoints
-----------
pymatgen.io.vasp.inputs.Kpoints を薄くラップした KPOINTS 管理クラス。

設計方針
- 既存 KPOINTS があれば読み取って内部状態へ反映（ファイル構造は pymatgen に準拠）。
- 既存 KPOINTS が無ければ既定値（Monkhorst-Pack / 1 1 1 / shift 0 0 0 / "K-Points"）で開始。
- set_* 系で内部状態を更新。auto_write=True のときは更新都度ファイルへ書き出し。
- write() 明示呼び出しで現在の内部状態を KPOINTS ファイルへ保存。
- _build_kpoints() は引数を取らず、内部状態のみを参照して Kpoints を構築。
- pymatgen の現行I/F（gamma_automatic / monkhorst_automatic）を使用。

注意
- モード名は "Gamma" または "Monkhorst-Pack" を想定（先頭大文字）。
- グリッド/シフトは常に長さ3の整数タプルとして厳格に保持。
"""
# from __future__ import annotations

import sys
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from pymatgen.io.vasp.inputs import Kpoints

from x_logger import XLogger


class VaspKpoints:
    """
    KPOINTS ファイルの読み書きと、モード/グリッド/シフト/コメントの管理を行う。

    既定動作
    - 既存 KPOINTS があれば読み取り優先。
    - 無い場合は "Monkhorst-Pack", grid=(1,1,1), shift=(0,0,0), comment="K-Points" で初期化。

    Aargs:
        kpoints_name (str): KPOINTS ファイル名（絶対パス推奨）。
        auto_write (bool): True の場合、set_* 呼び出しで都度ファイルへ保存。
        _logger (XLogger): 任意のロガー（info/debug を想定）。None 可。

    """

    def __init__(
        self,
        kpoints_name: str = "KPOINTS",
        logger: Optional[XLogger] = XLogger(),
        *,
        auto_write: bool = True,
    ) -> None:
        """

        Args:
            kpoints_name (str):
            logger (XLogger):
            auto_write (bool):
        """
        self.kpoints_name: str = kpoints_name
        self.auto_write: bool = auto_write
        self.logger = logger

        # 内部状態（厳格に長さ3のタプルで保持）
        self._mode: str
        self._grid: Tuple[int, int, int]
        self._shift: Tuple[int, int, int]
        self._comment: str

        # pymatgen の Kpoints オブジェクト
        self._kpts_obj: Optional[Kpoints] = None

        if os.path.exists(self.kpoints_name):
            self.load()
        else:
            # 既定値
            self._mode = "Monkhorst-Pack"
            self._grid = (1, 1, 1)
            self._shift = (0, 0, 0)
            self._comment = "K-Points"
            # 既定値から Kpoints を初期生成（引数なしのビルド）
            self._kpts_obj = self._build_kpoints()
            self.write()

    def load(self):
        """
        既存の KPOINTS を読み込む
        """
        # 既存 KPOINTS を読み取り
        self._kpts_obj = Kpoints.from_file(self.kpoints_name)
        # コメント
        self._comment = self._kpts_obj.comment or "K-Points"
        # モード推定（Gamma か Monkhorst-Pack で分岐）
        if getattr(self._kpts_obj, "style", None) == Kpoints.supported_modes.Gamma:
            self._mode = "Gamma"
        else:
            # デフォルトは Monkhorst 扱い
            self._mode = "Monkhorst-Pack"

        # グリッド（長さ3保証）
        if self._kpts_obj.kpts and len(self._kpts_obj.kpts[0]) == 3:
            kx, ky, kz = self._kpts_obj.kpts[0]
            self._grid = (int(kx), int(ky), int(kz))
        else:
            # 安全側
            self._grid = (1, 1, 1)

        # シフト（長さ3保証）
        if self._kpts_obj.kpts_shift and len(self._kpts_obj.kpts_shift) == 3:
            sx, sy, sz = self._kpts_obj.kpts_shift
            self._shift = (int(sx), int(sy), int(sz))
        else:
            self._shift = (0, 0, 0)

        if self.logger:
            self.logger.info(
                f"Loaded KPOINTS from {self.kpoints_name} (mode={self._mode}, grid={self._grid}, shift={self._shift})"
            )

    def write(self) -> None:
        """現在の内部状態を KPOINTS ファイルへ書き出す。"""
        self._kpts_obj = self._build_kpoints()
        if self.logger:
            self.logger.info(
                f"Write KPOINTS: mode={self._mode}, grid={self._grid}, shift={self._shift} -> {self.kpoints_name}"
            )
        self._kpts_obj.write_file(self.kpoints_name)

    def export_dict(self) -> dict:
        """現在の内部状態を辞書で返す（ロギング/デバッグ用）。"""
        return {
            "mode": self._mode,
            "grid": self._grid,
            "shift": self._shift,
            "comment": self._comment,
            "path": self.kpoints_name,
        }

    def update(
        self,
        mode: Optional[str] = None,
        grid: Optional[Tuple[int, int, int]] = None,
        shift: Optional[Tuple[int, int, int]] = None,
        comment: Optional[str] = None,
    ) -> None:
        """
        複数項目をまとめて更新する。指定されたもののみ反映。
        auto_write=True のときは更新後に書き出し。
        """
        changed = False

        if mode is not None:
            self.set_mode(mode)
            changed = True

        if grid is not None:
            if len(grid) != 3:
                raise ValueError("grid must be a tuple of length 3")
            kx, ky, kz = grid
            self.set_grid(int(kx), int(ky), int(kz))
            changed = True

        if shift is not None:
            if len(shift) != 3:
                raise ValueError("shift must be a tuple of length 3")
            sx, sy, sz = shift
            self.set_shift(int(sx), int(sy), int(sz))
            changed = True

        if comment is not None:
            self.set_comment(comment)
            changed = True

        if changed and (not self.auto_write):
            # auto_write=False の場合は、内部状態の再構築のみ行われる
            pass

    def _build_kpoints(self) -> Kpoints:
        """
        内部状態（mode/grid/shift/comment）に基づき Kpoints を構築する。
        現行 pymatgen I/F に合わせ、automatic は使用せず gamma_automatic / monkhorst_automatic を利用。
        """
        comment = self._comment or "K-Points"

        if self._mode == "Gamma":
            kpt = Kpoints.gamma_automatic(kpts=self._grid, comment=comment)
        else:
            # 既定は Monkhorst-Pack
            kpt = Kpoints.monkhorst_automatic(kpts=self._grid, comment=comment)

        # シフトは生成後に適用
        kpt.kpts_shift = list(self._shift)
        return kpt

    # ----------------------------
    #
    # ----------------------------
    def get_mode(self) -> str:
        """現在のモード（"Gamma" or "Monkhorst-Pack"）を返す。"""
        return self._mode

    def set_mode(
        self,
        mode: str,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        モードを設定する。大文字小文字はそのまま保存するが、想定は "Gamma" / "Monkhorst-Pack"。

        Args:
            mode (str):
            auto_write (bool):

        Returns:

        """
        if mode not in ("Gamma", "Monkhorst-Pack"):
            raise ValueError('mode must be "Gamma" or "Monkhorst-Pack"')
        self._mode = mode
        self._kpts_obj = self._build_kpoints()

        if auto_write is None:
            auto_write = self.auto_write

        if auto_write:
            self.write()

    def get_grid(self) -> Tuple[int, int, int]:
        """k-point グリッド (kx, ky, kz) を返す。"""
        return self._grid

    def set_grid(
        self,
        kx: int,
        ky: int,
        kz: int,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        k-point グリッド (kx, ky, kz) を設定する。

        Args:
            kx:
            ky:
            kz:
            auto_write (bool):

        Returns:
        """
        self._grid = (int(kx), int(ky), int(kz))
        self._kpts_obj = self._build_kpoints()

        if auto_write is None:
            auto_write = self.auto_write

        if auto_write:
            self.write()

    def get_shift(self) -> Tuple[int, int, int]:
        """シフト (sx, sy, sz) を返す。"""
        return self._shift

    def set_shift(
        self,
        sx: int,
        sy: int,
        sz: int,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        シフト (sx, sy, sz) を設定する。

        Args:
            sx:
            sy:
            sz:
            auto_write (bool):

        Returns:
        """
        self._shift = (int(sx), int(sy), int(sz))
        self._kpts_obj = self._build_kpoints()

        if auto_write is None:
            auto_write = self.auto_write

        if auto_write:
            self.write()

    def get_comment(self) -> str:
        """先頭コメントを返す。"""
        return self._comment

    def set_comment(
        self,
        s: str,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        先頭コメントを設定する。

        Args:
            s (str):
            auto_write (bool):

        Returns:
        """
        self._comment = s or "K-Points"
        self._kpts_obj = self._build_kpoints()

        if auto_write is None:
            auto_write = self.auto_write

        if auto_write:
            self.write()
