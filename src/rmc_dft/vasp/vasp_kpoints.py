#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VASP KPOINTS 編集クラス
-----------------------

このモジュールは、VASP の KPOINTS ファイルを安全に読み込み・編集・保存するためのクラスを提供する。
`vasp_incar.py` と同一の設計思想に基づいており、auto_write による自動保存機構を持つ。

主な特徴:
    - 既存 KPOINTS が存在すればそれを読み込み、無ければ Gamma 自動生成 (1x1x1) で作成。
    - get_value() / set_value() により主要な項目を取得・設定可能。
    - コメント・グリッド設定などの最小限の編集に対応。
    - auto_write=True の場合、set_value() 時に自動的にファイル更新。
    - pymatgen.io.vasp.inputs.Kpoints を内部的に使用。

使用例:
    >>> from rmc_dft.vasp.vasp_kpoints import VaspKpoints
    >>> kp = VaspKpoints("KPOINTS", auto_write=True)
    >>> kp.set_value("grid", [4, 4, 4])
    >>> print(kp.get_value("grid"))
    >>> kp.reload_kpoints()

"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable
from pymatgen.io.vasp.inputs import Kpoints
from x_logger import XLogger


class VaspKpoints:
    """
    VASP KPOINTS ファイルを安全に読み込み・編集・保存するためのクラス。

    vasp_incar.py と同様の構造を持ち、auto_write により set_value() 実行時に
    ファイルが自動的に更新される。

    Attributes:
        kpoints_name (str): 読み込む KPOINTS ファイルの名前
        auto_write (bool): 値変更時に自動保存を行うかどうか
        _path (Path): KPOINTS ファイルへのパス
        _kpoints (Kpoints): pymatgen の Kpoints オブジェクト
        _logger (XLogger): ロギング用オブジェクト
    """

    def __init__(
        self,
        kpoints_name: str = "KPOINTS",
        auto_write: bool = True,
        logger: XLogger | None = None,
    ) -> None:
        """
        コンストラクタ

        Args:
            kpoints_name (str): KPOINTS ファイル名
            auto_write (bool): 値変更時に自動で書き込む場合は True
            logger (XLogger): ロガー（未指定なら内部で生成）
        """
        self.kpoints_name = str(Path(kpoints_name))
        self.auto_write = auto_write
        self._path = Path(self.kpoints_name)

        self._logger = logger or XLogger()
        self._logger.info(f"Initializing VaspKpoints: {self.kpoints_name}")

        # KPOINTS ファイル読込
        if self._path.exists():
            self._kpoints = Kpoints.from_file(self.kpoints_name)
            self._logger.info(f"Loaded existing KPOINTS: {self.kpoints_name}")
        else:
            self._kpoints = Kpoints.gamma_automatic()
            self._logger.info(
                f"Created new Gamma-centered KPOINTS: {self.kpoints_name}"
            )

    # ================================================================
    # ファイル I/O 操作
    # ================================================================
    def _write_kpoints(self) -> None:
        """
        内部の Kpoints オブジェクトを KPOINTS ファイルに書き戻す。
        auto_write=True の場合、set_value() 時に自動実行される。
        """
        self._kpoints.write_file(self.kpoints_name)
        self._logger.info(f"Updated: {self.kpoints_name}")

    def reload_kpoints(self) -> None:
        """
        外部で KPOINTS ファイルが変更された場合に再読み込みを行う。
        """
        if self._path.exists():
            self._kpoints = Kpoints.from_file(self.kpoints_name)
            self._logger.info(f"Reloaded: {self.kpoints_name}")

    # ================================================================
    # 値取得関連
    # ================================================================
    def get_value(self, key: str) -> Any | None:
        """
        KPOINTS 内の特定項目を取得する。

        Args:
            key (str): 取得対象のキー名（'mode', 'grid', 'comment', 'num_kpts' など）

        Returns:
            Any | None: 対応する値（存在しない場合は None）
        """
        k = key.lower()
        if k == "mode":
            return self._kpoints.style.name
        elif k == "grid":
            return self._kpoints.kpts
        elif k == "comment":
            return self._kpoints.comment
        elif k == "num_kpts":
            return self._kpoints.num_kpts
        elif k == "labels":
            return getattr(self._kpoints, "labels", None)
        return None

    # ================================================================
    # 値設定関連
    # ================================================================
    def set_value(self, key: str, value: Any) -> None:
        """
        KPOINTS 内の値を設定する。

        Args:
            key (str): 設定対象のキー名（'grid', 'gamma', 'comment' など）
            value (Any): 設定する値

        Notes:
            - grid: Monkhorst-Pack 方式で k-point グリッドを設定
            - gamma: Gamma-centered 自動生成に切り替え
            - comment: コメント行の変更
        """
        k = key.lower()
        if k == "grid":
            # 例: [4, 4, 4]
            self._kpoints = Kpoints.monkhorst_automatic(kpts=value)
            self._logger.info(f"Set Monkhorst grid: {value}")
        elif k == "gamma":
            self._kpoints = Kpoints.gamma_automatic()
            self._logger.info("Set Gamma-centered KPOINTS")
        elif k == "comment":
            self._kpoints.comment = str(value)
            self._logger.info(f"Updated comment: {value}")
        else:
            self._logger.warning(f"Unknown key for set_value: {key}")
            return

        if self.auto_write:
            self._write_kpoints()

    # ================================================================
    # 出力関連
    # ================================================================
    def export_dict(self) -> dict:
        """
        現在の KPOINTS 内容を辞書形式で返す。

        Returns:
            dict: KPOINTS の辞書形式データ
        """
        return self._kpoints.as_dict()

    def __repr__(self) -> str:
        """
        インスタンスの簡易表現。
        """
        return f"<VaspKpoints file={self.kpoints_name} auto_write={self.auto_write}>"


# ================================================================
# 動作テスト
# ================================================================
if __name__ == "__main__":
    logger = XLogger()
    kpoints = VaspKpoints("KPOINTS", auto_write=True, logger=logger)

    logger.info(f"Current mode: {kpoints.get_value('mode')}")
    logger.info(f"Current grid: {kpoints.get_value('grid')}")

    # 既存グリッドの変更
    kpoints.set_value("grid", [3, 3, 3])

    # コメントの設定
    kpoints.set_value("comment", "Test grid modification")

    # Gamma 生成に切り替え
    kpoints.set_value("gamma", None)

    # 再読み込みテスト
    kpoints.reload_kpoints()
    logger.info(f"Reloaded grid: {kpoints.get_value('grid')}")

    # 辞書形式で出力確認
    logger.info(f"KPOINTS dict: {kpoints.export_dict()}")
