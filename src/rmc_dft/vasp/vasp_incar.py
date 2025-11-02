#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

VASP の INCAR 編集機能を担当するクラス群。

本モジュールは、RMC-DFT システムにおける
「VASP 入力編集部」を独立モジュールとして管理することが目的

主構成:
    - INCAR の読み込み・編集・削除・再読み込みを行う。
    - pymatgen.io.vasp.inputs.Incar を利用。
    - 実ファイルが存在しない場合は空の INCAR から開始。
    - set_value で即座にファイルへ反映（存在しない場合は新規作成）。
    - get_value は None を返した場合、VASP デフォルト値を意味する。

テスト:
    if __name__ == "__main__" 以下で、INCAR が
        (A) 既存する場合
        (B) 存在しない場合
    の両ケースを検証する。
"""

import os
from typing import Any, Optional, Dict
from pymatgen.io.vasp.inputs import Incar

from x_logger import XLogger


class VaspIncar:
    """
    VASP の INCAR ファイルを編集・管理するクラス。
    多々たんに pymatgen のうすーいラッパー

    責務:
        - INCAR ファイルの読み込みと書き込み。
        - タグ値の取得、設定、削除、再読み込み。
        - ファイルが存在しない場合の初期化と作成。

    非責務:
        - VASP 実行・他入力ファイル（POSCAR, POTCAR 等）の管理。
        - ファイルフォーマットの一般化や抽象化。

    主要設計:
        - 実ファイルが存在する場合はその内容を基準とする。
        - 実ファイルが存在しない場合は空の Incar() を生成する。
        - set_value() 呼び出し時に即時ファイル書き込みを行う。
        - get_value() は None を返す場合、VASP のデフォルト値を意味する。
    """

    def __init__(
        self,
        incar_name: str = "INCAR",
        logger: XLogger = None,
    ) -> None:
        """
        コンストラクタ。
        指定したファイル名の INCAR を読み込み、存在しない場合は空から開始する。

        Args:
            incar_name (str):
                編集対象の INCAR ファイル名（相対パスまたは絶対パス）。
                既定値は "INCAR"。
        """
        if logger is None:
            logger = XLogger()
        self._logger = logger

        self.incar_name: str = incar_name  # INCAR

        # Pymatgen Module
        self.incar_data: Incar = self._load_incar()  # Incar オブジェクトをロード

    def _load_incar(
        self,
        incar_name: str = None,
    ) -> Incar:
        """
        INCAR ファイルを読み込み、Incar オブジェクトを生成する。

        Returns:
            Incar: 読み込んだ Incar オブジェクト。
                   ファイルが存在しない場合は空の Incar()。
        """
        self._logger.info("== incar reload")
        if not incar_name:
            incar_name = self.incar_name

        file_exists: bool = os.path.exists(incar_name)
        if file_exists:
            # pymatgen で INCAR のロード
            return Incar.from_file(incar_name)
        else:
            return Incar()

    def reload_incar(
        self,
        incar_name: str = None,
    ) -> bool:
        """
        外部で INCAR が編集された場合に再読み込みを行う。

        動作:
            - ファイルが存在する場合は再度 Incar.from_file() を実行。
            - 存在しない場合は空の Incar() にリセットする。
        """
        self._logger.info("== reload incar")
        self.incar_data = self._load_incar(incar_name)
        return True

    def get_value(
        self,
        tag_name: str,
    ) -> Optional[Any]:
        """
        指定されたタグの値を取得する。

        Args:
            tag_name (str): 取得するタグ名（例: "ENCUT", "ISPIN"）。

        Returns:
            Optional[Any]: タグ値。
                - タグが存在すればその値。
                - 存在しない場合は None（VASP デフォルト値を意味する）。
        """
        tag_upper: str = tag_name.upper()
        tag_exists: bool = tag_upper in self.incar_data

        if tag_exists:
            return self.incar_data[tag_upper]
        else:
            return None

    def set_value(
        self,
        tag_name: str,
        value: Any,
        force_write: bool = False,
    ) -> None:
        """
        指定されたタグの値を設定し、即座にファイルへ反映する。

        Args:
            tag_name (str): 設定するタグ名。
            value (Any): 設定する値（数値、文字列、真偽値など）。
            force_write (bool): ファイル書き出しの有無 (既存のINCAR情報を消すので注意)
        """
        tag_upper: str = tag_name.upper()
        self.incar_data[tag_upper] = value

        # ここで書き出すのはテスト用(既存のINCAR情報を消すので)
        if write:
            self.incar_data.write_file(self.incar_name)

    def remove_value(
        self,
        tag_name: str,
        force_write: bool = False,
    ) -> None:
        """
        指定されたタグを削除し、ファイルへ反映する。
        基本的にファイルへ反映するので注意（既存の INCAR のコメント構造が壊れるため）

        デフォルトは force_write = False のために、デフォルトではこのメソッドは何もしない

        Args:
            tag_name (str): 削除対象のタグ名。
            force_write (bool): 強制的にファイルの読みき（デフォルトFalse)
        """
        tag_upper: str = tag_name.upper()
        tag_exists: bool = tag_upper in self.incar_data

        if force_write:
            if tag_exists:
                del self.incar_data[tag_upper]
                self.incar_data.write_file(self.incar_name)

    def export_dict(self) -> Dict[str, Any]:
        """
        現在保持している INCAR 内容を辞書形式で返す。

        Returns:
            Dict[str, Any]: タグ名をキー、値を値とする辞書。
        """
        return dict(self.incar_data)


if __name__ == "__main__":
    """
    機能テスト。
        1) INCAR が存在する場合。
        2) INCAR が存在しない場合。
    """

    # ---------------------------------------------------------------
    # (1) INCAR がある場合
    # ---------------------------------------------------------------
    ## existing_incar_name: str = "INCAR_existing_case"

    ## # テスト準備: 既存ファイルを再生成
    ## if os.path.exists(existing_incar_name):
    ##     os.remove(existing_incar_name)
    ## with open(existing_incar_name, "w", encoding="utf-8") as f:
    ##     f.write("ENCUT = 450\n")
    ##     f.write("ISPIN = 2\n")

    ## print("=== ケースA: 既存 INCAR がある場合 ===")

    ## # クラス生成と初期読み込み確認
    ## incar_a = VaspIncar(incar_name=existing_incar_name)
    ## print("初期読み込み:", incar_a.export_dict())

    ## # タグ値の取得（既存値と未設定タグ）
    ## print("get_value('ENCUT') =", incar_a.get_value("ENCUT"))
    ## print("get_value('LREAL') =", incar_a.get_value("LREAL"))

    ## # 値の上書き設定
    ## print("\n--- set_value テスト ---")
    ## incar_a.set_value("ENCUT", 520)
    ## print("ENCUT=520 設定後:", incar_a.export_dict())

    ## # タグ削除
    ## print("\n--- remove_value テスト ---")
    ## incar_a.remove_value("ISPIN")
    ## print("ISPIN 削除後:", incar_a.export_dict())

    ## # 外部編集を模擬（手動追記）
    ## with open(existing_incar_name, "a", encoding="utf-8") as f:
    ##     f.write("LREAL = .FALSE.\n")

    ## # 再読み込み確認
    ## incar_a.reload_incar()
    ## print("\n--- reload_incar テスト ---")
    ## print("再読み込み後:", incar_a.export_dict())

    # ---------------------------------------------------------------
    # INCAR が存在しない場合
    # ---------------------------------------------------------------
    missing_incar_name: str = "INCAR_missing_case"

    if os.path.exists(missing_incar_name):
        os.remove(missing_incar_name)

    print("\n=== ケースB: INCAR が存在しない場合 ===")

    # クラス生成（空から開始）
    incar_b = VaspIncar(incar_name=missing_incar_name)
    print("初期状態:", incar_b.export_dict())

    # 値の取得（None 返却確認）
    print("get_value('ENCUT') =", incar_b.get_value("ENCUT"))

    # 新規タグ設定（ファイルが自動作成される）
    incar_b.set_value("ENCUT", 520)
    incar_b.set_value("EDIFF", 1e-5)
    print("\n--- 新規ファイル作成と設定確認 ---")
    print("設定後:", incar_b.export_dict())

    # タグ削除テスト
    incar_b.remove_value("EDIFF")
    print("EDIFF 削除後:", incar_b.export_dict())

    # 外部編集を模擬（ISMEAR 追記）
    with open(missing_incar_name, "a", encoding="utf-8") as f:
        f.write("ISMEAR = 0\n")

    # 再読み込み確認
    incar_b.reload_incar()
    print("\n--- 再読み込み確認 ---")
    print("再読み込み後:", incar_b.export_dict())
