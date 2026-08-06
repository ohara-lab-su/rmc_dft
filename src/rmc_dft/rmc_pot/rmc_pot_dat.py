#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
RMC_POT *.dat の固定形式 / 自由形式 自動切替ラッパークラス。
"""

import time
import shutil
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
        """RmcPotDat ラッパーを生成する。

        Args:
            config: Config インスタンス。
            logger: XLogger インスタンス。
            cfg_name: *.dat の拡張子を除いたファイル名。
            auto_write: 自動保存フラグ。
            use_free_format: 新規 *.dat 作成時に使う既定形式。
                True は自由形式、False は固定形式、None は自由形式を既定とする。

        Notes:
            コンストラクタでは *.dat の読込み・生成を行わない。
            実際の初期化は init() で行う。
        """
        self._logger = logger or XLogger()
        self._config = config or Config()
        self._cfg_name = cfg_name or self._config.cfg_name
        self._auto_write = auto_write
        self._use_free_format = True if use_free_format is None else use_free_format
        self._impl: Optional[Union[RmcPotDatFree, RmcPotDatFixed]] = None

    def set_free_format(self, use_free_format: bool) -> None:
        """新規 *.dat 作成時に使用する形式を設定する。

        init() 完了後、または既存 *.dat がある場合は、既存ファイルの形式を
        変更しない。
        """
        self._use_free_format = use_free_format
        target_path = Path(f"{self._cfg_name}.dat")
        if target_path.exists():
            detected = self._detect_if_free_format(target_path)
            format_name = "自由形式" if detected else "固定形式"
            self._logger.info(
                f"[rmc_pot_dat] 既存 {target_path.name} を使用します。形式は {format_name} です。"
            )

    def init(
        self,
        *,
        use_free_format: Optional[bool] = None,
        prefer_existing: bool = True,
    ) -> None:
        """*.dat を読み込むか、各形式クラスの初期値から新規作成する。

        Args:
            use_free_format: 新規作成時の形式。None の場合はコンストラクタまたは
                set_free_format() で保持した形式を使う。
            prefer_existing: 既存 *.dat がある場合に既存ファイルを優先する。
                False の場合は既存ファイルをバックアップし、指定形式の初期値で
                作り直す。
        """
        if use_free_format is not None:
            self._use_free_format = use_free_format

        target_path = Path(f"{self._cfg_name}.dat")
        if target_path.exists() and prefer_existing:
            is_free = self._detect_if_free_format(target_path)
            format_name = "自由形式" if is_free else "固定形式"
            self._logger.info(
                f"[rmc_pot_dat] 既存 {target_path.name} を使用します。形式は {format_name} です。"
            )
        else:
            is_free = self._use_free_format
            if target_path.exists():
                backup_path = target_path.with_suffix(target_path.suffix + ".bak_init")
                shutil.copy2(target_path, backup_path)
                target_path.unlink()
                self._logger.info(
                    f"[rmc_pot_dat] 既存 {target_path.name} を {backup_path.name} に退避しました。"
                )
            format_name = "自由形式" if is_free else "固定形式"
            self._logger.info(
                f"[rmc_pot_dat] {target_path.name} を {format_name} の初期値から作成します。"
            )

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
        if self._impl is None:
            raise RuntimeError("RmcPotDat.init() がまだ呼ばれていません。")
        return getattr(self._impl, name)


def main() -> None:
    """自由形式 DAT を選択し、基本設定を書き込む利用例。

    Notes:
        ``sample_dat.dat`` が存在しない場合は、自由形式のデフォルト DAT を
        作成する。SNC 関係の操作は従来どおり ``RmcPotDatFree`` に委譲される。
    """
    dat = RmcPotDat(
        cfg_name="sample_dat",
        auto_write=False,
        use_free_format=True,
    )
    dat.set_comment("SiO2 sample", auto_write=False)
    dat.set_density(0.0665715652, auto_write=False)
    dat.set_cutoffs([1.9, 1.1, 1.9], auto_write=False)
    dat.write()
    print("generated: sample_dat.dat")


if __name__ == "__main__":
    main()
