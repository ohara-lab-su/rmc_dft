#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from pymatgen.io.vasp.inputs import Incar

from rmc_dft.config import Config
from x_logger import XLogger


class VaspIncar:
    """
    VASP INCAR 編集を一元管理するクラス。
    pymatgen.Incar による値操作と、コメント保持を両立する。

    主な特徴:
        - 既存INCARファイルを安全に読み込み、コメント/空行を保持。
        - 値の追加・更新・削除をサポート。
        - pymatgen.Incar 互換インターフェース (get/set/remove/export)。
    """

    def __init__(
        self,
        incar_name: str = "INCAR",
        logger: Optional[XLogger] = None,
        *,
        config: Optional[Config] = None,
        auto_write: bool = True,
    ) -> None:
        """

        Args:
            incar_name (str):
            logger (XLogger):
            auto_write (bool):
        """
        self.incar_name: str = os.path.abspath(incar_name)

        # それぞれの tag 操作で自動的に書き換え
        self.auto_write: bool = auto_write
        self._logger: XLogger = logger or XLogger()
        self._config: Config = config or Config()
        self._lines: list[str] = []

        # pymatgen Incar()
        self._incar: Incar = Incar()

        if os.path.exists(self.incar_name):
            self.load()

    # ==============================
    # 基本入出力
    # ==============================

    def load(self) -> None:
        """
        ファイルを読み込み、pymatgen.Incarとテキスト行を両方保持
        """
        with open(self.incar_name, "r") as f:
            self._lines = f.readlines()

        # pymatgen Incar()
        self._incar = Incar.from_file(self.incar_name)
        self._logger.info(f"[VaspIncar] Loaded INCAR: {self.incar_name}")

    def write(self) -> None:
        """内部linesを書き戻し"""
        with open(self.incar_name, "w") as f:
            f.writelines(self._lines)
        self._logger.info(f"[VaspIncar] Wrote INCAR: {self.incar_name}")

    # ==============================
    # 行操作
    # ==============================
    def _find_line_index(
        self,
        tag: str,
    ) -> Optional[int]:
        """
        指定タグの行番号を返す
        実際の INCAR に、指定のタグがどの行にあるのか？を調べる
        """
        tag_upper = tag.upper()
        for i, line in enumerate(self._lines):
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=")[0].strip().upper()
                if key == tag_upper:
                    return i
        return None

    @staticmethod
    def _format_line(tag: str, value: Any) -> str:
        """整形ルール統一"""
        return f"{tag:<15} = {value}\n"

    # ==============================
    # 値操作（pymatgen互換）
    # ==============================
    def get(
        self,
        tag: str,
        default: Any = None,
    ) -> Any:
        """
        値取得。存在しない場合はdefaultを返す。

        Args:
            tag (str):
            default (Any):

        Returns:
            Any:
        """
        return self._incar.get(tag, default)

    def get_tag(self, tag: str, default: Any = None) -> Any:
        return self.get(tag, default)

    def set(
        self,
        tag: str,
        value: Any,
    ) -> None:
        """
        値設定。コメント保持したまま編集。

        Args:
            tag (str):  INCAR のキー
            value (Any):  value

        Returns:
            None:
        """
        idx = self._find_line_index(tag)
        new_line = self._format_line(tag, value)

        if idx is not None:
            self._lines[idx] = new_line
            self._logger.info(f"[VaspIncar] Updated tag: {tag} -> {value}")
        else:
            # 新規タグは末尾に追記
            self._lines.append(new_line)
            self._logger.info(f"[VaspIncar] Added tag: {tag} = {value}")

        # pymatgen側更新
        self._incar[tag] = value

        if self._config is not None:
            if self._config.vasp_incar_tags is None:
                self._config.vasp_incar_tags = {}
            ##########
            self._config.vasp_incar_tags[tag] = value
            ##########

        if self.auto_write:
            self.write()

    def set_tag(self, tag: str, value: Any) -> None:
        self.set(tag, value)

    def remove(self, tag: str) -> None:
        """指定タグを削除"""
        idx = self._find_line_index(tag)
        if idx is not None:
            del self._lines[idx]

            self._logger.info(f"[VaspIncar] Removed tag: {tag}")

            if tag in self._incar:
                del self._incar[tag]

            if self._config is not None and self._config.vasp_incar_tags is not None:
                self._config.vasp_incar_tags.pop(tag, None)

            if self.auto_write:
                self.write()

    def reload(self) -> None:
        """再読込（外部修正反映）"""
        self.load()

    def export_dict(self) -> Dict[str, Any]:
        """内部Incar辞書を返す"""
        return dict(self._incar)

    def diff_with(self, other: "VaspIncar") -> Dict[str, Tuple[Any, Any]]:
        """
        2つの VaspIncar インスタンスを比較し、値が異なるタグのみを返す。

        コメント行や元の行順序は比較対象に含めず、
        内部で保持している ``pymatgen.Incar`` 辞書
        （``self._incar`` と ``other._incar``）の値だけで比較を行う。

        Args:
            other (VaspIncar):
                比較対象となる VaspIncar インスタンス。

        Returns:
            Dict[str, Tuple[Any, Any]]:
                値が異なるタグだけを含む辞書。
                キーがタグ名、値は ``(self 側の値, other 側の値)`` のタプル。
        """
        diff: Dict[str, Tuple[Any, Any]] = {}

        keys = set(self._incar.keys()) | set(other._incar.keys())

        for key in sorted(keys):
            v1 = self._incar.get(key, None)
            v2 = other._incar.get(key, None)

            if v1 != v2:
                diff[key] = (v1, v2)

        return diff


if __name__ == "__main__":
    import os
    from x_logger import XLogger
    from rmc_dft.vasp.vasp_incar import VaspIncar  # 絶対インポート

    _logger = XLogger()
    incar_file = "INCAR"

    # ===== ケースA: INCAR が無い場合（新規作成 -> 追加 -> 読み直し） =====
    if not os.path.exists(incar_file):
        _logger.info("[TEST:A] INCAR が存在しないため、新規に作成します。")
        incar = VaspIncar(
            incar_file,
            auto_write=True,
            logger=_logger,
        )

        # 新規追加（例）
        add_entries = {
            "SYSTEM": "test_system",
            "GGA": "PE",
            "ISPIN": 2,
            "ISMEAR": 0,
            "SIGMA": 0.05,
            "EDIFF": 1e-5,
            "ISYM": 0,
        }
        for k, v in add_entries.items():
            incar.set(k, v)
            _logger.info(f"[TEST:A] add {k} = {v}")

        # 読み直し確認
        incar_re = VaspIncar(incar_file, auto_write=False, logger=_logger)
        for k in add_entries.keys():
            _logger.info(f"[TEST:A] re-read {k} = {incar_re.get(k)}")

        _logger.info("[TEST:A] コメント保持は目視で INCAR を確認してください。")
        raise SystemExit(0)

    else:
        # ===== ケースB: INCAR がある場合（既存確認→追加→更新→読み直し） =====
        _logger.info("[TEST:B] 既存の INCAR を用いてテストを行います。")

        # 既存値の確認（例）
        check_keys = [
            "SYSTEM",
            "GGA",
            "ISPIN",
            "ISMEAR",
            "SIGMA",
            "EDIFF",
            "ISYM",
            "IBRION",
            "LORBIT",
            "NEDOS",
        ]
        incar = VaspIncar(incar_file, auto_write=True, logger=_logger)
        for k in check_keys:
            _logger.info(f"[TEST:B] before {k} = {incar.get(k)}")

        # 無かったら追加するキー（例）
        add_only = {
            "IBRION": 2,
            "LORBIT": 11,
            "NEDOS": 1500,
        }
        for k, v in add_only.items():
            if incar.get(k) is None:
                incar.set(k, v)
                _logger.info(f"[TEST:B] add {k} = {v}")
            else:
                _logger.info(f"[TEST:B] skip add (exists) {k} = {incar.get(k)}")

        # 既存キーの更新（例）
        updates = {
            "ISMEAR": 0,
            "EDIFF": 1e-5,
        }
        for k, v in updates.items():
            before = incar.get(k)
            incar.set(k, v)
            after = incar.get(k)
            _logger.info(f"[TEST:B] update {k}: {before} -> {after}")

        # 読み直し確認
        incar_re = VaspIncar(incar_file, auto_write=False, logger=_logger)
        for k in set(list(add_only.keys()) + list(updates.keys())):
            _logger.info(f"[TEST:B] re-read {k} = {incar_re.get(k)}")

        _logger.info(
            "[TEST:B] コメント・空行・順序の保持は目視で INCAR を確認してください。"
        )
