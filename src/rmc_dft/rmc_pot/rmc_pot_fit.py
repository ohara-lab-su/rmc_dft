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
        *,
        fit_name: Optional[str] = None,
        cfg_name: Optional[str] = None,
        config: Optional[Config] = None,  # Config(),
        logger: Optional[XLogger] = None,
    ):
        """

        Args:
            fit_name (str): aaa.fit まで含めた名前
            cfg_name (str): cfg_name.fit (.fitを含むフルのファイル名)
            config (Config):
            logger (XLogger):
        """
        self._logger = logger or XLogger(logger_name="RmcPotFit")
        self._cfg_name = None
        self._config = None
        self.filename = None

        if fit_name:
            self.filename: str = fit_name
        else:
            self._config = config or Config()
            self._cfg_name: Optional[str] = cfg_name or self._config.cfg_name
            self.filename: str = f"{cfg_name}.fit"
        self._logger.info(f"[rmc_pot_fit] == fit filename = {fit_name}")

        # データ格納
        self.Q: List[float] = []
        self.F_calc: List[float] = []
        self.F_exp_renorm: List[float] = []
        self.F_exp_orig: List[float] = []
        self.background: List[float] = []

        # 読み取り
        # self.read_fit()

    def read_fit(
        self,
        filename: Optional[str] = None,
    ) -> Optional[bool]:
        """
        .fit ファイルを読み取り、主要データ列を格納する。
        self.filename: fullname

        Args:
            filename:

        Returns:

        """
        if filename is None:
            filename = self.filename

        self._logger.info(f"[rmc_pot_fit] == read_fit({filename})")

        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            self._logger.error(f"[rmc_pot_fit] file not found: {filename}")
            return False

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

        return True

    # S(Q) に変換するためのメソッド
    def get_S_calc(self) -> List[float]:
        """
        S_calc(Q) = F_calc + 1
        RMC_POT の F(Q) はこちらの形
        """
        return [f + 1.0 for f in self.F_calc]

    # def get_S_calc(self) -> List[float]:
    #    """
    #    S_calc(Q) = 1 + F_calc(Q) / Q
    #    ※ Q=0 は除外または無視する前提（RMC_POT の fit では通常 Q>0）
    #    """
    #    s_list: List[float] = []

    #    for q, f in zip(self.Q, self.F_calc):
    #        if q == 0.0:
    #            s_list.append(1.0)
    #        else:
    #            s_list.append(1.0 + f / q)

    #    return s_list

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
