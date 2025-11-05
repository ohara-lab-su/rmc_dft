#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotDat: RMC_POT の .dat 入力ファイル編集クラス

- 本クラスは「タグ名ではなく行番号に意味がある」RMC_POT の .dat 形式を前提
- 各行は「値 [任意空白] ! コメント」の構造で、コメントは保持したまま値のみ更新
- 代表的に編集頻度の高い行:
    2行目: number density (float)
    3行目: cut offs (float×3)
    4行目: maximum moves (float×2)
    5行目: r spacing (float)
- 真偽値は .true. / .false. に正規化して出力
- 任意行の直接取得/更新用に get_line()/set_line() も提供
"""

from dataclasses import dataclass
from typing import List, Sequence, Union, Tuple, Optional
from pathlib import Path

from x_logger import XLogger


@dataclass
class _Line:
    """
    内部表現: 1 行ぶんの値とコメント。

    Attributes:
        value: '!' より左側の文字列（前後空白は内部では保持しない）
        comment: '!' 以降のコメント文字列（先頭の '!' は保持しない）
        had_bang: コメントが存在したか
    """

    value: str
    comment: str = ""
    had_bang: bool = False

    def render(self) -> str:
        """現在の値とコメントから 1 行のテキストを生成する。"""
        if self.had_bang:
            # 値 + 1 つ以上の空白 + "! " + コメント
            value_part = self.value.rstrip()
            return f"{value_part} ! {self.comment.strip()}\n"
        # コメントがなかった行は値のみ
        return f"{self.value.rstrip()}\n"


class RmcPotDat:
    """
    RMC_POT の .dat ファイルを行番号ベースで編集するためのクラス。

    使い方:
        dat = RmcPotDat("/abs/path/to/aaa.dat", auto_write=True)
        rho = dat.get_density()
        dat.set_cutoffs((2.5, 2.2, 2.0))  # auto_write=True なら即時保存
        dat.write()  # 明示保存も可能

    注意:
        - 行番号は 1 始まり。内部処理では 0 始まりのリストに対応付けます。
        - 既存コメントは保持します。コメント無しの行へ値を設定した場合はコメント無しで書き出します。
        - 指定の .dat 形式（添付例）を前提に実装しています。
    """

    def __init__(
        self,
        dat_name: str,
        auto_write: bool = True,
        logger: XLogger | None = None,
    ) -> None:
        """
        Args:
            dat_name (str): xxxx.dat の絶対パス、基本名前（拡張子は付けない）
            auto_write (bool): True の場合 set_* / set_line で即時書き出し
            logger (XLogger):
        """
        self._logger = logger or XLogger()
        self.dat_name: str = dat_name
        self._lines: list[_Line] = []
        self._auto_write: bool = auto_write
        self._load()

    # --------------------
    # 静的フォーマット関数群（クラス内に集約）
    # --------------------
    @staticmethod
    def _to_bool_token(v: bool | str) -> str:
        """
        真偽入力を .true. / .false. に正規化する。

        Args:
            v: bool もしくは真偽を表す文字列（大文字小文字は不問）

        Returns:
            ".true." もしくは ".false."
        """
        if isinstance(v, bool):
            return ".true." if v else ".false."
        s = str(v).strip().lower()
        if s in (".true.", "true", "t", "1", "yes", "y"):
            return ".true."
        if s in (".false.", "false", "f", "0", "no", "n"):
            return ".false."
        # 不明値はそのまま返さず、明示的に例外
        raise ValueError(f"真偽として解釈できません: {v!r}")

    @staticmethod
    def _fmt_number(x: Union[int, float]) -> str:
        """
        数値を .dat に過度な科学表記を使わず整形する。

        仕様:
          - int はそのまま
          - float は小数点以下の無意味なゼロを取り除く
          - 非常に大きい/小さい値でない限り指数表記は避ける
        """
        if isinstance(x, int) or (isinstance(x, float) and x.is_integer()):
            return str(int(x))
        # 通常の小数表現を優先
        s = f"{float(x):.12g}"  # 12桁で十分に安定
        return s

    @classmethod
    def _fmt_sequence(cls, seq: Sequence[Union[int, float]]) -> str:
        """数値列を空白区切りで整形。"""
        return " ".join(cls._fmt_number(v) for v in seq)

    # --------------------
    # 基本 I/O
    # --------------------
    def _load(self) -> None:
        """ファイルを読み込んで内部行リストを構築。"""
        self._logger.info(f"== load({self.dat_name}.dat)")

        p = Path(f"{self.dat_name}.dat")
        if not p.exists():
            raise FileNotFoundError(
                f".dat ファイルが見つかりません: {p} (.dat は自動付加されます)"
            )

        self._lines.clear()
        with p.open("r", encoding="utf-8") as f:
            for raw in f.readlines():
                # 行末改行を残した解析は不要 -> strip はしない、'!' で分割のみ
                if "!" in raw:
                    left, right = raw.split("!", 1)
                    self._lines.append(
                        _Line(value=left.strip(), comment=right.strip(), had_bang=True)
                    )
                else:
                    self._lines.append(
                        _Line(value=raw.strip(), comment="", had_bang=False)
                    )

    def write(self, out_name: str | None = None) -> None:
        """
        現在の内容を書き出す (.dat は自動付加される)

        Args:
            out_name (str): 出力先。未指定なら self.dat_name に上書き保存。
        """
        target = Path(f"{self.dat_name if out_name is None else out_name}.dat")
        with target.open("w", encoding="utf-8") as f:
            for ln in self._lines:
                f.write(ln.render())
        self._logger.info(f"== write({target})")

    # --------------------
    # 任意行の get / set
    # --------------------
    def get_line(self, line_no_1based: int) -> str:
        """
        任意行の値部分を返す（コメントは含めない）
        本来の RMC_POT を編集するための raw メソッド

        Args:
            line_no_1based: 1 始まりの行番号

        Returns:
            値（文字列）
        """
        idx = self._index(line_no_1based)
        return self._lines[idx].value

    def set_line(
        self,
        line_no_1based: int,
        value: Union[str, int, float, Sequence[Union[int, float]], bool],
        *,
        auto_write: bool | None = None,
    ) -> None:
        """
        任意行の値部分を更新（コメントは保持）。

        Args:
            line_no_1based: 1 始まりの行番号
            value: 置換値（数値/数値列/真偽/文字列）
            auto_write: True 指定で即時保存。None の場合はインスタンス既定(self._auto_write)に従う。

        Raises:
            IndexError: 行番号が範囲外
            ValueError: 真偽解釈など不正値
        """
        idx = self._index(line_no_1based)
        self._lines[idx].value = self._coerce_value(value)
        do_write = self._auto_write if auto_write is None else auto_write
        if do_write:
            self.write()

    # --------------------
    # ヘルパ
    # --------------------
    def _index(self, line_no_1based: int) -> int:
        """
        1 始まり行番号 -> 0 始まりインデックスに変換し、範囲を検証。

        Args:
            line_no_1based (int): 1 始まり

        Returns:

        """
        idx = line_no_1based - 1
        if idx < 0 or idx >= len(self._lines):
            raise IndexError(
                f"行番号が範囲外です: {line_no_1based} (全 {len(self._lines)} 行)"
            )
        return idx

    @classmethod
    def _coerce_value(
        cls,
        value: Union[str, int, float, Sequence[Union[int, float]], bool],
    ) -> str:
        """
        入力値を .dat へ書き込むための文字列に正規化。

        ルール:
          - str: そのまま（前後空白は適宜呼び出し側で制御）
          - bool: .true. / .false.
          - Sequence[Union[int, float]]: 空白区切りで整形
          - Number: 数値フォーマットで整形
        """
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, bool):
            return cls._to_bool_token(value)
        if isinstance(value, (int, float)):
            return cls._fmt_number(value)
        try:
            seq = list(value)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError(f"未対応の型です: {type(value)!r}") from exc
        return cls._fmt_sequence(seq)

    # --------------------
    # 代表フィールド: density / cutoffs / max_moves / r_spacing
    # --------------------
    def get_comment(self) -> str:
        """1 行目 comment を str で返す。"""
        return str(self.get_line(1).split()[0])

    def set_comment(
        self,
        comment: str,
        *,
        auto_write: bool | None = None,
    ) -> None:
        """1 行目 comment を更新。"""
        self.set_line(1, comment, auto_write=auto_write)

    def get_density(self) -> float:
        """
        2 行目 density を float で返す。

        例)
        0.0842566414       ! number densit

        - 系の数密度（number density） 単位は原子数 / Å^3。
        - cfg ファイル中の原子数とシミュレーションボックス体積の
          関係で一致させる必要があります。（二重定義）
        """
        return float(self.get_line(2).split()[0])

    def set_density(
        self, rho: Union[int, float], *, auto_write: bool | None = None
    ) -> None:
        """2 行目 density を更新。"""
        self.set_line(2, rho, auto_write=auto_write)

    def get_cutoffs(self) -> List[Union[int, float]]:
        """
        3 行目 cut offs を (c1, c2, c3) で返す。

        例)
        1 1 1 1 1 1 ! cut offs

        - 説明: 原子種ごとのカットオフ距離（またはカットオフの有無フラグ）を指定するフィールド。
        - 実務上: 多くの実装では「最低許容距離（min separation）」や「ペアごとの距離カットオフ」を指定。
                 型の数 (ntypes) に応じた個数を並べる必要がある
        - 並びは3元型の場合、11,12,13,22,23,33となっている
        - n元型の場合、11,12,13,14, ... , 1n, 22, 23,...,2n, 33, 34, ..., 3n, ..., nn となる
        """
        toks = self.get_line(3).split()
        try:
            return [tok for tok in toks]
        except ValueError as exc:
            raise ValueError(f"cut offs 行に数値以外の値があります: {toks!r}") from exc

    def set_cutoffs(
        self,
        values: Sequence[Union[int, float]],
        *,
        auto_write: bool | None = None,
    ) -> None:
        """
        3 行目 cut offs を更新。可変長対応。

        Args:
            values (Sequence[Union[int, float]]):
                 原子種ごとのカットオフ距離リストを指定する。
                 要素数は ntypes に応じて可変（3 要素に限定しない）。
            auto_write (bool | None, optional):
        """
        seq = list(values)
        for v in seq:
            if not isinstance(v, (int, float)):
                raise TypeError(f"cut offs には数値のみを指定してください: {v!r}")

        # set_line はコメントを保持したまま値部を置換する
        self.set_line(3, seq, auto_write=auto_write)

    def get_max_moves(self) -> Tuple[float, float]:
        """
        4 行目 maximum moves を (m1, m2) で返す。

        例)
        0.01 0.01 0.01   ! maximum moves

        - 説明: 原子移動の最大振幅（1 回の move での最大変位）を指定します。複数値が並んでいる場合はタイプごと、または移動タイプごとの設定になっていることがあります。単位は Å。
        - 備考: 値が小さいほど受理率が高くなるがサンプリング効率は落ちます。調整して受理率を 20–50% 程度に保つのが一般的です。
        """
        toks = self.get_line(4).split()
        if len(toks) < 2:
            raise ValueError(f"maximum moves 行の要素数が不足: {toks!r}")
        return float(toks[0]), float(toks[1])

    def set_max_moves(
        self,
        values: Sequence[Union[int, float]],
        *,
        auto_write: bool | None = None,
    ) -> None:
        """4 行目 maximum moves を更新。"""
        seq = list(values)
        if len(seq) != 2:
            raise ValueError(f"maximum moves は 2 要素が必要です: {values!r}")
        self.set_line(4, seq, auto_write=auto_write)

    def get_r_spacing(self) -> float:
        """
        5 行目 r spacing を float で返す。i

        例)
        0.025        ! r spacing

        - 説明: 近接分布関数 g(r) のビン幅（r の刻み幅）。単位は Å。
        - 備考: 小さいほど解像度は上がるが計算負荷が増える
        """
        toks = self.get_line(5).split()
        if not toks:
            raise ValueError("r spacing 行が空です")
        return float(toks[0])

    def set_r_spacing(
        self, dr: Union[int, float], *, auto_write: bool | None = None
    ) -> None:
        """5 行目 r spacing を更新。"""
        self.set_line(5, dr, auto_write=auto_write)

    def get_print_interval(self) -> int:
        """
        8 行目（step for printing）を取得する。

        【内容】
        - RMC_POT の計算進行中、標準出力やログファイルに
          エネルギー・受理率・コスト関数などの経過情報を
          どの間隔で出力するかを指定するステップ数。

        【マニュアル定義】
        - ラベル: “step for printing”
        - 意味: RMC の実行ループ中で何ステップごとに
                計算状況（χ²値、受理率、平均変位など）を表示するか。
        - 値の単位: ステップ数（整数）
        - 0 または負値: 無効（出力を行わない、もしくは既定間隔を使用）

        【例】
            5000  ! step for printing
            → 5000 ステップごとに進行情報を出力。
            100   ! step for printing
            → 100 ステップごとに頻繁に出力。
            0     ! step for printing
            → 出力を抑止または既定間隔に従う。

        Returns:
            int: ログ出力間隔（ステップ数単位）
        """
        tokens = self.get_line(8).split()
        if not tokens:
            raise ValueError("8 行目が空です。")
        try:
            return int(float(tokens[0]))
        except ValueError as exc:
            raise ValueError(f"8 行目に整数以外の値があります: {tokens!r}") from exc

    def set_print_interval(
        self,
        interval_step: int,
        *,
        auto_write: bool | None = None,
    ) -> None:
        """
        8 行目（step for printing）を更新する。

        【内容】
        - 計算経過を標準出力やログに記録する間隔を指定する。
          値は「ステップ数」で指定し、0 の場合は無効または既定値使用。

        【例】
            5000 → 5000 ステップごとに出力。
            100  → 100 ステップごとに出力。
            0    → 出力を抑止。

        Args:
            interval_step (int):
                出力間隔（ステップ数単位）
            auto_write (bool | None):
                True の場合は即時保存。None の場合はインスタンス既定値に従う。
        """
        if interval_step < 0:
            raise ValueError(
                f"interval_step は 0 以上を指定してください: {interval_step}"
            )
        self.set_line(8, str(int(interval_step)), auto_write=auto_write)

    def get_time_and_save(self) -> tuple[float, int]:
        """
        9 行目（time limit, step for saving）を取得する。

        【内容】
        - 9 行目は、計算の停止条件と出力間隔を設定する 2 つの値からなる。
          RMC_POT マニュアルでは「time limit, step for saving」と定義されている。

          (1) time limit:
              - 計算の最大実行時間（単位: 分）
              - 経過時間がこの値を超えると自動停止する。
              - 0 の場合は無効（時間制限なし）

          (2) step for saving:
              - RMC 計算の進行中、どの間隔で現在構造などをファイルに保存するか。
              - ステップ数単位で指定（例: 5000 → 5000 ステップごとに保存）
              - 0 の場合は無効（または既定間隔に従う）

        【例】
            0.2 0   ! time limit, step for saving
            → 最大 0.2 分（12 秒）で終了、保存間隔は無効
            60 500  ! time limit, step for saving
            → 60 分で停止、500 ステップごとに保存

        Returns:
            tuple[float, int]:
                (time_limit_min, save_interval_step)
        """
        toks = self.get_line(9).split()
        if len(toks) < 2:
            raise ValueError(f"9 行目の要素数が不足しています: {toks!r}")
        try:
            return float(toks[0]), int(float(toks[1]))
        except ValueError as exc:
            raise ValueError(f"9 行目に数値以外の値があります: {toks!r}") from exc

    def set_time_and_save(
        self,
        time_limit_min: float,
        save_interval_step: int,
        *,
        auto_write: bool | None = None,
    ) -> None:
        """
        9 行目（time limit, step for saving）を更新する。

        【内容】
        - time limit:
            計算の最大実行時間（分単位, float）。
            0 の場合は時間制限なし。
        - step for saving:
            結果ファイルを出力するステップ間隔（整数ステップ）。
            0 の場合は自動保存を無効化。

        【例】
            (60, 1000)
            → 最大 60 分で停止、1000 ステップごとに結果保存。
            (0, 0)
            → 両方無効化（時間制限も保存間隔も設定しない）。

        Args:
            time_limit_min (float): 最大実行時間（単位: 分）
            save_interval_step (int): 保存ステップ間隔
            auto_write (bool | None): True で即時保存。None は既定に従う。
        """
        if time_limit_min < 0:
            raise ValueError(
                f"time_limit_min は 0 以上を指定してください: {time_limit_min}"
            )
        if save_interval_step < 0:
            raise ValueError(
                f"save_interval_step は 0 以上を指定してください: {save_interval_step}"
            )

        values = [self._fmt_number(time_limit_min), str(int(save_interval_step))]
        self.set_line(9, values, auto_write=auto_write)

    def get_data_flags(self) -> tuple[int, int, int, int]:
        """
        10 行目（g(r), neutron, x-ray, EXAFS の出力フラグ）を取得する。

        【内容】
        - 各整数は、その物理量の計算・出力を行うかどうかを指定する。
          順序は常に以下で固定される（RMC_POT マニュアル II.E 節より）:
            (1) g(r) の計算フラグ
            (2) neutron S(Q) の計算フラグ
            (3) X-ray F(Q) の計算フラグ
            (4) EXAFS χ(k) の計算フラグ

        【仕様】
        - 0: 無効（そのデータ種を出力・比較しない）
        - 1: 有効（そのデータ種を出力・比較する）

        【例】
            0 0 1 0  ! g(r), neutron, x-ray, EXAFS
            → g(r)=0, neutron=0, x-ray=1, EXAFS=0
              → X線データのみ出力・比較対象とする設定。

        Returns:
            tuple[int, int, int, int]:
                (gr_flag, neutron_flag, xray_flag, exafs_flag)
        """
        tokens = self.get_line(10).split()
        if len(tokens) < 4:
            raise ValueError(f"10 行目の要素数が不足しています: {tokens!r}")
        try:
            return tuple(int(v) for v in tokens[:4])  # type: ignore[return-value]
        except ValueError as exc:
            raise ValueError(f"10 行目に整数以外の値があります: {tokens!r}") from exc

    def set_data_flags(
        self,
        flags: tuple[int, int, int, int],
        *,
        auto_write: bool | None = None,
    ) -> None:
        """
        10 行目（g(r), neutron, x-ray, EXAFS の出力フラグ）を更新する。

        【内容】
        - 10 行目は、4 つの整数値で各データ種の出力可否を指定する。
          順序は固定:
            (1) g(r)
            (2) neutron S(Q)
            (3) X-ray F(Q)
            (4) EXAFS χ(k)
        - 各値の意味:
            0: 無効（出力・比較を行わない）
            1: 有効（出力・比較を行う）

        【例】
            (0, 0, 1, 0)
            → g(r)=off, neutron=off, X-ray=on, EXAFS=off
              → X線 F(Q) のみを比較対象に設定。

        Args:
            flags (tuple[int, int, int, int]):
                (gr_flag, neutron_flag, xray_flag, exafs_flag)
            auto_write (bool | None):
                True なら即時保存。None の場合はインスタンス既定に従う。
        """
        if len(flags) != 4:
            raise ValueError(
                f"flags は 4 要素 (g(r), neutron, x-ray, EXAFS) が必要です: {flags!r}"
            )
        if not all(isinstance(v, int) and v in (0, 1) for v in flags):
            raise ValueError(f"flags には 0 または 1 のみ指定可能です: {flags!r}")

        self.set_line(10, [str(v) for v in flags], auto_write=auto_write)

    def get_exp_filename(self) -> str:
        """
        11 行目（実験データファイル名）を返す（旧来固定フォーマット）。

        【.dat 側の決まり（旧来固定）】
        - 10 行目は 4 つの整数をこの順で持つ:
            g(r), neutron S(Q), X-ray F(Q), EXAFS χ(k)
          これらは各データ種の「ブロック数」を表す（0 ならブロック無し）。
        - 11 行目以降には、上記順序で「有効なデータ種のブロック」が連続。
          各ブロックの先頭行が「実験データファイル名」、直後の行が「点範囲（開始・終了の2整数）」。
        - 本メソッドは「11 行目のファイル名」をそのまま返す（例: 10 行目が `0 0 1 0` なら
          11 行目は X-ray F(Q) ブロックのファイル名）。

        【実験データファイルの中身（旧来固定フォーマット, あいまいさ無し）】
        - 1 行目: データ点数 N（整数）
        - 2 行目: タイトル（任意文字列。数値としては読まれない）
        - 3 行目以降: 各データ点の行。種別ごとに列は厳密に以下となる。
          - g(r)        : r, g(r)                                         （2 列）
          - neutron S(Q): Q, S(Q)                                         （2 列）
          - X-ray F(Q)  : Q, F(Q), c_αβ を RMC 順で M 本                  （2+M 列）
                           M = ntypes*(ntypes+1)/2
                           RMC 順 = 11, 12, 13, …, 22, 23, …, 33
                           例: 2 元系 → 5 列（Q, F(Q), c11, c12, c22）
                               3 元系 → 8 列（Q, F(Q), c11, c12, c13, c22, c23, c33）
          - EXAFS χ(k)  : k, χ(k)                                         （2 列）

        例（あなたの貼付データ）:
        - 10 行目 `0 0 1 0` → X-ray F(Q) にフィット。
          5 列ファイルは 2 元系（Q, F(Q), c11, c12, c22）、
          8 列ファイルは 3 元系（Q, F(Q), c11, c12, c13, c22, c23, c33）。
        """
        return self.get_line(11).split()[0]

    def set_exp_filename(
        self,
        path: Union[str, Path],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        11 行目（実験データファイル名）を更新する（旧来固定フォーマット）。

        【.dat 側の決まり（旧来固定）】
        - 10 行目の順序は常に:
            g(r), neutron S(Q), X-ray F(Q), EXAFS χ(k)
        - 11 行目は、上記で有効な最初のブロックが X-ray の場合には
          その「ファイル名行」となる（例: `0 0 1 0`）。
          本メソッドは **11 行目のみ** を対象として文字列を書き換える。

        【実験データファイルの中身（確認用の定義）】
        - 1 行目: N（整数）
        - 2 行目: タイトル（任意。数値としては読まれない）
        - 3 行目以降（厳密定義）:
          - g(r)        : r, g(r)                                         （2 列）
          - neutron S(Q): Q, S(Q)                                         （2 列）
          - X-ray F(Q)  : Q, F(Q), c_αβ × M（RMC 順, M = ntypes*(ntypes+1)/2）
          - EXAFS χ(k)  : k, χ(k)                                         （2 列）

        Args:
            path: 実験データファイルへのパス（相対・絶対いずれも可）。
            auto_write: True の場合は即時保存。None の場合はインスタンス既定に従う。
        """
        self.set_line(11, str(Path(path)), auto_write=auto_write)
