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
from pathlib import Path
from typing import List, Sequence, Union, Tuple

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
