#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotHst
-----------
RMC_POT の .hst ファイルを読み取り、
History::save が 1 回呼ばれたときの履歴レコードを 1 つとして扱う。

・履歴レコードは「generated ～ chi2/F(Q)_set#1」までの 8 個の数値要素から成る。
・ファイル中の表ヘッダ行（generated ...）の直後から、
　空行または非数値行が出るまでを「履歴表」として読み取る。
・History::save の呼び出し回数 ＝ 履歴レコード数。

内部構造：
_records = [
    {
        "generated": int,
        "tried": int,
        "accepted": int,
        "time": int,
        "tried_per_gen": float,
        "acc_per_tried": float,
        "chi2_tot": float,
        "chi2_set1": float,
    },
    ...
]
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotHst:

    def __init__(
        self,
        hst_name: Optional[str] = None,
        cfg_name: Optional[str] = None,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
    ) -> None:
        """
        RmcPotHst を初期化し、.hst ファイルの読み込みとパースを行う。

        hst_name、cfg_name、config のいずれかを指定することで
        対象となる .hst ファイルが決定される。
        hst_name が指定されている場合はそれが最優先される。

        1) cfg_name があればそれが優先
           hst_nameと書いている場合がある
           基本的には hst_name.hst ファイルを読む
           内部的には cfg_name として扱う
        2) config があればそれが優先

        Args:
            hst_name (Optional[str]): 読み込む .hst ファイル名。
            cfg_name (Optional[str]): CFG 名。指定された場合は「{cfg_name}.hst」を対象とする。
            config (Optional[Config]): Config オブジェクト。内部から cfg_name を参照する。
            logger (Optional[XLogger]): 使用するロガー。
        """
        self._logger: XLogger = logger or XLogger(logger_name="RmcPotHst")

        # HST ファイル名は cfg_name を基準に決定する
        if hst_name is not None:
            self._hst_file: str = hst_name

        elif cfg_name is not None:
            self._hst_file: str = f"{cfg_name}.hst"

        elif config is not None:
            config: Config = Config("config.yaml")
            cfg_name: str = config.cfg_name
            self._hst_file: str = f"{cfg_name}.hst"

        else:
            self._logger.error(f"[rmc_pot_hst] hst_name or cfg_name not provided")
            raise NotImplementedError

        # 生ログ行と記録行
        self._lines: List[str] = []
        self._records: List[Dict[str, Union[int, float]]] = []

        # パースしたか？
        self._parsed: bool = False

        self._load_file()
        self._parse()

    # ---------------------------------------------------------------
    # HST ファイル読み込み（純粋に行読み取り）
    # ---------------------------------------------------------------
    def _load_file(self) -> None:
        """
        .hst ファイルを読み込み、生の行データとして保持する。

        ファイルが存在しない場合は警告を出力し、
        内部の行データは空リストとして扱う。
        """
        try:
            with open(self._hst_file, "r") as f:
                self._lines = f.readlines()
            self._logger.info(f"[rmc_pot_hst] Loaded HST: {self._hst_file}")
        except FileNotFoundError:
            self._logger.warning(f"[rmc_pot_hst] HST not found: {self._hst_file}")
            self._lines = []

    # ---------------------------------------------------------------
    # パース（唯一の構造化処理）
    # ---------------------------------------------------------------
    def _parse(self) -> None:
        """

        .hst ファイル中の履歴テーブルを解析し、内部レコード(_records)として格納する。

        「generated」で始まる表ヘッダ行の直後から、
        横方向に 8 個の数値カラムを持つ行のみを
        履歴レコードとして採用する。

        空行または数値に変換できない行が現れた時点で
        履歴テーブルの終端とみなす。

        履歴表の構造（横方向＝1 レコード＝History::save 1 回分）:
            generated
            tried
            accepted
            time
            tried/gen
            acc/tried
            chi2_tot/data_point
            chi2/F(Q)_set#1

        つまり、**横方向に 8 個の数値カラム**を持つ行だけを
        1 レコードとして採用する。
        """
        if self._parsed:
            return

        in_table: bool = False  # 「generated ...」ヘッダ以降かどうか

        for line in self._lines:
            stripped: str = line.strip()

            # 空行
            if stripped == "":
                # すでに履歴表を読み始めていれば、ここで終了
                if in_table:
                    break
                # まだヘッダ前なら単にスキップ
                continue

            # まだヘッダ行を見つけていない段階
            if not in_table:
                # 履歴表ヘッダ行を検出
                if stripped.startswith("generated"):
                    in_table = True  # 次の行からデータ行として扱う
                continue

            # ここに来たら、ヘッダ行の「次以降」＝データ候補行
            items: List[str] = stripped.split()

            # 横方向の要素数が 8 未満なら履歴表の終端とみなす
            if len(items) < 8:
                break

            try:
                # 8 個すべて数値に変換できるかどうかを確認
                generated_val: int = int(items[0])
                tried_val: int = int(items[1])
                accepted_val: int = int(items[2])
                time_val: int = int(items[3])
                tried_per_gen_val: float = float(items[4])
                acc_per_tried_val: float = float(items[5])
                chi2_tot_val: float = float(items[6])
                chi2_set1_val: float = float(items[7])
            except ValueError:
                # 数値に変換できない＝履歴表の終端とみなして終了
                break

            rec: Dict[str, Union[int, float]] = {
                "generated": generated_val,
                "tried": tried_val,
                "accepted": accepted_val,
                "time": time_val,
                "tried_per_gen": tried_per_gen_val,
                "acc_per_tried": acc_per_tried_val,
                "chi2_tot": chi2_tot_val,
                "chi2_set1": chi2_set1_val,
            }
            self._records.append(rec)

        self._parsed = True

    # ==============================================================
    # 互換 API（read_chi2）
    # ==============================================================
    def read_chi2(self) -> Tuple[List[int], List[float]]:
        """
        chi2_tot の履歴を取得するための互換 API。

        旧 RmcPotHst クラスとの互換性を保つため、
        ステップ番号は行番号（0 始まり）として扱う。

        （互換 API）
        旧 RmcPotHst は：
            steps = [0, 1, 2, ...]
            chi2_list = [chi2_tot_of_loop0, chi2_tot_of_loop1, ...]
        の形式で返していたため、それを再現する。

        ※ hst には "step" が存在しないため、
          行番号＝ステップ番号として扱う。

        Returns:
            Tuple[List[int], List[float]]:
                ステップ番号のリストと chi2_tot のリスト。
        """
        steps: List[int] = []
        chi2: List[float] = []

        for i, rec in enumerate(self._records):
            steps.append(i)
            chi2.append(rec["chi2_tot"])

        return steps, chi2

    def detect_convergence(
        self,
        rel_tol: float = 1.0e-2,
        acc_tol: float = 1.0e-3,
        min_consecutive: int = 3,
    ) -> Optional[int]:
        """
        RMC の履歴データに基づいて「実質的な収束点」を判定する。

        本関数は、chi2_tot の絶対値ではなく、
        連続ループ間での「相対的な改善率」と
        探索の活動度（accepted/tried）を用いて収束を定義する。

        判定の考え方は以下の通り：

        1. 各ループ i について、直前ループとの差分から
           相対改善率 delta を計算する。

               delta = (chi2[i-1] - chi2[i]) / chi2[i-1]

        2. 次の 2 条件を同時に満たす場合、
           そのループは「改善がほぼ止まっている」とみなす。

           (a) 相対改善率が十分小さい
               delta < rel_tol

           (b) 試行の受理率が十分小さい
               accepted/tried < acc_tol

           これは、
           「chi2 はほとんど下がらず、かつ探索も動いていない」
           状態を意味する。

        3. 上記の「停滞状態」が min_consecutive 回
           連続して観測された場合にのみ、
           偶然ではない実質的な収束と判断する。

        4. 戻り値として返す loop index は、
           「収束状態に最初に入ったループ番号」であり、
           最終ループ番号ではない点に注意する。

        Args:
            rel_tol (float):
                連続ループ間の相対変化率
                chi2 の相対改善率に対する閾値。
                これ未満の改善は「停滞」とみなす。
            acc_tol (float):
                accepted/tried に対する閾値。
                これ未満は「探索がほぼ停止」とみなす。
            min_consecutive (int):
                停滞状態が連続して必要な最小ループ数。

        Returns:
            Optional[int]:
                収束と判断された最初の loop index。
                判定条件を満たさない場合は None。
        """
        # chi2_tot の履歴（loop ごと）
        chi2 = self.get_chi2_tot()

        # accepted/tried の履歴（探索の活動度）
        acc = self.get_accepted_per_tried()

        # 必要な hstルグの step数に対して
        # 実際のステップ数が少ない場合は自動ループだと無限に回るだけなので
        # エラーを返すようにする
        if len(chi2) < min_consecutive + 1:
            return -1  # 判定不能（行数不足）

        # 停滞状態が何回連続したかを数えるカウンタ
        consec = 0

        # loop 1 以降で前ループとの差分を見る
        for i in range(1, len(chi2)):
            # 前ループの chi2 が非正の場合は評価不能なのでスキップ
            if chi2[i - 1] <= 0.0:
                continue

            # 相対改善率を計算
            delta = (chi2[i - 1] - chi2[i]) / chi2[i - 1]

            # 改善が小さく、かつ探索も止まっているか？
            if delta < rel_tol and acc[i] < acc_tol:
                consec += 1

                # 規定回数連続したら収束と判断
                if consec >= min_consecutive:
                    # 収束状態に「入り始めた」loop index を返す
                    return i - min_consecutive + 1
            else:
                # どちらか一方でも条件を満たさなければリセット
                consec = 0

        # 最後まで条件を満たさなければ未収束
        return None

    def detect_convergence_set1(
        self,
        rel_tol: float = 1.0e-2,
        acc_tol: float = 1.0e-3,
        min_consecutive: int = 2,
    ) -> Optional[int]:
        """
        F(Q) set#1 の chi2 を用いて RMC の実質的収束点を判定する。

        chi2_tot ではなく、hst 中の
        「chi2/F(Q)_set#1」を評価量として用いる点のみが
        detect_convergence() との違いである。

        Returns:
            Optional[int]:
                収束と判断された最初の loop index。
                判定できない場合は None。
        """
        chi2 = self.get_chi2_set1(None)
        acc = self.get_accepted_per_tried(None)

        consec = 0

        for i in range(1, len(chi2)):
            if chi2[i - 1] <= 0.0:
                continue

            delta = (chi2[i - 1] - chi2[i]) / chi2[i - 1]

            if delta < rel_tol and acc[i] < acc_tol:
                consec += 1
                if consec >= min_consecutive:
                    return i - min_consecutive + 1
            else:
                consec = 0

        return None

    # ==============================================================
    # ループ総数
    # ==============================================================
    def get_num_rmc_loops(self) -> int:
        """
        .hst に含まれる履歴レコード数を返す。

        Returns:
            int: RMC ループ回数。
        """
        return len(self._records)

    # ==============================================================
    # 個別 API
    # ==============================================================

    # -----------------------------
    def get_generated(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[int, List[int]]:
        """
        指定したループに対応する値、または全ループ分の値を取得する。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        generated（このループで生成した移動数）を返す。
        loop_index=None → 全ループ list
        loop_index=int → 当該ループの値

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[int, float, List[int], List[float]]:
                対応する値。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["generated"])
            return out

        return self._records[loop_index]["generated"]

    # -----------------------------
    def get_tried(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[int, List[int]]:
        """
        指定したループに対応する tried の値、または全ループ分の値を取得する。

        tried は、そのループにおいて試行された移動回数を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[int, List[int]]:
                tried の値。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["tried"])
            return out
        return self._records[loop_index]["tried"]

    # -----------------------------
    def get_accepted(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[int, List[int]]:
        """
        指定したループに対応する accepted の値、または全ループ分の値を取得する。

        accepted は、そのループにおいて受理された移動回数を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[int, List[int]]:
                accepted の値。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["accepted"])
            return out
        return self._records[loop_index]["accepted"]

    # -----------------------------
    def get_time(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[int, List[int]]:
        """
        指定したループに対応する time の値、または全ループ分の値を取得する。

        time は、そのループに対応する経過時間（hst 出力に記録された値）を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[int, List[int]]:
                time の値。
        """
        if loop_index is None:
            out: List[int] = []
            for rec in self._records:
                out.append(rec["time"])
            return out
        return self._records[loop_index]["time"]

    # -----------------------------
    def get_tried_per_generated(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[float, List[float]]:
        """
        指定したループに対応する tried_per_gen の値、または全ループ分の値を取得する。

        tried_per_gen は、generated に対する tried の比率を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[float, List[float]]:
                tried_per_gen の値。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["tried_per_gen"])
            return out
        return self._records[loop_index]["tried_per_gen"]

    # -----------------------------
    def get_accepted_per_tried(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[float, List[float]]:
        """
        指定したループに対応する acc_per_tried の値、または全ループ分の値を取得する。

        acc_per_tried は、tried に対する accepted の比率を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[float, List[float]]:
                acc_per_tried の値。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["acc_per_tried"])
            return out
        return self._records[loop_index]["acc_per_tried"]

    # -----------------------------
    def get_chi2_tot(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[float, List[float]]:
        """
        全データーセットをまとめた chi
        chi2_tota/data_point

        Args:
            loop_index:

        Returns:

        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_tot"])
            return out
        return self._records[loop_index]["chi2_tot"]

    # -----------------------------
    def get_chi2_set1(
        self,
        loop_index: Optional[int] = None,
    ) -> Union[float, List[float]]:
        """
        指定したループに対応する chi2_set1 の値、または全ループ分の値を取得する。

        chi2_set1 は、hst 出力における
        「chi2/F(Q)_set#1」に対応する chi2 値であり、
        第 1 データセット（set#1）の評価量を表す。

        loop_index を指定しない場合は全ループ分のリストを返し、
        指定した場合は対応する単一の値を返す。

        Args:
            loop_index (Optional[int]):
                取得対象のループ番号。

        Returns:
            Union[float, List[float]]:
                chi2_set1 の値。
        """
        if loop_index is None:
            out: List[float] = []
            for rec in self._records:
                out.append(rec["chi2_set1"])
            return out
        return self._records[loop_index]["chi2_set1"]
