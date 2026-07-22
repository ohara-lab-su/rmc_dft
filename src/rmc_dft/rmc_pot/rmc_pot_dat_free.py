#!/usr/bin/env python3
"""RMC_POT 自由形式 ``*.dat`` の読み書き機能。

``#002`` または ``#003`` で始まる自由形式ファイルを、セクションと
キーワードを単位として読み書きする。物理行番号には依存しない。
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from rmc_dft.config import Config
from x_logger import XLogger

FREE_DAT_TEMPLATE: str = """{version}

[ GENERAL ]
TITLE = System
NDENS = 0.08
CUT-OFF = 2.0
MAX-MOVES = 0.1
R-SPACING = 0.025
PRINT-STEP = 1000
RUN-TIME = 1.0 0
FNC-TYPE = NONE

[ EXP ]
TYPE = XRD
"""


class RmcPotDatFree:
    """RMC_POT 自由形式 ``*.dat`` をセクション／キーワード単位で扱う。

    # 実行バイナリが _ADVANCED_GEOM_CONST を有効に置く必要がある
    # make AGC=0
    # が必要となる

    Attributes:
        直接公開する属性はない。設定値は既存の getter/setter または
        自由形式固有の ``get()``, ``set()``, ``add()`` を通して操作する。

    Notes:
        ファイル上の実体である ``[ SECTION ]`` と ``KEY = VALUE`` を
        そのまま内部表現として保持する。
    """

    _FNC_TO_FREE = {
        0: "NONE",
        1: "NORMAL",
        2: "ADJUST",
        3: "MOVE-IN",
    }
    _FREE_TO_FNC = {value: key for key, value in _FNC_TO_FREE.items()}

    def __init__(
        self,
        config: Optional[Config] = None,
        logger: Optional[XLogger] = None,
        *,
        cfg_name: Optional[str] = None,
        auto_write: bool = True,
        version: str = "#003",
    ) -> None:
        """自由形式 RMC_POT 入力ファイル編集クラスを初期化する。

        Args:
            config: RMC_DFT 全体設定。省略時は新しい ``Config`` を使用する。
            logger: ログ出力に使用する ``XLogger``。省略時は新規作成する。
            cfg_name: 読み書きする ``*.dat`` の拡張子を除いた名前。
                省略時は ``config.cfg_name`` を使用する。
            auto_write: setter 実行後に自動保存する既定動作。
            version: 自由形式ファイル先頭へ書く形式識別子。
                ``#002`` または ``#003`` を想定する。

        Notes:
            自由形式のセクション名とキーワードを直接読み書きする。

            ``<cfg_name>.dat`` が存在する場合は、その自由形式ファイルを読み込み、
            先頭行の ``#002`` または ``#003`` を以後の出力形式として維持する。
            ファイルが存在しない場合だけ、``version`` で指定した形式の
            デフォルト ``*.dat`` を新規作成する。

            ``auto_write=True`` の場合、各 setter は更新直後に ``*.dat`` へ
            反映する。複数設定をまとめて反映したい場合だけ、
            インスタンスまたは各メソッドで ``auto_write=False`` を指定する。
        """
        self._logger = logger or XLogger()
        self._config = config or Config()
        self._cfg_name = cfg_name or self._config.cfg_name
        self._auto_write = auto_write
        self._version = version
        self._sections: List[Tuple[str, Dict[str, List[str]]]] = []

        path = Path(f"{self._cfg_name}.dat")
        if path.exists():
            self.load()
        else:
            self.create_dat_file(str(self._cfg_name))
            self.load()

        changed = False
        if self._config.rmc_comment is not None:
            self.set_comment(self._config.rmc_comment, auto_write=False)
            changed = True
        if self._config.number_density_A3 is not None:
            self.set_density(self._config.number_density_A3, auto_write=False)
            changed = True
        if self._config.rmc_cutoffs is not None:
            self.set_cutoffs(self._config.rmc_cutoffs, auto_write=False)
            changed = True
        if self._config.rmc_max_moves is not None:
            self.set_maximum_moves(self._config.rmc_max_moves, auto_write=False)
            changed = True
        if self._config.rmc_r_spacing is not None:
            self.set_r_spacing(self._config.rmc_r_spacing, auto_write=False)
            changed = True
        if self._config.rmc_moveout_option is not None:
            self.set_moveout_option(self._config.rmc_moveout_option, auto_write=False)
            changed = True
        if self._config.rmc_time_and_save is not None:
            self.set_time_and_save(
                self._config.rmc_time_and_save[0],
                self._config.rmc_time_and_save[1],
                auto_write=False,
            )
            changed = True
        if self._config.rmc_data_flags is not None:
            self.set_data_flags(self._config.rmc_data_flags, auto_write=False)
            changed = True
        if self._config.rmc_exp_filename is not None:
            self.set_exp_filename(self._config.rmc_exp_filename, auto_write=False)
            changed = True
        if self._config.rmc_exp_range is not None:
            self.set_exp_range(
                self._config.rmc_exp_range[0],
                self._config.rmc_exp_range[1],
                auto_write=False,
            )
            changed = True
        if self._config.rmc_sigma_factor is not None:
            self.set_sigma_factor(self._config.rmc_sigma_factor, auto_write=False)
            changed = True
        if self._config.rmc_num_atoms_per_move is not None:
            self.set_num_atoms_per_move(
                self._config.rmc_num_atoms_per_move,
                auto_write=False,
            )
            changed = True
        if changed and self._auto_write:
            self.write()

    def create_dat_file(self, basename: str) -> bool:
        """自由形式の初期 ``*.dat`` ファイルを作成する。

        Args:
            basename: 出力ファイル名から ``.dat`` を除いた部分。

        Returns:
            新規作成した場合は ``True``。同名ファイルが既に存在する場合は
            上書きせず ``False`` を返す。

        Notes:
            初期値は ``[ GENERAL ]`` セクションへ自由形式のキーとして設定する。
            物理的な行配置には依存しない。

            初期状態では ``FNC-TYPE = NONE`` とし、``[ BPOT ]`` を作成しない。
            したがって ``set_fnc_switch()`` を呼ばなければ、FNC も topology も
           使用しない自由形式 ``*.dat`` になる。
        """
        path = Path(f"{basename}.dat")
        if path.exists():
            self._logger.error(f'[rmc_pot_dat_free] "{path}" はすでに存在します')
            return False
        default_input = FREE_DAT_TEMPLATE.format(version=self._version)
        path.write_text(default_input, encoding="utf-8")
        self._logger.info(f"[rmc_pot_dat_free] default dat file を作成しました: {path}")
        return True

    @staticmethod
    def _to_bool_token(v: Union[bool, str]) -> str:
        """真偽入力をRMC_POT の論理トークンへ変換する。

        Args:
            v: ``bool`` または真偽を表す文字列。

        Returns:
            ``".true."`` または ``".false."``。

        Raises:
            ValueError: 入力を真偽値として解釈できない場合。
        """
        if isinstance(v, bool):
            if v:
                return ".true."
            return ".false."
        value = str(v).strip().lower()
        if value in {".true.", "true", "t", "1", "yes", "y"}:
            return ".true."
        if value in {".false.", "false", "f", "0", "no", "n"}:
            return ".false."
        raise ValueError(f"真偽として解釈できません: {v!r}")

    @staticmethod
    def _fmt_number(x: Union[int, float]) -> str:
        """数値を RMC_POT 入力用の文字列へ整形する。

        Args:
            x: 整形する整数または浮動小数点数。

        Returns:
            不要な末尾ゼロを抑えた数値文字列。

        Notes:
            整数値として表現できる浮動小数点数は整数表記へ変換する。
            それ以外は有効桁数を保ちながら過度な指数表記を避ける。
        """
        if isinstance(x, int) or (isinstance(x, float) and x.is_integer()):
            return str(int(x))
        return f"{float(x):.12g}"

    @classmethod
    def _fmt_sequence(cls, seq: Sequence[Union[int, float]]) -> str:
        """数値列を RMC_POT 入力用の空白区切り文字列へ整形する。

        Args:
            seq: 整形する数値列。

        Returns:
            各要素を ``_fmt_number()`` で整形した空白区切り文字列。
        """
        return " ".join(cls._fmt_number(value) for value in seq)

    def load(self) -> bool:
        """現在の ``cfg_name`` に対応する自由形式ファイルを読み込む。

        Returns:
            ファイルを読み込めた場合は ``True``。対象ファイルが存在しない場合は
            ``False`` を返す。

        Raises:
            ValueError: ファイルが空、形式識別子が不正、またはセクション外に
                キー値が記述されている場合。

        Notes:
            ``[ SECTION ]`` と ``KEY = VALUE`` を解析し、同一キーの複数出現を
            値リストとして保持する。継続行は直前のキー値へ連結する。
        """
        path = Path(f"{self._cfg_name}.dat")
        if not path.exists():
            self._logger.info(
                f"[rmc_pot_dat_free] .dat ファイルが見つかりません: {path}"
            )
            return False
        raw_lines = path.read_text(encoding="utf-8").splitlines()
        if not raw_lines:
            raise ValueError(f"空のファイルです: {path}")
        version = raw_lines[0].strip()
        if version not in {"#002", "#003"}:
            raise ValueError(f"自由形式 *.dat ではありません: {path}")
        self._version = version
        self._sections = []
        current = None
        pending_key = None
        for raw in raw_lines[1:]:
            line = raw.split("!", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                name = line[1:-1].strip().upper()
                current = {}
                self._sections.append((name, current))
                pending_key = None
                continue
            if current is None:
                raise ValueError(f"セクション外に値があります: {line}")
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()
                current.setdefault(key, []).append(value)
                pending_key = key
            elif pending_key is not None:
                values = current[pending_key]
                values[-1] = (values[-1] + " " + line).strip()
            else:
                raise ValueError(f"KEY = VALUE 形式ではありません: {line}")
        if not self._find_sections("GENERAL"):
            self._sections.insert(0, ("GENERAL", {}))
        return True

    def write(self, out_name: Optional[str] = None) -> None:
        """保持している自由形式データを ``*.dat`` へ書き出す。

        Args:
            out_name: 出力ファイル名から ``.dat`` を除いた部分。
                省略時は現在の ``cfg_name`` を使用する。

        Notes:
            セクションの並び、キーの並び、同一キーの値順を内部表現の順序どおり
            出力する。
        """
        if out_name is None:
            base = self._cfg_name
        else:
            base = out_name
        self.validate_mode_configuration(
            check_input_files=False,
        )
        self._write_path(Path(f"{base}.dat"))

    def _write_path(self, path: Path) -> None:
        """指定パスへ自由形式データを書き出す。

        Args:
            path: 出力先の ``Path``。

        Notes:
            先頭に形式識別子を出力し、その後へ各セクションと
            ``KEY = VALUE`` を順番に出力する。
        """
        output = [self._version, ""]
        for name, values in self._sections:
            output.append(f"[ {name} ]")
            for key, entries in values.items():
                for value in entries:
                    output.append(f"{key} = {value}")
            output.append("")
        path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
        self._logger.info(f"[rmc_pot_dat_free] == write({path})")

    def _find_sections(self, name: str) -> List[Dict[str, List[str]]]:
        """指定名と一致する全セクションを取得する。

        Args:
            name: 大文字小文字を区別しないセクション名。

        Returns:
            出現順を維持したセクション辞書のリスト。
        """
        upper = name.upper()
        found: List[Dict[str, List[str]]] = []
        for section_name, values in self._sections:
            if section_name == upper:
                found.append(values)
        return found

    def _first_section(self, name: str, create: bool = False) -> Dict[str, List[str]]:
        """指定名の最初のセクションを取得する。

        Args:
            name: 対象セクション名。
            create: 存在しない場合に新規セクションを作成するかどうか。

        Returns:
            最初のセクション辞書。未存在かつ ``create=False`` の場合は空辞書。
        """
        found = self._find_sections(name)
        if found:
            return found[0]
        if not create:
            return {}
        values: Dict[str, List[str]] = {}
        self._sections.append((name.upper(), values))
        return values

    def _first_value(self, section: str, key: str, default: str = "") -> str:
        """指定セクション・キーの最初の値を取得する。

        Args:
            section: セクション名。
            key: キー名。
            default: 値が存在しない場合に返す文字列。

        Returns:
            最初に登録された値、または ``default``。
        """
        values = self._first_section(section).get(key.upper(), [])
        if values:
            return values[0]
        return default

    def _set_value(self, section: str, key: str, value: Any) -> None:
        """指定セクションのキーを単一値で設定する。

        Args:
            section: セクション名。
            key: キー名。
            value: 保存する値。

        Notes:
            対象セクションが存在しない場合は作成し、同一キーの既存値は
            単一要素の値リストで置き換える。
        """
        target = self._first_section(section, create=True)
        target[key.upper()] = [str(value)]

    def _first_exp(self, create: bool = False) -> Dict[str, List[str]]:
        """最初の ``[ EXP ]`` セクションを取得する。

        Args:
            create: 存在しない場合に新規作成するかどうか。

        Returns:
            最初の実験データセクション。未存在かつ ``create=False`` の場合は空辞書。
        """
        sections = self._find_sections("EXP")
        if sections:
            return sections[0]
        if not create:
            return {}
        values: Dict[str, List[str]] = {}
        self._sections.append(("EXP", values))
        return values

    def _exp_type_counts(self) -> Tuple[int, int, int, int]:
        """実験データ種別ごとの ``[ EXP ]`` セクション数を数える。

        Returns:
            ``(GR, ND, XRD, EXAFS)`` の順に格納した件数。
        """
        counts = {"GR": 0, "ND": 0, "XRD": 0, "EXAFS": 0}
        for exp in self._find_sections("EXP"):
            exp_type = exp.get("TYPE", [""])[0].upper()
            if exp_type in counts:
                counts[exp_type] += 1
        return counts["GR"], counts["ND"], counts["XRD"], counts["EXAFS"]

    @staticmethod
    def _bool_int(value: Any) -> str:
        """真偽入力を自由形式で使用する ``0`` または ``1`` へ変換する。

        Args:
            value: 真偽値として解釈する値。

        Returns:
            真と解釈した場合は ``"1"``、それ以外は ``"0"``。
        """
        token = str(value).strip().lower()
        if token in {"1", "true", ".true.", "yes", "y", "t"}:
            return "1"
        return "0"

    @staticmethod
    def _bool_line(value: Any) -> str:
        """自由形式の真偽値を論理トークンへ変換する。

        Args:
            value: ``0``、``1``、または真偽を表す文字列。

        Returns:
            ``".true."`` または ``".false."``。
        """
        bool_value = RmcPotDatFree._bool_int(value)
        if bool_value == "1":
            return ".true."
        return ".false."

    def _fnc_compat_line(self) -> str:
        """自由形式の FNC 状態を数値表現へ変換する。

        Returns:
            FNC 0～4 と option を表す文字列。
        """
        if self._find_sections("BPOT"):
            options = self.get_fnc_options()
            tokens = ["4"]
            tokens.extend(options)
            return " ".join(tokens)

        fnc_value = self._first_value(
            "GENERAL",
            "FNC-TYPE",
            "NONE",
        )
        return self._fnc_free_to_fixed(fnc_value)

    def _fnc_free_to_fixed(self, value: str) -> str:
        """自由形式の ``FNC-TYPE`` を数値表現へ変換する。

        Args:
            value: ``NONE``、``NORMAL``、``ADJUST``、``MOVE-IN``、
                ``FLEXIBLE`` のいずれかと追加オプション。

        Returns:
            FNC 番号と追加オプションを空白で連結した文字列。
        """
        tokens = value.split()
        if tokens:
            mode = self._FREE_TO_FNC.get(tokens[0].upper(), 0)
        else:
            mode = 0
        return " ".join([str(mode)] + tokens[1:])

    def set(self, section: str, key: str, value: Any, index: int = 0) -> None:
        """自由形式の指定キーを単一値で設定する。

        Args:
            section: セクション名。
            key: キー名。
            value: 設定する値。
            index: 同名セクションが複数ある場合の 0 始まり位置。

        Notes:
            指定位置までセクションが存在しない場合は必要数を追加する。
            既存の同一キー値は置き換える。
        """
        sections = self._find_sections(section)
        while len(sections) <= index:
            values: Dict[str, List[str]] = {}
            self._sections.append((section.upper(), values))
            sections = self._find_sections(section)
        sections[index][key.upper()] = [self._coerce_value(value)]

    def add(self, section: str, key: str, value: Any, index: int = 0) -> None:
        """自由形式の指定キーへ値を追加する。

        Args:
            section: セクション名。
            key: キー名。
            value: 追加する値。
            index: 同名セクションが複数ある場合の 0 始まり位置。

        Notes:
            既存値は保持し、同じキーの値リスト末尾へ追加する。
        """
        sections = self._find_sections(section)
        while len(sections) <= index:
            values: Dict[str, List[str]] = {}
            self._sections.append((section.upper(), values))
            sections = self._find_sections(section)
        sections[index].setdefault(key.upper(), []).append(self._coerce_value(value))

    def get(
        self, section: str, key: str, index: int = 0, default: Optional[str] = None
    ) -> Optional[str]:
        """自由形式の指定キーから最初の値を取得する。

        Args:
            section: セクション名。
            key: キー名。
            index: 同名セクションが複数ある場合の 0 始まり位置。
            default: セクションまたはキーが存在しない場合の戻り値。

        Returns:
            最初の値、または ``default``。
        """
        sections = self._find_sections(section)
        if index >= len(sections):
            return default
        values = sections[index].get(key.upper(), [])
        if values:
            return values[0]
        return default

    def get_all(self, section: str, key: str, index: int = 0) -> List[str]:
        """自由形式の指定キーに登録された全値を取得する。

        Args:
            section: セクション名。
            key: キー名。
            index: 同名セクションが複数ある場合の 0 始まり位置。

        Returns:
            登録順を維持した値リスト。対象が存在しない場合は空リスト。
        """
        sections = self._find_sections(section)
        if index >= len(sections):
            return []
        return list(sections[index].get(key.upper(), []))

    # -------------------------------
    # 個別メソッド
    # -------------------------------

    def initialize_sections(
        self,
        section: str,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """指定名のセクションをすべて削除して未設定状態へ戻す。

        Args:
            section: 初期化するセクション名。
            auto_write: 初期化後に ``*.dat`` を保存するかどうか。
                ``None`` の場合はインスタンスの ``auto_write`` 設定を使う。

        Notes:
            ``[ SNC ]``、``[ EXP ]``、``[ COS ]`` など、同じ名前の
            セクションを複数記述できる項目を作り直す前に使用する。

            空のセクションは作成しない。既存の同名セクションをすべて削除し、
            次の高水準 setter または add メソッドが完全なセクションを
            一つずつ追加できる状態にする。
        """
        section_name = str(section).strip().upper()
        if not section_name:
            raise ValueError("section は空にできません。")

        retained_sections: List[Tuple[str, Dict[str, List[str]]]] = []

        for name, values in self._sections:
            if name != section_name:
                retained_sections.append((name, values))

        self._sections = retained_sections

        self._logger.info(
            "[rmc_pot_dat_free] initialize_sections: " f"section={section_name}"
        )

        if self._resolve_auto_write(auto_write):
            self.write()

    def initialize_qn_constraints(
        self,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """すべての Qn/SNC 制約を削除して再設定前の状態へ戻す。

        Args:
            auto_write: 初期化後に ``*.dat`` を保存するかどうか。
                ``None`` の場合はインスタンスの ``auto_write`` 設定を使う。

        Notes:
            Q4、Q3、Q2 などを一式として作り直す場合に最初に呼び出す。
            既存の ``[ SNC ]`` を残したまま追加し続けることを防ぐ。
        """
        self.initialize_sections(
            "SNC",
            auto_write=auto_write,
        )

    def add_section(self, section: str) -> int:
        """空の自由形式セクションを末尾へ追加する。

        Args:
            section: 追加するセクション名。

        Returns:
            追加した同名セクションの 0 始まり位置。

        Notes:
            内部構築用の低水準メソッドであり、自動書き込みは行わない。
            必須キーを持たない空セクションを一時的に作るためである。
            通常は ``add_qn_constraint()`` などの高水準メソッドを使用する。
        """
        values: Dict[str, List[str]] = {}
        self._sections.append((section.upper(), values))
        return len(self._find_sections(section)) - 1

    def remove_section(self, section: str, index: int = 0) -> None:
        """指定位置の自由形式セクションを削除する。

        Args:
            section: セクション名。
            index: 同名セクションが複数ある場合の 0 始まり位置。

        Raises:
            IndexError: 指定したセクション位置が存在しない場合。
        """
        count = -1
        for position, (name, _) in enumerate(self._sections):
            if name == section.upper():
                count += 1
                if count == index:
                    del self._sections[position]
                    return
        raise IndexError(f"{section} セクション index={index} は存在しません。")

    def remove(self, section: str, key: str, index: int = 0) -> None:
        """指定セクションからキーと全値を削除する。

        Args:
            section: セクション名。
            key: 削除するキー名。
            index: 同名セクションが複数ある場合の 0 始まり位置。

        Notes:
            対象セクションまたはキーが存在しない場合は何も変更しない。
        """
        sections = self._find_sections(section)
        if index >= len(sections):
            return
        sections[index].pop(key.upper(), None)

    def section_count(self, section: str) -> int:
        """指定名の自由形式セクション数を返す。

        Args:
            section: セクション名。

        Returns:
            同名セクションの件数。
        """
        return len(self._find_sections(section))

    def set_cfg_name(self, cfg_name: str) -> None:
        """読み書き対象の構成名を変更する。

        Args:
            cfg_name: ``.dat`` を除いた新しい構成名。

        Notes:
            クラス内部の名前と ``Config.cfg_name`` を同時に更新する。
        """
        self._cfg_name = cfg_name
        self._config.cfg_name = cfg_name

    def set_element_info(
        self,
        element_info: Sequence[str],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """原子タイプ順の元素記号を設定する。"""
        symbols = [str(element).strip() for element in element_info]

        if not symbols:
            raise ValueError("element_info は1件以上必要です。")

        if any(not symbol for symbol in symbols):
            raise ValueError("element_info に空の元素記号は指定できません。")

        self._set_value(
            "GENERAL",
            "CHEMICAL-SYMBOLS",
            " ".join(symbols),
        )

        if self._resolve_auto_write(auto_write):
            self.write()

    @staticmethod
    def _to_bool_token(v: Union[bool, str]) -> str:
        """
        真偽入力を .true. / .false. に正規化する。

        Args:
            v: bool もしくは真偽を表す文字列（大文字小文字は不問）

        Returns:
            ".true." もしくは ".false."
        """
        if isinstance(v, bool):
            if v:
                return ".true."
            return ".false."
        s = str(v).strip().lower()
        if s in (".true.", "true", "t", "1", "yes", "y"):
            return ".true."
        if s in (".false.", "false", "f", "0", "no", "n"):
            return ".false."
        # 不明値はそのまま返さず、明示的に例外
        raise ValueError(f"真偽として解釈できません: {v!r}")

    @staticmethod
    def _fmt_number(
        x: Union[int, float],
    ) -> str:
        """
        数値を .dat に過度な科学表記を使わず整形

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
    def _fmt_sequence(
        cls,
        seq: Sequence[Union[int, float]],
    ) -> str:
        """数値列を空白区切りで整形。"""
        return " ".join(cls._fmt_number(v) for v in seq)

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

    def get_comment(self) -> str:
        """``[ GENERAL ]`` の ``TITLE`` を返す。"""
        return self._first_value("GENERAL", "TITLE", "")

    def set_comment(
        self,
        comment: str,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """``[ GENERAL ]`` の ``TITLE`` を設定する。"""
        self._logger.info(f"[rmc_pot_dat_free] set_comment = {comment}")
        self._config.rmc_comment = comment
        self._set_value("GENERAL", "TITLE", comment)
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_density(self) -> Union[float, bool]:
        """``[ GENERAL ]`` の ``NDENS`` を返す。"""
        value = self._first_value("GENERAL", "NDENS", "")
        if not value:
            self._logger.error("[rmc_pot_dat_free] NDENS が未設定です")
            return False
        try:
            return float(value)
        except ValueError:
            self._logger.error(
                f"[rmc_pot_dat_free] NDENS が数値ではありません: {value}"
            )
            return False

    def set_density(
        self,
        rho: Union[int, float],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """``[ GENERAL ]`` の ``NDENS`` を設定する。"""
        self._logger.info(f"[rmc_pot_dat_free] set_density = {rho}")
        self._config.number_density_A3 = float(rho)
        self._set_value("GENERAL", "NDENS", self._fmt_number(rho))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_cutoffs(self) -> List[Union[int, float, str]]:
        """``[ GENERAL ]`` の ``CUT-OFF`` を RMC 順で返す。

        ``CUT-OFF`` は数値列のほか、自由形式で認められる ``MIN`` または
        ``MIN-ALL`` を取れる。
        """
        value = self._first_value("GENERAL", "CUT-OFF", "")
        if not value:
            return []
        values: List[Union[int, float, str]] = []
        for token in value.split():
            try:
                number = float(token)
            except ValueError:
                values.append(token)
                continue
            if number.is_integer():
                values.append(int(number))
            else:
                values.append(number)
        return values

    def set_cutoffs(
        self,
        values: Union[str, Sequence[Union[int, float]]],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """``[ GENERAL ]`` の ``CUT-OFF`` を設定する。

        数値列は RMC 順で指定する。自由形式固有の自動決定を使う場合は
        ``"MIN"`` または ``"MIN-ALL"`` を指定する。
        """
        if isinstance(values, str):
            value_text = values.strip().upper()
        else:
            value_text = self._fmt_sequence(values)
            self._config.rmc_cutoffs = list(values)
        self._logger.info(f"[rmc_pot_dat_free] set_cutoffs = {value_text}")
        self._set_value("GENERAL", "CUT-OFF", value_text)
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_max_moves(self) -> List[float]:
        """``[ GENERAL ]`` の ``MAX-MOVES`` を返す。"""
        value = self._first_value("GENERAL", "MAX-MOVES", "")
        if not value:
            return []
        try:
            return [float(token) for token in value.split()]
        except ValueError:
            self._logger.error(f"[rmc_pot_dat_free] MAX-MOVES が不正です: {value}")
            return []

    def set_maximum_moves(
        self,
        values: Sequence[Union[int, float]],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """``[ GENERAL ]`` の ``MAX-MOVES`` を設定する。"""
        sequence = list(values)
        self._config.rmc_max_moves = sequence
        self._set_value("GENERAL", "MAX-MOVES", self._fmt_sequence(sequence))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_r_spacing(self) -> float:
        """``[ GENERAL ]`` の ``R-SPACING`` を返す。"""
        value = self._first_value("GENERAL", "R-SPACING", "0.0")
        return float(value)

    def set_r_spacing(
        self, dr: Union[int, float], *, auto_write: Optional[bool] = True
    ) -> None:
        """``[ GENERAL ]`` の ``R-SPACING`` を設定する。"""
        self._config.rmc_r_spacing = float(dr)
        self._set_value("GENERAL", "R-SPACING", self._fmt_number(dr))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_moveout_option(self) -> bool:
        """``[ GENERAL ]`` の ``MOVEOUT`` を返す。"""
        value = self._first_value("GENERAL", "MOVEOUT", "0")
        return self._bool_int(value) == "1"

    def set_moveout_option(
        self, use_moveout: bool, *, auto_write: Optional[bool] = True
    ) -> None:
        """``[ GENERAL ]`` の ``MOVEOUT`` を設定する。"""
        self._config.rmc_moveout_option = bool(use_moveout)
        self._set_value("GENERAL", "MOVEOUT", self._bool_int(use_moveout))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_num_config_to_collect(self) -> int:
        """``[ GENERAL ]`` の ``COLL-NUMBER`` を返す。"""
        value = self._first_value("GENERAL", "COLL-NUMBER", "0")
        return int(float(value))

    def set_num_config_to_collect(
        self, value: int, *, auto_write: Optional[bool] = True
    ) -> None:
        """``[ GENERAL ]`` の ``COLL-NUMBER`` を設定する。"""
        self._set_value("GENERAL", "COLL-NUMBER", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_print_interval(self) -> int:
        """``[ GENERAL ]`` の ``PRINT-STEP`` を返す。"""
        value = self._first_value("GENERAL", "PRINT-STEP", "0")
        return int(float(value))

    def set_print_interval(
        self, value: int, *, auto_write: Optional[bool] = True
    ) -> None:
        """``[ GENERAL ]`` の ``PRINT-STEP`` を設定する。"""
        self._set_value("GENERAL", "PRINT-STEP", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_time_and_save(self) -> Tuple[float, int]:
        """``[ GENERAL ]`` の ``RUN-TIME`` と ``SAVE-TIME`` を返す。"""
        run_time = self._first_value("GENERAL", "RUN-TIME", "0")
        save_time = self._first_value("GENERAL", "SAVE-TIME", "0")
        return float(run_time), int(float(save_time))

    def set_time_and_save(
        self,
        time_limit_min: float,
        save_interval_step: float,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """``[ GENERAL ]`` の ``RUN-TIME`` と ``SAVE-TIME`` を設定する。"""
        self._config.rmc_time_and_save = (
            float(time_limit_min),
            int(save_interval_step),
        )
        self._set_value("GENERAL", "RUN-TIME", self._fmt_number(time_limit_min))
        self._set_value("GENERAL", "SAVE-TIME", self._fmt_number(save_interval_step))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_data_flags(self) -> Tuple[int, int, int, int]:
        """``[ EXP ]`` の ``TYPE`` からデータ種別ごとの件数を返す。

        戻り値の順序は ``GR``, ``ND``, ``XRD``, ``EXAFS``。
        """
        return self._exp_type_counts()

    def set_data_flags(
        self, flags: Sequence[int], *, auto_write: Optional[bool] = True
    ) -> bool:
        """指定されたデータ種別の ``[ EXP ]`` セクションを残す。

        新しい ``[ EXP ]`` は ``TYPE`` だけを持つ。``DATAFILE`` などの必須値を
        空文字やダミー値で補完しない。
        """
        values = list(flags)
        if len(values) != 4:
            self._logger.error("[rmc_pot_dat_free] flags は4要素で指定してください")
            return False
        for value in values:
            if value not in (0, 1):
                self._logger.error(
                    "[rmc_pot_dat_free] flags は0または1で指定してください"
                )
                return False
        types = ["GR", "ND", "XRD", "EXAFS"]
        existing = self._find_sections("EXP")
        non_exp_sections = []
        for section_name, section_values in self._sections:
            if section_name != "EXP":
                non_exp_sections.append((section_name, section_values))
        selected_exp_sections = []
        for flag, exp_type in zip(values, types):
            if flag == 0:
                continue
            selected = None
            for exp in existing:
                current_type = exp.get("TYPE", [""])[0].upper()
                if current_type == exp_type:
                    selected = exp
                    break
            if selected is None:
                selected = {"TYPE": [exp_type]}
            selected_exp_sections.append(("EXP", selected))
        self._sections = non_exp_sections + selected_exp_sections
        self._config.rmc_data_flags = values
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_exp_filename(self) -> Union[str, bool]:
        """
        最初の [ EXP ] セクションに設定された実験データファイル名を取得します。

        Returns:
            str:
                [ EXP ] セクションの DATAFILE に設定された実験データファイル名。
            bool:
                False（[ EXP ] セクションが存在しない、DATAFILE が存在しない、
                または DATAFILE が空の場合）。

        Notes:
            - 自由形式 (*.dat) では実験データは [ EXP ] セクションで定義されます。
            - DATAFILE キーには実験データファイル名を指定します。
            - このメソッドは最初の [ EXP ] セクションだけを対象とします。
            - 実験データファイル自体の形式は RMC_POT の仕様に従います。
              g(r)、neutron S(Q)、X-ray F(Q)、EXAFS χ(k) など、
              TYPE の指定に応じたデータファイルを参照します。
        """
        exp = self._first_exp()

        if exp is None:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] section not found.")
            return False

        datafiles = exp.get("DATAFILE")

        if not datafiles:
            self._logger.error("[rmc_pot_dat_free] DATAFILE not found.")
            return False

        filename = datafiles[0].strip()

        self._logger.info(f'[rmc_pot_dat_free] == get_exp_filename: "{filename}"')

        if not filename:
            self._logger.error("[rmc_pot_dat_free] DATAFILE is empty.")
            return False

        return filename

    def set_exp_filename(
        self, path: Union[str, Path], *, auto_write: Optional[bool] = None
    ) -> bool:
        """最初の ``[ EXP ]`` の ``DATAFILE`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        filename = str(Path(path))
        exp["DATAFILE"] = [filename]
        self._config.rmc_exp_filename = filename
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_exp_range(self) -> Union[Tuple[int, int], bool]:
        """最初の ``[ EXP ]`` の ``POINT-RANGE`` を返す。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        values = exp.get("POINT-RANGE", [])
        if not values:
            self._logger.error("[rmc_pot_dat_free] POINT-RANGE がありません")
            return False
        tokens = values[0].split()
        if len(tokens) != 2:
            self._logger.error(
                f"[rmc_pot_dat_free] POINT-RANGE が不正です: {values[0]}"
            )
            return False
        try:
            return int(tokens[0]), int(tokens[1])
        except ValueError:
            self._logger.error(
                f"[rmc_pot_dat_free] POINT-RANGE が不正です: {values[0]}"
            )
            return False

    def set_exp_range(
        self, start: int, end: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """最初の ``[ EXP ]`` の ``POINT-RANGE`` を設定する。"""
        if start < 1 or end < start:
            self._logger.error(
                f"[rmc_pot_dat_free] POINT-RANGE が不正です: {start} {end}"
            )
            return False
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["POINT-RANGE"] = [f"{int(start)} {int(end)}"]
        self._config.rmc_exp_range = (int(start), int(end))
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_scale_factor(self) -> bool:
        """自由形式に汎用 ``SCALE`` キーはないため ``False`` を返す。"""
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式 [ EXP ] に汎用 SCALE キーはありません"
        )
        return False

    def set_scale_factor(
        self, value: float, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式に汎用 ``SCALE`` キーはないため設定しない。"""
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式 [ EXP ] に汎用 SCALE キーはありません"
        )
        return False

    def get_sigma_factor(self) -> Union[float, bool]:
        """最初の ``[ EXP ]`` の ``SIGMA`` を返す。"""
        exp = self._first_exp()
        if not exp:
            return False
        values = exp.get("SIGMA", [])
        if not values:
            return False
        try:
            return float(values[0].split()[0])
        except ValueError:
            self._logger.error(f"[rmc_pot_dat_free] SIGMA が不正です: {values[0]}")
            return False

    def set_sigma_factor(
        self, sigma: float, *, auto_write: Optional[bool] = None
    ) -> bool:
        """最初の ``[ EXP ]`` の ``SIGMA`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["SIGMA"] = [self._fmt_number(sigma)]
        self._config.rmc_sigma_factor = float(sigma)
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_flag_15(self) -> bool:
        """最初の ``[ EXP ]`` の ``USE-RFACTOR`` を返す。"""
        exp = self._first_exp()
        if not exp:
            return False
        values = exp.get("USE-RFACTOR", ["0"])
        return self._bool_int(values[0]) == "1"

    def set_flag_15(self, value: bool, *, auto_write: Optional[bool] = None) -> bool:
        """最初の ``[ EXP ]`` の ``USE-RFACTOR`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["USE-RFACTOR"] = [self._bool_int(value)]
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_flag_16(self) -> bool:
        """最初の ``[ EXP ]`` の ``RENORM`` を返す。"""
        exp = self._first_exp()
        if not exp:
            return False
        values = exp.get("RENORM", ["0"])
        return self._bool_int(values[0]) == "1"

    def set_flag_16(self, value: bool, *, auto_write: Optional[bool] = None) -> bool:
        """最初の ``[ EXP ]`` の ``RENORM`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["RENORM"] = [self._bool_int(value)]
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_flag_17(self) -> bool:
        """最初の ``[ EXP ]`` の ``READ-COEFFS`` を返す。"""
        exp = self._first_exp()
        if not exp:
            return False
        values = exp.get("READ-COEFFS", ["0"])
        return self._bool_int(values[0]) == "1"

    def set_flag_17(self, value: bool, *, auto_write: Optional[bool] = None) -> bool:
        """最初の ``[ EXP ]`` の ``READ-COEFFS`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["READ-COEFFS"] = [self._bool_int(value)]
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_flag_18(self) -> bool:
        """最初の ``[ EXP ]`` の ``COMPTON-SUPR-COEFF`` を返す。"""
        exp = self._first_exp()
        if not exp:
            return False
        values = exp.get("COMPTON-SUPR-COEFF", ["0"])
        return self._bool_int(values[0]) == "1"

    def set_flag_18(self, value: bool, *, auto_write: Optional[bool] = None) -> bool:
        """最初の ``[ EXP ]`` の ``COMPTON-SUPR-COEFF`` を設定する。"""
        exp = self._first_exp()
        if not exp:
            self._logger.error("[rmc_pot_dat_free] [ EXP ] セクションがありません")
            return False
        exp["COMPTON-SUPR-COEFF"] = [self._bool_int(value)]
        if self._resolve_auto_write(auto_write):
            self.write()
        return True

    def get_angle_constraint_count(self) -> int:
        """``[ COS ]`` セクション数を返す。"""
        return len(self._find_sections("COS"))

    def set_angle_constraint_count(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式では制約数を独立設定できないため設定しない。"""
        current = len(self._find_sections("COS"))
        if int(value) == current:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式では [ COS ] の個数はセクション実体から決まります"
        )
        return False

    def get_coord_constraint_count(self) -> int:
        """``[ COORD ]`` セクション数を返す。"""
        return len(self._find_sections("COORD"))

    def set_coord_constraint_count(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式では制約数を独立設定できないため設定しない。"""
        current = len(self._find_sections("COORD"))
        if int(value) == current:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式では [ COORD ] の個数はセクション実体から決まります"
        )
        return False

    def get_avg_coord_constraint_count(self) -> int:
        """``[ AVCOORD ]`` セクション数を返す。"""
        return len(self._find_sections("AVCOORD"))

    def set_avg_coord_constraint_count(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式では制約数を独立設定できないため設定しない。"""
        current = len(self._find_sections("AVCOORD"))
        if int(value) == current:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式では [ AVCOORD ] の個数はセクション実体から決まります"
        )
        return False

    def get_potential_flag(self) -> int:
        """potential セクションが存在する場合に ``1``、なければ ``0`` を返す。"""
        for section in ("NBPOT", "BPOT", "AENET", "TABPOT"):
            if self._find_sections(section):
                return 1
        return 0

    def set_potential_flag(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式では potential 種別をセクションで指定するため設定しない。"""
        current = self.get_potential_flag()
        if int(value) == current:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] 自由形式では [ NBPOT ]、[ BPOT ]、[ AENET ]、[ TABPOT ] を設定してください"
        )
        return False

    def get_fnc_switch(self) -> int:
        """FNC または ``[ BPOT ]`` の状態を数値で取得する。

        Returns:
            0 から 4 の状態番号。

            - 0: FNC なし、かつ ``[ BPOT ]`` なし
            - 1: ``FNC-TYPE = NORMAL``
            - 2: ``FNC-TYPE = ADJUST``
            - 3: ``FNC-TYPE = MOVE-IN``
            - 4: ``[ BPOT ]`` による flexible molecule / topology mode

        Notes:
            ``FNC-TYPE`` が存在しない場合も ``NONE`` として扱う。
            ``[ BPOT ]`` が存在しない場合は topology mode ではない。

            自由形式では ``FNC-TYPE`` に 4 または ``FLEXIBLE`` は存在しない。
            topology を使う flexible molecule mode は ``[ BPOT ]`` の存在で判定する。
        """
        if self._find_sections("BPOT"):
            return 4

        fnc_type = self._first_value(
            "GENERAL",
            "FNC-TYPE",
            "NONE",
        )
        tokens = fnc_type.split()
        if not tokens:
            return 0

        mode = self._FREE_TO_FNC.get(tokens[0].upper())
        if mode is None:
            raise ValueError("未対応の FNC-TYPE です: " f"{tokens[0]}")
        return mode

    def get_fnc_options(self) -> List[str]:
        """FNC / topology option を取得する。

        Returns:
            FNC 1～3 では ``FNC-TYPE`` の追加トークンを返す。
            topology mode では ``[ BPOT ]`` の ``COMP-OPTION`` を返す。
        """
        mode = self.get_fnc_switch()

        if mode == 4:
            section = self._first_section("BPOT")
            return list(section.get("COMP-OPTION", []))

        fnc_type = self._first_value(
            "GENERAL",
            "FNC-TYPE",
            "NONE",
        )
        tokens = fnc_type.split()
        return tokens[1:]

    @staticmethod
    def _coerce_fnc_switch_value(
        value: Union[bool, int],
    ) -> int:
        """
        FNC switch のユーザー入力を RMC_POT の番号へ変換する。

        bool 入力はユーザー向け I/F として扱う。
            False -> 0
            True  -> 1

        int 入力は RMC_POT の生番号指定として扱い、bool より優先してその番号を使う。
        """
        if isinstance(value, bool):
            if value:
                return 1
            return 0

        mode = int(value)
        if mode < 0 or mode > 4:
            raise ValueError("FNC switch は 0, 1, 2, 3, 4 のいずれかです。")
        return mode

    @staticmethod
    def _coerce_fnc_options(
        opt: Optional[Union[str, Sequence[str]]],
    ) -> List[str]:
        """FNC switch 行の追加オプションを token list に正規化する。"""
        if opt is None:
            return []
        if isinstance(opt, str):
            s = opt.strip()
            if not s:
                return []
            return s.split()
        options: List[str] = []
        for value in opt:
            option = str(value).strip()
            if option:
                options.append(option)
        return options

    def set_fnc_switch(
        self,
        value: Union[bool, int],
        *,
        opt: Optional[Union[str, Sequence[str]]] = None,
        keep_existing_opt: bool = True,
        auto_write: Optional[bool] = None,
    ) -> None:
        """FNC または topology mode を設定する。

        Args:
            value: ``False``/``True`` または 0～4 の状態番号。
            opt: FNC の追加トークン、または mode 4 の ``COMP-OPTION``。
            keep_existing_opt: ``opt`` 省略時に既存 option を保持するか。
            auto_write: 設定後に直ちに保存するか。

        Raises:
            ValueError: FNC 1～3 と ``[ BPOT ]`` を同時指定した場合。

        Notes:
            自由形式では FNC 1～3 は ``[ GENERAL ]`` の ``FNC-TYPE`` で指定する。
            flexible molecule mode は
            ``FNC-TYPE`` ではなく ``[ BPOT ]`` の存在で指定する。
        """
        is_bool_input = isinstance(value, bool)
        mode = self._coerce_fnc_switch_value(value)

        options: List[str] = []
        if opt is not None:
            options = self._coerce_fnc_options(opt)
        else:
            if keep_existing_opt:
                if not is_bool_input:
                    options = self.get_fnc_options()

        if mode == 4:
            self._set_value(
                "GENERAL",
                "FNC-TYPE",
                "NONE",
            )

            bpot = self._first_section(
                "BPOT",
                create=True,
            )
            if options:
                bpot["COMP-OPTION"] = list(options)

        else:
            if mode in {1, 2, 3}:
                if self._find_sections("BPOT"):
                    raise ValueError(
                        "自由形式では FNC 1～3 と [ BPOT ] topology mode "
                        "を同時に使用できません。"
                    )

            if mode == 0:
                retained_sections = []
                for name, values in self._sections:
                    if name != "BPOT":
                        retained_sections.append((name, values))
                self._sections = retained_sections

            free_mode = self._FNC_TO_FREE[mode]
            tokens = [free_mode]
            tokens.extend(options)
            self._set_value(
                "GENERAL",
                "FNC-TYPE",
                " ".join(tokens),
            )

        self.validate_mode_configuration(
            check_input_files=False,
        )

        if self._resolve_auto_write(auto_write):
            self.write()

    def validate_mode_configuration(
        self,
        *,
        check_input_files: bool = False,
    ) -> None:
        """自由形式の mode 指定と入力ファイルを検証する。

        Args:
            check_input_files: ``True`` の場合、mode が要求する
                ``*.fnc`` または ``*.top`` の存在も確認する。

        Raises:
            ValueError: 排他的な mode が同時に設定されている場合。
            FileNotFoundError: 必要な外部入力ファイルが存在しない場合。

        Notes:
            ``[ SNC ]`` は ``*.dat`` 内の制約セクションであり、
            外部 ``*.snc`` 入力ファイルを選択する mode ではない。
        """
        fnc_type = self._first_value(
            "GENERAL",
            "FNC-TYPE",
            "NONE",
        )
        fnc_tokens = fnc_type.split()

        fnc_mode = "NONE"
        if fnc_tokens:
            fnc_mode = fnc_tokens[0].upper()

        allowed_fnc_modes = {
            "NONE",
            "NORMAL",
            "ADJUST",
            "MOVE-IN",
        }
        if fnc_mode not in allowed_fnc_modes:
            raise ValueError(
                "自由形式の FNC-TYPE は NONE、NORMAL、ADJUST、"
                "MOVE-IN のいずれかです。"
            )

        has_bpot = bool(self._find_sections("BPOT"))
        if has_bpot:
            if fnc_mode != "NONE":
                raise ValueError(
                    "[ BPOT ] topology mode と FNC-TYPE=NORMAL/ADJUST/"
                    "MOVE-IN は同時に使用できません。"
                )

        if self._find_sections("AENET"):
            self._validate_aenet_compatibility()

        if not check_input_files:
            return

        if fnc_mode != "NONE":
            fnc_path = Path(f"{self._cfg_name}.fnc")
            if not fnc_path.exists():
                raise FileNotFoundError(
                    f"FNC mode に必要なファイルがありません: {fnc_path}"
                )

        if has_bpot:
            top_path = Path(f"{self._cfg_name}.top")
            if not top_path.exists():
                raise FileNotFoundError(
                    "topology mode に必要なファイルがありません: " f"{top_path}"
                )

    def _resolve_fnc_path(
        self,
        fnc_name: Optional[str] = None,
    ) -> Path:
        """
        FNC ファイルパスを解決する。
        """
        if fnc_name is None:
            return Path(f"{self._cfg_name}.fnc")

        path = Path(fnc_name)
        if path.suffix == ".fnc":
            return path

        return Path(f"{fnc_name}.fnc")

    def _find_fnc_range_header_index(
        self,
        lines: List[str],
        path: Path,
    ) -> int:
        """
        FNC ファイル内の rmin/rmax 定義ヘッダ行を探す。
        """
        for index, line in enumerate(lines):
            if "No. of possible rmin-rmax pairs" in line:
                return index

        raise ValueError(f"FNC rmin/rmax ヘッダが見つかりません: {path}")

    def get_fnc_distance_ranges(
        self,
        fnc_name: Optional[str] = None,
    ) -> Dict[int, Tuple[float, float]]:
        """
        FNC ファイルの constraint type ごとの rmin/rmax を取得する。
        """
        path = self._resolve_fnc_path(fnc_name)

        if not path.exists():
            raise FileNotFoundError(f"FNC ファイルが見つかりません: {path}")

        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        header_index = self._find_fnc_range_header_index(lines, path)

        if len(lines) <= header_index + 3:
            raise ValueError(f"FNC ファイルのヘッダが短すぎます: {path}")

        try:
            type_count = int(lines[header_index + 1].split()[0])
        except (IndexError, ValueError) as exc:
            raise ValueError(f"FNC type 数を読めません: {path}") from exc

        rmins = [float(v) for v in lines[header_index + 2].split()]
        rmaxs = [float(v) for v in lines[header_index + 3].split()]

        if len(rmins) != type_count:
            raise ValueError(
                f"FNC rmin 数が type 数と一致しません: "
                f"type_count={type_count}, rmin_count={len(rmins)}"
            )

        if len(rmaxs) != type_count:
            raise ValueError(
                f"FNC rmax 数が type 数と一致しません: "
                f"type_count={type_count}, rmax_count={len(rmaxs)}"
            )

        ranges: Dict[int, Tuple[float, float]] = {}
        type_index = 1
        while type_index <= type_count:
            ranges[type_index] = (
                rmins[type_index - 1],
                rmaxs[type_index - 1],
            )
            type_index = type_index + 1

        return ranges

    def set_fnc_distance_ranges(
        self,
        ranges: Dict[int, Tuple[float, float]],
        fnc_name: Optional[str] = None,
    ) -> None:
        """
        FNC ファイルの constraint type ごとの rmin/rmax を更新する。

        既存の FNC ペア、neighbor index、constraint type は変更しない。
        変更するのはヘッダの rmin/rmax のみである。
        """
        path = self._resolve_fnc_path(fnc_name)

        if not path.exists():
            raise FileNotFoundError(f"FNC ファイルが見つかりません: {path}")

        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        header_index = self._find_fnc_range_header_index(lines, path)

        if len(lines) <= header_index + 3:
            raise ValueError(f"FNC ファイルのヘッダが短すぎます: {path}")

        try:
            type_count = int(lines[header_index + 1].split()[0])
        except (IndexError, ValueError) as exc:
            raise ValueError(f"FNC type 数を読めません: {path}") from exc

        rmins = [float(v) for v in lines[header_index + 2].split()]
        rmaxs = [float(v) for v in lines[header_index + 3].split()]

        if len(rmins) != type_count:
            raise ValueError(
                f"FNC rmin 数が type 数と一致しません: "
                f"type_count={type_count}, rmin_count={len(rmins)}"
            )

        if len(rmaxs) != type_count:
            raise ValueError(
                f"FNC rmax 数が type 数と一致しません: "
                f"type_count={type_count}, rmax_count={len(rmaxs)}"
            )

        for type_index, distance_range in ranges.items():
            if type_index < 1 or type_index > type_count:
                raise ValueError(
                    f"FNC constraint type が範囲外です: "
                    f"type_index={type_index}, type_count={type_count}"
                )

            rmin = float(distance_range[0])
            rmax = float(distance_range[1])

            if rmin >= rmax:
                raise ValueError(
                    f"FNC rmin は rmax より小さい必要があります: "
                    f"type_index={type_index}, rmin={rmin}, rmax={rmax}"
                )

            rmins[type_index - 1] = rmin
            rmaxs[type_index - 1] = rmax

        lines[header_index + 2] = " ".join(self._fmt_number(v) for v in rmins) + "\n"
        lines[header_index + 3] = " ".join(self._fmt_number(v) for v in rmaxs) + "\n"

        with path.open("w", encoding="utf-8") as f:
            f.writelines(lines)

        self._logger.info(f"[rmc_pot_dat_free] == set_fnc_distance_ranges({path})")

    def get_initial_bin_shift(self) -> int:
        """``[ GENERAL ]`` の ``BIN-SHIFT`` を返す。"""
        value = self._first_value("GENERAL", "BIN-SHIFT", "0")
        return int(float(value))

    def set_initial_bin_shift(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の ``BIN-SHIFT`` を設定する。"""
        self._set_value("GENERAL", "BIN-SHIFT", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_xmax_used(self) -> float:
        """``[ GENERAL ]`` の ``XMAX-FACTOR`` を返す。"""
        value = self._first_value("GENERAL", "XMAX-FACTOR", "1.0")
        return float(value)

    def set_xmax_used(self, value: float, *, auto_write: Optional[bool] = None) -> None:
        """``[ GENERAL ]`` の ``XMAX-FACTOR`` を設定する。"""
        self._set_value("GENERAL", "XMAX-FACTOR", self._fmt_number(value))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_num_atoms_per_move(self) -> int:
        """通常の自由形式 atomic RMC では1回の move で動かす原子数は1を返す。"""
        return 1

    def set_num_atoms_per_move(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式 atomic RMC では1以外を設定しない。"""
        if int(value) != 1:
            self._logger.error(
                "[rmc_pot_dat_free] 自由形式の通常 atomic RMC では1回の move で動かす原子数は1です"
            )
            return False
        self._config.rmc_num_atoms_per_move = 1
        return True

    def get_history_buffer_size(self) -> int:
        """``[ GENERAL ]`` の ``HST_BUFFSIZE`` を返す。"""
        value = self._first_value("GENERAL", "HST_BUFFSIZE", "0")
        return int(float(value))

    def set_history_buffer_size(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の ``HST_BUFFSIZE`` を設定する。"""
        self._set_value("GENERAL", "HST_BUFFSIZE", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_display_update_interval(self) -> int:
        """``[ GENERAL ]`` の ``HST-STEP-FACTOR`` を返す。"""
        value = self._first_value("GENERAL", "HST-STEP-FACTOR", "1")
        return int(float(value))

    def set_display_update_interval(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の ``HST-STEP-FACTOR`` を設定する。"""
        self._set_value("GENERAL", "HST-STEP-FACTOR", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_custom_move_flag(self) -> int:
        """自由形式で対応する設定がないため ``0`` を返す。"""
        return 0

    def set_custom_move_flag(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式で対応する設定がないため設定しない。"""
        if int(value) == 0:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] この設定に対応する自由形式キーワードはありません"
        )
        return False

    def get_load_histogram_flag(self) -> int:
        """``[ GENERAL ]`` の ``RELOAD`` を返す。"""
        value = self._first_value("GENERAL", "RELOAD", "0")
        return int(float(value))

    def set_load_histogram_flag(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の ``RELOAD`` を設定する。"""
        self._set_value("GENERAL", "RELOAD", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_max_atoms_per_cell(self) -> int:
        """自由形式で対応する設定がないため ``0`` を返す。"""
        return 0

    def set_max_atoms_per_cell(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> bool:
        """自由形式で対応する設定がないため設定しない。"""
        if int(value) == 0:
            return True
        self._logger.error(
            "[rmc_pot_dat_free] この設定に対応する自由形式キーワードはありません"
        )
        return False

    def get_swap_settings(self) -> Tuple[float, int]:
        """``[ GENERAL ]`` の ``SWAP-FRACTION`` と ``SWAP-ALLOW`` を返す。"""
        fraction = self._first_value("GENERAL", "SWAP-FRACTION", "0")
        allow = self._first_value("GENERAL", "SWAP-ALLOW", "0")
        return float(fraction), int(float(allow))

    def set_swap_settings(
        self, fraction: int, allow_flag: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の swap 関連キーワードを設定する。"""
        self._set_value("GENERAL", "SWAP-FRACTION", self._fmt_number(fraction))
        self._set_value("GENERAL", "SWAP-ALLOW", str(int(allow_flag)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def get_thread_count(self) -> int:
        """``[ GENERAL ]`` の ``THREADS`` を返す。"""
        value = self._first_value("GENERAL", "THREADS", "1")
        return int(float(value))

    def set_thread_count(
        self, value: int, *, auto_write: Optional[bool] = None
    ) -> None:
        """``[ GENERAL ]`` の ``THREADS`` を設定する。"""
        self._set_value("GENERAL", "THREADS", str(int(value)))
        if self._resolve_auto_write(auto_write):
            self.write()

    def _resolve_auto_write(self, auto_write: Optional[bool]) -> bool:
        """自動書き込みの実行可否を決定する。

        Args:
            auto_write: メソッド呼び出し単位の自動書き込み指定。
                ``None`` の場合はインスタンスの ``auto_write`` 設定を使う。

        Returns:
            書き込みを実行する場合は ``True``、実行しない場合は ``False``。
        """
        if auto_write is None:
            return self._auto_write
        return auto_write

    @staticmethod
    def _normalize_sigma_mode(mode: str) -> str:
        """sigma 指定方式を正規化する。

        Args:
            mode: ``normal``、``master``、``scalable`` のいずれか。

        Returns:
            小文字へ正規化した sigma 指定方式。

        Raises:
            ValueError: 未対応の指定方式が与えられた場合。
        """
        normalized = str(mode).strip().lower()
        allowed = {
            "normal",
            "master",
            "scalable",
        }
        if normalized not in allowed:
            raise ValueError(
                "sigma_mode は 'normal'、'master'、'scalable' "
                "のいずれかで指定してください。"
            )
        return normalized

    @classmethod
    def _sigma_keyword(
        cls,
        base_keyword: str,
        sigma_mode: str,
    ) -> str:
        """sigma 指定方式に対応する自由形式キーワードを返す。

        Args:
            base_keyword: 通常 sigma 用の基本キーワード。
            sigma_mode: ``normal``、``master``、``scalable`` のいずれか。

        Returns:
            自由形式 ``*.dat`` へ書き込むキーワード。
        """
        mode = cls._normalize_sigma_mode(sigma_mode)
        if mode == "master":
            return f"{base_keyword}-MASTER"
        if mode == "scalable":
            return f"{base_keyword}-SCALABLE"
        return base_keyword

    @staticmethod
    def _validate_positive_atom_type(
        atom_type: int,
        argument_name: str,
    ) -> int:
        """RMC 原子タイプ番号を検証する。

        Args:
            atom_type: 1 始まりの RMC 原子タイプ番号。
            argument_name: 例外メッセージへ表示する引数名。

        Returns:
            検証済みの整数値。

        Raises:
            ValueError: 原子タイプ番号が 1 未満の場合。
        """
        value = int(atom_type)
        if value < 1:
            raise ValueError(f"{argument_name} は 1 以上で指定してください。")
        return value

    @staticmethod
    def _validate_distance_range(
        minimum: Union[int, float],
        maximum: Union[int, float],
        argument_name: str,
    ) -> Tuple[float, float]:
        """距離範囲を検証する。

        Args:
            minimum: 距離範囲の下限。単位は Å。
            maximum: 距離範囲の上限。単位は Å。
            argument_name: 例外メッセージへ表示する範囲名。

        Returns:
            ``(minimum, maximum)`` の浮動小数点数タプル。

        Raises:
            ValueError: 下限が負、または上限が下限以下の場合。
        """
        minimum_value = float(minimum)
        maximum_value = float(maximum)

        if minimum_value < 0.0:
            raise ValueError(f"{argument_name} の下限は 0 以上で指定してください.")
        if maximum_value <= minimum_value:
            raise ValueError(f"{argument_name} の上限は下限より大きくしてください.")
        return minimum_value, maximum_value

    def get_qn_constraints(self) -> List[Dict[str, Any]]:
        """自由形式 ``[ SNC ]`` の Qn 制約を取得する。

        Returns:
            Qn 制約ごとの辞書を格納したリスト。各辞書は次を含む。

            - ``central_type``: 中心原子の RMC タイプ番号
            - ``first_neighbor_type``: 第一近接原子の RMC タイプ番号
            - ``first_neighbor_range``: 第一近接距離範囲 ``(min, max)`` [Å]
            - ``second_neighbors``: 第二近接タイプと距離範囲のリスト
            - ``coordination_number``: 目標 Qn の n
            - ``fraction``: 制約を満たす中心原子の目標割合
            - ``sigma``: 重みパラメータ
            - ``sigma_mode``: ``normal``、``master``、``scalable``

        Raises:
            ValueError: 必須キーワードが欠落している場合、または値の個数が
                マニュアルの ``[ SNC ]`` 形式と一致しない場合。

        Notes:
            Qn 制約は第二近接制約である。中心タイプ ``i`` が第一近接タイプ
            ``j`` を n 個持ち、各第一近接を介して指定タイプの第二近接が
            存在する状態を、指定割合の中心原子へ課す。
        """
        constraints: List[Dict[str, Any]] = []
        sections = self._find_sections("SNC")

        for section_index, section in enumerate(sections):
            central_values = section.get("CTYPE_FTYPE_FROM_TO", [])
            if len(central_values) != 1:
                raise ValueError(
                    f"[SNC] index={section_index}: "
                    "CTYPE_FTYPE_FROM_TO は 1 行必要です。"
                )

            central_tokens = central_values[0].split()
            if len(central_tokens) != 4:
                raise ValueError(
                    f"[SNC] index={section_index}: "
                    "CTYPE_FTYPE_FROM_TO は 4 値必要です。"
                )

            second_values = section.get("STYPE_FROM_TO", [])
            if not second_values:
                raise ValueError(
                    f"[SNC] index={section_index}: "
                    "STYPE_FROM_TO は 1 行以上必要です。"
                )

            second_neighbors: List[Dict[str, Any]] = []
            for second_value in second_values:
                second_tokens = second_value.split()
                if len(second_tokens) != 3:
                    raise ValueError(
                        f"[SNC] index={section_index}: "
                        "STYPE_FROM_TO は 3 値必要です。"
                    )
                second_neighbors.append(
                    {
                        "atom_type": int(second_tokens[0]),
                        "minimum": float(second_tokens[1]),
                        "maximum": float(second_tokens[2]),
                    }
                )

            sigma_key = ""
            sigma_mode = ""
            candidate_keys = [
                ("COORDNUM_FRACT_SIGMA", "normal"),
                ("COORDNUM_FRACT_SIGMA-MASTER", "master"),
                ("COORDNUM_FRACT_SIGMA-SCALABLE", "scalable"),
            ]
            for candidate_key, candidate_mode in candidate_keys:
                values = section.get(candidate_key, [])
                if values:
                    if sigma_key:
                        raise ValueError(
                            f"[SNC] index={section_index}: "
                            "sigma 指定は 1 種類だけ使用してください。"
                        )
                    sigma_key = candidate_key
                    sigma_mode = candidate_mode

            if not sigma_key:
                raise ValueError(
                    f"[SNC] index={section_index}: "
                    "COORDNUM_FRACT_SIGMA 系キーワードが必要です。"
                )

            sigma_values = section[sigma_key]
            if len(sigma_values) != 1:
                raise ValueError(
                    f"[SNC] index={section_index}: " f"{sigma_key} は 1 行必要です。"
                )

            sigma_tokens = sigma_values[0].split()
            if len(sigma_tokens) != 3:
                raise ValueError(
                    f"[SNC] index={section_index}: " f"{sigma_key} は 3 値必要です。"
                )

            constraint = {
                "central_type": int(central_tokens[0]),
                "first_neighbor_type": int(central_tokens[1]),
                "first_neighbor_range": (
                    float(central_tokens[2]),
                    float(central_tokens[3]),
                ),
                "second_neighbors": second_neighbors,
                "coordination_number": int(sigma_tokens[0]),
                "fraction": float(sigma_tokens[1]),
                "sigma": float(sigma_tokens[2]),
                "sigma_mode": sigma_mode,
            }
            constraints.append(constraint)

        return constraints

    def add_qn_constraint(
        self,
        central_type: int,
        first_neighbor_type: int,
        first_neighbor_minimum: Union[int, float],
        first_neighbor_maximum: Union[int, float],
        second_neighbors: Sequence[Tuple[int, Union[int, float], Union[int, float]]],
        coordination_number: int,
        fraction: Union[int, float],
        sigma: Union[int, float],
        *,
        sigma_mode: str = "normal",
        auto_write: Optional[bool] = None,
    ) -> int:
        """Qn 第二近接制約を新しい ``[ SNC ]`` セクションとして追加する。

        Args:
            central_type: 中心原子の RMC タイプ番号。
            first_neighbor_type: 第一近接原子の RMC タイプ番号。
            first_neighbor_minimum: 中心-第一近接距離の下限 [Å]。
            first_neighbor_maximum: 中心-第一近接距離の上限 [Å]。
            second_neighbors: 第二近接原子ごとの
                ``(atom_type, minimum, maximum)``。距離は第一近接原子から
                第二近接原子までの範囲 [Å]。
            coordination_number: 目標 Qn の n。
            fraction: 制約を満たす中心原子の目標割合。0 以上 1 以下。
            sigma: 制約の重みパラメータ。
            sigma_mode: ``normal``、``master``、``scalable`` のいずれか。
            auto_write: 更新後に ``*.dat`` を保存するかどうか。

        Returns:
            追加した ``[ SNC ]`` セクションの 0 始まりインデックス。

        Raises:
            ValueError: 原子タイプ、距離範囲、割合、sigma、または第二近接指定が
                不正な場合。

        Notes:
            出力する必須キーワードは次の3種類である。

            - ``CTYPE_FTYPE_FROM_TO``
            - 1 行以上の ``STYPE_FROM_TO``
            - ``COORDNUM_FRACT_SIGMA`` 系のいずれか1つ
        """
        central_value = self._validate_positive_atom_type(
            central_type,
            "central_type",
        )
        first_value = self._validate_positive_atom_type(
            first_neighbor_type,
            "first_neighbor_type",
        )
        first_minimum, first_maximum = self._validate_distance_range(
            first_neighbor_minimum,
            first_neighbor_maximum,
            "first_neighbor_range",
        )

        if not second_neighbors:
            raise ValueError("second_neighbors は 1 件以上必要です。")

        coordination_value = int(coordination_number)
        if coordination_value < 0:
            raise ValueError("coordination_number は 0 以上で指定してください。")

        fraction_value = float(fraction)
        if fraction_value < 0.0 or fraction_value > 1.0:
            raise ValueError("fraction は 0 以上 1 以下で指定してください。")

        sigma_value = float(sigma)
        if sigma_value <= 0.0:
            raise ValueError("sigma は 0 より大きい値を指定してください。")

        section_index = self.add_section("SNC")
        section = self._find_sections("SNC")[section_index]

        section["CTYPE_FTYPE_FROM_TO"] = [
            self._fmt_sequence(
                [
                    central_value,
                    first_value,
                    first_minimum,
                    first_maximum,
                ]
            )
        ]

        section["STYPE_FROM_TO"] = []
        for atom_type, minimum, maximum in second_neighbors:
            second_type = self._validate_positive_atom_type(
                atom_type,
                "second_neighbor atom_type",
            )
            second_minimum, second_maximum = self._validate_distance_range(
                minimum,
                maximum,
                "second_neighbor_range",
            )
            section["STYPE_FROM_TO"].append(
                self._fmt_sequence(
                    [
                        second_type,
                        second_minimum,
                        second_maximum,
                    ]
                )
            )

        sigma_key = self._sigma_keyword(
            "COORDNUM_FRACT_SIGMA",
            sigma_mode,
        )
        section[sigma_key] = [
            self._fmt_sequence(
                [
                    coordination_value,
                    fraction_value,
                    sigma_value,
                ]
            )
        ]

        self._logger.info(
            "[rmc_pot_dat_free] add_qn_constraint: "
            f"index={section_index}, Q{coordination_value}"
        )

        if self._resolve_auto_write(auto_write):
            self.write()

        return section_index

    def set_qn_constraint(
        self,
        index: int,
        central_type: int,
        first_neighbor_type: int,
        first_neighbor_minimum: Union[int, float],
        first_neighbor_maximum: Union[int, float],
        second_neighbors: Sequence[Tuple[int, Union[int, float], Union[int, float]]],
        coordination_number: int,
        fraction: Union[int, float],
        sigma: Union[int, float],
        *,
        sigma_mode: str = "normal",
        auto_write: Optional[bool] = None,
    ) -> None:
        """既存の Qn 第二近接制約を置き換える。

        Args:
            index: 置換対象の ``[ SNC ]`` セクション番号。
            central_type: 中心原子の RMC タイプ番号。
            first_neighbor_type: 第一近接原子の RMC タイプ番号。
            first_neighbor_minimum: 中心-第一近接距離の下限 [Å]。
            first_neighbor_maximum: 中心-第一近接距離の上限 [Å]。
            second_neighbors: 第二近接タイプと距離範囲。
            coordination_number: 目標 Qn の n。
            fraction: 制約を満たす中心原子の目標割合。
            sigma: 制約の重みパラメータ。
            sigma_mode: sigma 指定方式。
            auto_write: 更新後に保存するかどうか。

        Raises:
            IndexError: 指定した ``[ SNC ]`` セクションが存在しない場合。
        """
        sections = self._find_sections("SNC")
        if index < 0 or index >= len(sections):
            raise IndexError(f"SNC セクション index={index} は存在しません。")

        self.remove_section("SNC", index)
        new_index = self.add_qn_constraint(
            central_type=central_type,
            first_neighbor_type=first_neighbor_type,
            first_neighbor_minimum=first_neighbor_minimum,
            first_neighbor_maximum=first_neighbor_maximum,
            second_neighbors=second_neighbors,
            coordination_number=coordination_number,
            fraction=fraction,
            sigma=sigma,
            sigma_mode=sigma_mode,
            auto_write=False,
        )

        if new_index != index:
            moved_section = self._find_sections("SNC")[new_index]
            section_position = -1
            count = -1
            for position, (name, values) in enumerate(self._sections):
                if name == "SNC":
                    count += 1
                    if values is moved_section:
                        section_position = position
                        break

            if section_position >= 0:
                name, values = self._sections.pop(section_position)
                target_position = len(self._sections)
                count = -1
                for position, (current_name, _) in enumerate(self._sections):
                    if current_name == "SNC":
                        count += 1
                        if count == index:
                            target_position = position
                            break
                self._sections.insert(target_position, (name, values))

        if self._resolve_auto_write(auto_write):
            self.write()

    def remove_qn_constraint(
        self,
        index: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """指定した Qn 第二近接制約を削除する。

        Args:
            index: 削除対象の ``[ SNC ]`` セクション番号。
            auto_write: 更新後に保存するかどうか。
        """
        self.remove_section("SNC", index)
        self._logger.info(f"[rmc_pot_dat_free] remove_qn_constraint: index={index}")
        if self._resolve_auto_write(auto_write):
            self.write()

    def clear_qn_constraints(
        self,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """すべての Qn 第二近接制約を削除する。

        Args:
            auto_write: 更新後に保存するかどうか。

        Notes:
            従来名との互換メソッド。新しく Qn/SNC 一式を作り直す場合は
            ``initialize_qn_constraints()`` を使用する。
        """
        self.initialize_qn_constraints(
            auto_write=auto_write,
        )

    def _validate_aenet_compatibility(self) -> None:
        """AENET と明示的に共存不可の自由形式セクションを検査する。

        Raises:
            ValueError: 非結合・結合ポテンシャル、局所不変性、非周期境界条件、
                または flexible molecule 設定が既に存在する場合。

        Notes:
            ANN は他の potential と併用できず、local invariance および
            non-periodic boundary conditions とも併用できない。
            coordination constraint、cosine constraint は削除しない。
            SNC についてマニュアルに明示的な併用禁止記述がないため、
            このメソッドでは自動的に拒否しない。
        """
        incompatible_sections = [
            "NBPOT",
            "BPOT",
            "LOCINV",
            "NOPER",
        ]
        for section_name in incompatible_sections:
            if self._find_sections(section_name):
                raise ValueError(
                    "AENET と共存できないセクションがあります: " f"[{section_name}]"
                )

        if self._find_sections("BPOT"):
            raise ValueError("AENET は [ BPOT ] topology mode と併用できません。")

    def get_aenet_settings(self) -> Optional[Dict[str, Any]]:
        """自由形式 ``[ AENET ]`` の ANN ポテンシャル設定を取得する。

        Returns:
            ``[ AENET ]`` が存在しない場合は ``None``。存在する場合は、
            potential ファイル、cutoff、原子別エネルギー出力、計算間隔、
            sigma 指定を格納した辞書。

        Raises:
            ValueError: 必須 ``IND_ANN-FILE_TYPE-NAME`` または sigma 指定が
                欠落している場合。
        """
        sections = self._find_sections("AENET")
        if not sections:
            return None
        if len(sections) > 1:
            raise ValueError("[AENET] セクションは 1 つだけ指定できます。")

        section = sections[0]
        potential_values = section.get("IND_ANN-FILE_TYPE-NAME", [])
        if not potential_values:
            raise ValueError("[AENET] IND_ANN-FILE_TYPE-NAME は 1 行以上必要です。")

        potentials: List[Dict[str, Any]] = []
        for value in potential_values:
            tokens = value.split()
            if len(tokens) < 2 or len(tokens) > 3:
                raise ValueError(
                    "IND_ANN-FILE_TYPE-NAME は "
                    "atom_type filename [type_name] の形式です。"
                )

            item: Dict[str, Any] = {
                "atom_type": int(tokens[0]),
                "filename": tokens[1],
                "type_name": None,
            }
            if len(tokens) == 3:
                item["type_name"] = tokens[2]
            potentials.append(item)

        sigma_key = ""
        sigma_mode = ""
        candidate_keys = [
            ("SIGMA", "normal"),
            ("SIGMA-MASTER", "master"),
            ("SIGMA-SCALABLE", "scalable"),
        ]
        for candidate_key, candidate_mode in candidate_keys:
            values = section.get(candidate_key, [])
            if values:
                if sigma_key:
                    raise ValueError(
                        "[AENET] sigma 指定は 1 種類だけ使用してください。"
                    )
                sigma_key = candidate_key
                sigma_mode = candidate_mode

        if not sigma_key:
            raise ValueError(
                "[AENET] SIGMA、SIGMA-MASTER、SIGMA-SCALABLE " "のいずれかが必要です。"
            )

        settings: Dict[str, Any] = {
            "potentials": potentials,
            "cutoff": None,
            "write_atomic_energy": False,
            "aenet_step": 5,
            "sigma": float(section[sigma_key][0].split()[0]),
            "sigma_mode": sigma_mode,
        }

        cutoff_values = section.get("CUTOFF-AENET", [])
        if cutoff_values:
            settings["cutoff"] = float(cutoff_values[0].split()[0])

        write_values = section.get("WRITE-ATOMIC-ENERGY", [])
        if write_values:
            write_token = self._bool_int(write_values[0])
            if write_token == "1":
                settings["write_atomic_energy"] = True

        step_values = section.get("AENET-STEP", [])
        if step_values:
            settings["aenet_step"] = int(float(step_values[0].split()[0]))

        return settings

    def set_aenet_potential(
        self,
        potentials: Sequence[Tuple[int, str, Optional[str]]],
        sigma: Union[int, float],
        *,
        sigma_mode: str = "normal",
        cutoff: Optional[Union[int, float]] = None,
        write_atomic_energy: bool = False,
        aenet_step: int = 5,
        auto_write: Optional[bool] = None,
    ) -> None:
        """AENET の ANN ポテンシャル設定を作成または置換する。

        Args:
            potentials: 原子タイプごとの
                ``(atom_type, filename, type_name)``。
                ``type_name`` を省略する場合は ``None`` を指定する。
            sigma: ANN potential の chi-square 寄与を重み付けする sigma。
            sigma_mode: ``normal``、``master``、``scalable`` のいずれか。
            cutoff: ANN potential の cutoff [Å]。``None`` の場合は
                potential ファイルに格納された値を使用する。
            write_atomic_energy: 個々の原子エネルギーを ``*.en`` へ出力するか。
            aenet_step: ANN potential を再計算するシミュレーション間隔。
                マニュアル記載の既定値は 5。
            auto_write: 更新後に保存するかどうか。

        Raises:
            ValueError: potential 指定が空、値が不正、または AENET と共存不可の
                セクションが存在する場合。

        Notes:
            ``IND_ANN-FILE_TYPE-NAME`` は原子タイプごとに複数行出力する。
            ``type_name`` を ``None`` にした場合、RMC_POT は
            ``[ GENERAL ]`` の ``CHEMICAL-SYMBOLS`` から元素記号を抽出する。
        """
        self._validate_aenet_compatibility()

        if not potentials:
            raise ValueError("potentials は 1 件以上必要です。")

        sigma_value = float(sigma)
        if sigma_value <= 0.0:
            raise ValueError("sigma は 0 より大きい値を指定してください。")

        step_value = int(aenet_step)
        if step_value < 1:
            raise ValueError("aenet_step は 1 以上で指定してください。")

        cutoff_value: Optional[float] = None
        if cutoff is not None:
            cutoff_value = float(cutoff)
            if cutoff_value <= 0.0:
                raise ValueError("cutoff は 0 より大きい値を指定してください。")

        retained_sections: List[Tuple[str, Dict[str, List[str]]]] = []
        for name, values in self._sections:
            if name != "AENET":
                retained_sections.append((name, values))
        self._sections = retained_sections

        section: Dict[str, List[str]] = {}
        section["IND_ANN-FILE_TYPE-NAME"] = []

        seen_types = set()
        for atom_type, filename, type_name in potentials:
            atom_type_value = self._validate_positive_atom_type(
                atom_type,
                "AENET atom_type",
            )
            if atom_type_value in seen_types:
                raise ValueError(
                    "AENET の atom_type は重複指定できません: " f"{atom_type_value}"
                )
            seen_types.add(atom_type_value)

            filename_value = str(filename).strip()
            if not filename_value:
                raise ValueError("AENET potential filename は空にできません。")

            tokens = [
                str(atom_type_value),
                filename_value,
            ]
            if type_name is not None:
                type_name_value = str(type_name).strip()
                if not type_name_value:
                    raise ValueError(
                        "type_name は文字列または None で指定してください。"
                    )
                tokens.append(type_name_value)

            section["IND_ANN-FILE_TYPE-NAME"].append(" ".join(tokens))

        if cutoff_value is not None:
            section["CUTOFF-AENET"] = [self._fmt_number(cutoff_value)]

        if write_atomic_energy:
            section["WRITE-ATOMIC-ENERGY"] = ["1"]
        else:
            section["WRITE-ATOMIC-ENERGY"] = ["0"]

        section["AENET-STEP"] = [str(step_value)]

        sigma_key = self._sigma_keyword("SIGMA", sigma_mode)
        section[sigma_key] = [self._fmt_number(sigma_value)]

        self._sections.append(("AENET", section))
        self._logger.info(
            "[rmc_pot_dat_free] set_aenet_potential: "
            f"potential_count={len(potentials)}"
        )

        if self._resolve_auto_write(auto_write):
            self.write()

    def add_aenet_potential_file(
        self,
        atom_type: int,
        filename: str,
        type_name: Optional[str] = None,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """既存の ``[ AENET ]`` へ原子タイプ別 potential ファイルを追加する。

        Args:
            atom_type: 1 始まりの RMC 原子タイプ番号。
            filename: AENET で学習済みの ANN potential ファイル名。
            type_name: AENET へ渡す原子タイプ名または元素記号。
                ``None`` の場合は ``CHEMICAL-SYMBOLS`` から抽出させる。
            auto_write: 更新後に保存するかどうか。

        Raises:
            ValueError: ``[ AENET ]`` が未設定、原子タイプが重複、
                または値が不正な場合。
        """
        settings = self.get_aenet_settings()
        if settings is None:
            raise ValueError(
                "AENET が未設定です。先に set_aenet_potential() を実行してください。"
            )

        atom_type_value = self._validate_positive_atom_type(
            atom_type,
            "AENET atom_type",
        )

        for item in settings["potentials"]:
            if item["atom_type"] == atom_type_value:
                raise ValueError(
                    "AENET の atom_type は重複指定できません: " f"{atom_type_value}"
                )

        section = self._find_sections("AENET")[0]
        filename_value = str(filename).strip()
        if not filename_value:
            raise ValueError("AENET potential filename は空にできません。")

        tokens = [
            str(atom_type_value),
            filename_value,
        ]
        if type_name is not None:
            type_name_value = str(type_name).strip()
            if not type_name_value:
                raise ValueError("type_name は文字列または None で指定してください。")
            tokens.append(type_name_value)

        section["IND_ANN-FILE_TYPE-NAME"].append(" ".join(tokens))
        self._logger.info(
            "[rmc_pot_dat_free] add_aenet_potential_file: "
            f"atom_type={atom_type_value}"
        )

        if self._resolve_auto_write(auto_write):
            self.write()

    def remove_aenet_potential_file(
        self,
        atom_type: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """指定原子タイプの AENET potential ファイル設定を削除する。

        Args:
            atom_type: 削除する RMC 原子タイプ番号。
            auto_write: 更新後に保存するかどうか。

        Raises:
            ValueError: ``[ AENET ]`` が未設定、対象原子タイプが存在しない、
                または削除により必須設定が空になる場合。
        """
        sections = self._find_sections("AENET")
        if not sections:
            raise ValueError("AENET は設定されていません。")

        section = sections[0]
        values = section.get("IND_ANN-FILE_TYPE-NAME", [])
        atom_type_value = int(atom_type)

        retained_values: List[str] = []
        removed = False
        for value in values:
            tokens = value.split()
            if tokens:
                current_type = int(tokens[0])
                if current_type == atom_type_value:
                    removed = True
                    continue
            retained_values.append(value)

        if not removed:
            raise ValueError(
                "指定した AENET atom_type は存在しません: " f"{atom_type_value}"
            )
        if not retained_values:
            raise ValueError(
                "最後の AENET potential は削除できません。"
                "AENET 全体を削除する場合は clear_aenet_potential() を使用してください。"
            )

        section["IND_ANN-FILE_TYPE-NAME"] = retained_values

        if self._resolve_auto_write(auto_write):
            self.write()

    def clear_aenet_potential(
        self,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """``[ AENET ]`` セクションと ANN potential 設定を削除する。

        Args:
            auto_write: 更新後に保存するかどうか。
        """
        retained_sections: List[Tuple[str, Dict[str, List[str]]]] = []
        for name, values in self._sections:
            if name != "AENET":
                retained_sections.append((name, values))
        self._sections = retained_sections

        self._logger.info("[rmc_pot_dat_free] clear_aenet_potential")

        if self._resolve_auto_write(auto_write):
            self.write()
