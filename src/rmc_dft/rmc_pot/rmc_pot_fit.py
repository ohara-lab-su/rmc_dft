#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import re

from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotFit:
    """
    RMC_POT の .fit ファイルを読み取って、
    Q, F(Q)、renormalized F(Q)_exp などを保持するクラス。
    """

    def __init__(
        self,
        cfg_name: Optional[str] = None,
        config: Optional[Config] = None,  # Config(),
        logger: Optional[XLogger] = None,
    ):
        """

        Args:
            cfg_name (str): cfg_name.fit (.fitを含むフルのファイル名)
            config (Config):
            logger (XLogger):
        """
        self._logger = logger or XLogger(logger_name="RmcPotFit")
        self._config = config or Config()
        self._cfg_name: Optional[str] = cfg_name or self._config.cfg_name
        self.filename: str = f"{cfg_name}.fit"

        # データ格納
        self.Q: List[float] = []
        self.F_calc: List[float] = []
        self.F_exp_renorm: List[float] = []
        self.F_exp_orig: List[float] = []
        self.background: List[float] = []

        # 読み取り
        self.read_fit()

    def read_fit(
        self,
        filename: Optional[str] = None,
    ) -> None:
        """
        .fit ファイルを読み取り、主要データ列を格納する。

        self.filename: fullname
        """
        if filename is None:
            filename = self.filename

        self._logger.info(f"== read_fit({filename})")

        with open(self.filename, "r") as f:
            lines = f.readlines()

        # データブロックは "Total F(Q)" 以降に並ぶため、それを探す
        data_started = False
        data_line_pattern = re.compile(
            r"\s*([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)"
        )

        for line in lines:
            if "Total F(Q)" in line:
                data_started = True
                continue

            if data_started:
                m = data_line_pattern.match(line)
                if m:
                    q = float(m.group(1))
                    f_calc = float(m.group(2))
                    f_exp_ren = float(m.group(3))
                    f_exp_orig = float(m.group(4))
                    bg = float(m.group(5))

                    self.Q.append(q)
                    self.F_calc.append(f_calc)
                    self.F_exp_renorm.append(f_exp_ren)
                    self.F_exp_orig.append(f_exp_orig)
                    self.background.append(bg)

    # S(Q) に変換するためのメソッド
    def get_S_calc(self) -> List[float]:
        """S_calc(Q) = F_calc + 1"""
        return [f + 1.0 for f in self.F_calc]

    def get_S_exp(self) -> List[float]:
        """S_exp(Q) = renormalized F_exp + 1"""
        return [f + 1.0 for f in self.F_exp_renorm]

    def get_S_exp_original(self) -> List[float]:
        """S_exp_original(Q) = original F_exp + 1"""
        return [f + 1.0 for f in self.F_exp_orig]

    def as_dict(self) -> Dict[str, List[float]]:
        """辞書形式で返したい場合に使用"""
        return {
            "Q": self.Q,
            "F_calc": self.F_calc,
            "F_exp_renorm": self.F_exp_renorm,
            "F_exp_orig": self.F_exp_orig,
            "background": self.background,
            "S_calc": self.get_S_calc(),
            "S_exp": self.get_S_exp(),
            "S_exp_orig": self.get_S_exp_original(),
        }
