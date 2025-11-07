#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
import os
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from pymatgen.io.vasp.inputs import Incar
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
        auto_write: bool = True,
        logger: Optional[XLogger] = None,
    ):
        self.incar_name: str = os.path.abspath(incar_name)

        # それぞれの tag 操作で自動的に書き換え
        self.auto_write: bool = auto_write
        self.logger: XLogger = logger or XLogger()
        self.lines: list[str] = []

        # pymatgen Incar()
        self.incar: Incar = Incar()

        if os.path.exists(self.incar_name):
            self._load()
        else:
            self.logger.info(
                f"[VaspIncarUnified] INCAR not found, new one will be created: {self.incar_name}"
            )

    # ==============================
    # 基本入出力
    # ==============================
    def _load(self) -> None:
        """ファイルを読み込み、pymatgen.Incarとテキスト行を両方保持"""
        with open(self.incar_name, "r") as f:
            self.lines = f.readlines()

        # pymatgen Incar()
        self.incar = Incar.from_file(self.incar_name)
        self.logger.info(f"[VaspIncarUnified] Loaded INCAR: {self.incar_name}")

    def write(self) -> None:
        """内部linesを書き戻し"""
        with open(self.incar_name, "w") as f:
            f.writelines(self.lines)
        self.logger.info(f"[VaspIncarUnified] Wrote INCAR: {self.incar_name}")

    # ==============================
    # 行操作
    # ==============================
    def _find_line_index(self, tag: str) -> int | None:
        """指定タグの行番号を返す"""
        tag_upper = tag.upper()
        for i, line in enumerate(self.lines):
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
    def get(self, tag: str, default: Any = None) -> Any:
        """値取得。存在しない場合はdefaultを返す。"""
        return self.incar.get(tag, default)

    def set(self, tag: str, value: Any) -> None:
        """値設定。コメント保持したまま編集。"""
        idx = self._find_line_index(tag)
        new_line = self._format_line(tag, value)

        if idx is not None:
            self.lines[idx] = new_line
            self.logger.info(f"[VaspIncarUnified] Updated tag: {tag} -> {value}")
        else:
            # 新規タグは末尾に追記
            self.lines.append(new_line)
            self.logger.info(f"[VaspIncarUnified] Added tag: {tag} = {value}")

        # pymatgen側更新
        self.incar[tag] = value
        if self.auto_write:
            self.write()

    def remove(self, tag: str) -> None:
        """指定タグを削除"""
        idx = self._find_line_index(tag)
        if idx is not None:
            del self.lines[idx]

            self.logger.info(f"[VaspIncarUnified] Removed tag: {tag}")
            if tag in self.incar:
                del self.incar[tag]
            if self.auto_write:
                self.write()

    def reload(self) -> None:
        """再読込（外部修正反映）"""
        self._load()

    def export_dict(self) -> dict[str, Any]:
        """内部Incar辞書を返す"""
        return dict(self.incar)


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
