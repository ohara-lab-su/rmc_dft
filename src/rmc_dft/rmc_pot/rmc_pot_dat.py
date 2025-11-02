#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com

RmcPotDat: RMC_POT の .dat 入力ファイル編集クラス

- 本クラスは「タグ名ではなく行番号に意味がある」RMC_POT の .dat 形式を前提とします。
- 各行は「値 [任意空白] ! コメント」の構造で、コメントは保持したまま値のみ更新します。
- 代表的に編集頻度の高い行:
    2行目: number density (float)
    3行目: cut offs (float×3)
    4行目: maximum moves (float×2)
    5行目: r spacing (float)
- 真偽値は .true. / .false. に正規化して出力します。
- 任意行の直接取得/更新用に get_line()/set_line() も提供します。
"""


from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union


Number = Union[int, float]
Grid2 = Tuple[Number, Number]
Grid3 = Tuple[Number, Number, Number]


def _to_bool_token(v: Union[bool, str]) -> str:
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


def _fmt_number(x: Number) -> str:
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


def _fmt_sequence(seq: Sequence[Number]) -> str:
    """数値列を空白区切りで整形。"""
    return " ".join(_fmt_number(v) for v in seq)


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
        dat = RmcPotDat("/abs/path/to/aaa.dat")
        rho = dat.get_density()
        dat.set_cutoffs((2.5, 2.2, 2.0))
        dat.write()  # 上書き保存

    注意:
        - 行番号は 1 始まり。内部処理では 0 始まりのリストに対応付けます。
        - 既存コメントは保持します。コメント無しの行へ値を設定した場合はコメント無しで書き出します。
        - 指定の .dat 形式（添付例）を前提に実装しています。
    """

    # 添付例に基づく主要フィールド行番号（1 始まり）
    LINE_DENSITY: int = 2
    LINE_CUTOFFS: int = 3
    LINE_MAX_MOVES: int = 4
    LINE_R_SPACING: int = 5

    def __init__(self, dat_path: str):
        """
        Args:
            dat_path: 編集対象 .dat の絶対パス（推奨）
        """
        self.dat_path: str = str(Path(dat_path))
        self._lines: List[_Line] = []
        self._load()

    # --------------------
    # 基本 I/O
    # --------------------
    def _load(self) -> None:
        """ファイルを読み込んで内部行リストを構築。"""
        p = Path(self.dat_path)
        if not p.exists():
            raise FileNotFoundError(f".dat ファイルが見つかりません: {self.dat_path}")

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

    def write(self, out_path: Optional[str] = None) -> None:
        """
        現在の内容を書き出す。

        Args:
            out_path: 出力先。未指定なら self.dat_path に上書き保存。
        """
        target = self.dat_path if out_path is None else str(Path(out_path))
        with open(target, "w", encoding="utf-8") as f:
            for ln in self._lines:
                f.write(ln.render())

    # --------------------
    # 任意行の get / set
    # --------------------
    def get_line(self, line_no_1based: int) -> str:
        """
        任意行の値部分を返す（コメントは含めない）。

        Args:
            line_no_1based: 1 始まりの行番号

        Returns:
            値（文字列）
        """
        idx = self._index(line_no_1based)
        return self._lines[idx].value

    def set_line(
        self, line_no_1based: int, value: Union[str, Number, Sequence[Number], bool]
    ) -> None:
        """
        任意行の値部分を更新（コメントは保持）。

        Args:
            line_no_1based: 1 始まりの行番号
            value: 置換値（数値/数値列/真偽/文字列）

        Raises:
            IndexError: 行番号が範囲外
            ValueError: 真偽解釈など不正値
        """
        idx = self._index(line_no_1based)
        self._lines[idx].value = self._coerce_value(value)

    # --------------------
    # 代表フィールド: density / cutoffs / max_moves / r_spacing
    # --------------------
    # density (2 行目)
    def get_density(self) -> float:
        """2 行目 density を float で返す。"""
        return float(self.get_line(self.LINE_DENSITY).split()[0])

    def set_density(self, rho: Number) -> None:
        """2 行目 density を更新。"""
        self.set_line(self.LINE_DENSITY, rho)

    # cut offs (3 行目; 3 要素)
    def get_cutoffs(self) -> Grid3:
        """3 行目 cut offs を (c1, c2, c3) で返す。"""
        toks = self.get_line(self.LINE_CUTOFFS).split()
        if len(toks) < 3:
            raise ValueError(f"cut offs 行の要素数が不足: {toks!r}")
        return float(toks[0]), float(toks[1]), float(toks[2])

    def set_cutoffs(self, values: Union[Grid3, Sequence[Number]]) -> None:
        """3 行目 cut offs を更新。"""
        seq = list(values)
        if len(seq) != 3:
            raise ValueError(f"cut offs は 3 要素が必要です: {values!r}")
        self.set_line(self.LINE_CUTOFFS, seq)

    # maximum moves (4 行目; 2 要素)
    def get_max_moves(self) -> Grid2:
        """4 行目 maximum moves を (m1, m2) で返す。"""
        toks = self.get_line(self.LINE_MAX_MOVES).split()
        if len(toks) < 2:
            raise ValueError(f"maximum moves 行の要素数が不足: {toks!r}")
        return float(toks[0]), float(toks[1])

    def set_max_moves(self, values: Union[Grid2, Sequence[Number]]) -> None:
        """4 行目 maximum moves を更新。"""
        seq = list(values)
        if len(seq) != 2:
            raise ValueError(f"maximum moves は 2 要素が必要です: {values!r}")
        self.set_line(self.LINE_MAX_MOVES, seq)

    # r spacing (5 行目; 1 要素)
    def get_r_spacing(self) -> float:
        """5 行目 r spacing を float で返す。"""
        toks = self.get_line(self.LINE_R_SPACING).split()
        if not toks:
            raise ValueError("r spacing 行が空です")
        return float(toks[0])

    def set_r_spacing(self, dr: Number) -> None:
        """5 行目 r spacing を更新。"""
        self.set_line(self.LINE_R_SPACING, dr)

    # --------------------
    # ヘルパ
    # --------------------
    def _index(self, line_no_1based: int) -> int:
        """1 始まり行番号 -> 0 始まりインデックスに変換し、範囲を検証。"""
        idx = line_no_1based - 1
        if idx < 0 or idx >= len(self._lines):
            raise IndexError(
                f"行番号が範囲外です: {line_no_1based} (全 {len(self._lines)} 行)"
            )
        return idx

    @staticmethod
    def _coerce_value(value: Union[str, Number, Sequence[Number], bool]) -> str:
        """
        入力値を .dat へ書き込むための文字列に正規化。

        ルール:
          - str: そのまま（前後空白は適宜呼び出し側で制御）
          - bool: .true. / .false.
          - Sequence[Number]: 空白区切りで整形
          - Number: 数値フォーマットで整形
        """
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, bool):
            return _to_bool_token(value)
        if isinstance(value, (int, float)):
            return _fmt_number(value)
        # Sequence[Number] の判定（str はすでに除外）
        try:
            seq = list(value)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError(f"未対応の型です: {type(value)!r}") from exc
        return _fmt_sequence(seq)
