#!/usr/bin/env python3
"""RMC_POT 自由形式 ``*.dat`` の読み書き機能。

固定形式版 ``RmcPotDat`` と同じ公開 I/F を維持しながら、内部では
``#002`` または ``#003`` の自由形式セクションとキーを扱う。
物理的な行番号ではなく、互換項目番号を自由形式キーへ対応付ける。
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence

from rmc_dft.config import Config
from x_logger import XLogger


class RmcPotDatFree:
    """固定形式版と同じ公開 I/F で自由形式 ``*.dat`` を扱う。

    Attributes:
        直接公開する属性はない。設定値は既存の getter/setter または
        自由形式固有の ``get()``, ``set()``, ``add()`` を通して操作する。

    Notes:
        固定形式版のメソッド名、引数、戻り値との互換性を維持する。
        一方、ファイル上の実体は ``[ SECTION ]`` と ``KEY = VALUE`` であり、
        固定形式の物理行へは依存しない。
    """

    _FNC_TO_FREE = {
        0: "NONE",
        1: "NORMAL",
        2: "ADJUST",
        3: "MOVE-IN",
        4: "FLEXIBLE",
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
            固定形式版 ``RmcPotDat`` と同じ公開 I/F を維持するため、
            行番号ベースの操作は自由形式のセクション名とキーへ内部変換する。
            既存ファイルがなければ自由形式の初期ファイルを生成して読み込む。
        """
        self._logger = logger or XLogger()
        self._config = config or Config()
        self._cfg_name = cfg_name or self._config.cfg_name
        self._auto_write = auto_write
        self._version = version
        self._sections: List[Tuple[str, Dict[str, List[str]]]] = []
        self._compat_values: Dict[int, str] = {}

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
            固定形式テンプレートの物理的な行配置には依存しない。
        """
        path = Path(f"{basename}.dat")
        if path.exists():
            self._logger.error(f'[rmc_pot_dat_free] "{path}" はすでに存在します')
            return False
        self._sections = [("GENERAL", {})]
        self._set_value("GENERAL", "TITLE", "")
        self._set_value("GENERAL", "NDENS", "0.0915")
        self._set_value("GENERAL", "CUT-OFF", "2.3 2.1 2 2.3 2.1 2")
        self._set_value("GENERAL", "MAX-MOVES", "0.1 0.1 0.1")
        self._set_value("GENERAL", "R-SPACING", "0.025")
        self._set_value("GENERAL", "MOVEOUT", "0")
        self._set_value("GENERAL", "COLL-NUMBER", "0")
        self._set_value("GENERAL", "PRINT-STEP", "5000")
        self._set_value("GENERAL", "RUN-TIME", "0.2")
        self._set_value("GENERAL", "SAVE-TIME", "0")
        self._set_value("GENERAL", "FNC-TYPE", "NONE")
        self._set_value("GENERAL", "BIN-SHIFT", "0")
        self._set_value("GENERAL", "XMAX-FACTOR", "1")
        self._set_value("GENERAL", "HST_BUFFSIZE", "200")
        self._set_value("GENERAL", "HST-STEP-FACTOR", "10")
        self._set_value("GENERAL", "RELOAD", "0")
        self._set_value("GENERAL", "THREADS", "4")
        self._write_path(path)
        return True

    @staticmethod
    def _to_bool_token(v: Union[bool, str]) -> str:
        """真偽入力を固定形式互換の論理トークンへ変換する。

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
            self._logger.info(f"[rmc_pot_dat_free] .dat ファイルが見つかりません: {path}")
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

    def get_line(self, line_no_1based: int) -> str:
        """固定形式互換の項目番号から値を取得する。

        Args:
            line_no_1based: 固定形式版 I/F で使用する 1 始まりの項目番号。

        Returns:
            対応する自由形式キーから復元した文字列。

        Notes:
            実ファイルの物理行を参照するメソッドではない。
            互換項目番号を自由形式セクションへ変換する仮想 I/F である。
        """
        return self._virtual_line(line_no_1based)

    def set_line(
        self,
        line_no_1based: int,
        value: Union[str, int, float, Sequence[Union[int, float]], bool],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """固定形式互換の項目番号を使って自由形式の値を更新する。

        Args:
            line_no_1based: 固定形式版 I/F で使用する 1 始まりの項目番号。
            value: 設定する文字列、数値、真偽値、または数値列。
            auto_write: ``True`` なら更新直後に保存する。``None`` の場合は
                インスタンスの既定値を使用する。

        Notes:
            実ファイルの物理行を書き換えるのではなく、項目番号に対応する
            自由形式のセクションとキーを更新する。
        """
        text = self._coerce_value(value)
        self._apply_virtual_line(line_no_1based, text)
        if auto_write is None:
            do_write = self._auto_write
        else:
            do_write = auto_write
        if do_write:
            self.write()

    def _index(self, line_no_1based: int) -> int:
        """固定形式互換の項目番号を検証して 0 始まりへ変換する。

        Args:
            line_no_1based: 1 から 33 までの互換項目番号。

        Returns:
            0 始まりへ変換した番号。

        Raises:
            IndexError: 指定番号が互換範囲外の場合。
        """
        if line_no_1based < 1 or line_no_1based > 33:
            raise IndexError(f"行番号が範囲外です: {line_no_1based} (全 33 行相当)")
        return line_no_1based - 1

    def _find_sections(self, name: str) -> List[Dict[str, List[str]]]:
        """指定名と一致する全セクションを取得する。

        Args:
            name: 大文字小文字を区別しないセクション名。

        Returns:
            出現順を維持したセクション辞書のリスト。
        """
        upper = name.upper()
        return [values for section_name, values in self._sections if section_name == upper]

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

    def _virtual_line(self, line_no: int) -> str:
        """自由形式データから固定形式互換の項目値を構成する。

        Args:
            line_no: 固定形式版 I/F の 1 始まり項目番号。

        Returns:
            固定形式版 getter が期待する文字列表現。

        Notes:
            ``[ GENERAL ]``、最初の ``[ EXP ]``、制約セクション数、
            potential セクションの有無を対応する互換値へ変換する。
        """
        self._index(line_no)
        general = self._first_section("GENERAL")
        exp = self._first_exp()

        # 固定形式互換 I/F の 11～18 番項目は、最初の [ EXP ] セクションへ対応付ける。
        # [ EXP ] が存在しない場合は、固定形式版と同じ型で既定値を返す。
        if exp:
            exp_datafile = exp.get("DATAFILE", [""])[0]
            exp_point_range = exp.get("POINT-RANGE", [""])[0]
            exp_scale = exp.get("SCALE", ["1"])[0]
            exp_sigma = exp.get("SIGMA", ["1"])[0]
            exp_use_rfactor = self._bool_line(
                exp.get("USE-RFACTOR", ["0"])[0]
            )
            exp_renorm = self._bool_line(
                exp.get("RENORM", ["0"])[0]
            )
            exp_read_coeffs = self._bool_line(
                exp.get("READ-COEFFS", ["0"])[0]
            )
            exp_compton_supr_coeff = self._bool_line(
                exp.get("COMPTON-SUPR-COEFF", ["0"])[0]
            )
        else:
            exp_datafile = ""
            exp_point_range = ""
            exp_scale = "1"
            exp_sigma = "1"
            exp_use_rfactor = ".false."
            exp_renorm = ".false."
            exp_read_coeffs = ".false."
            exp_compton_supr_coeff = ".false."

        # 自由形式では potential の有無をセクションの存在で判断する。
        # 固定形式互換 I/F では従来どおり "0" または "1" を返す。
        has_potential = False
        if self._find_sections("NBPOT"):
            has_potential = True
        if self._find_sections("BPOT"):
            has_potential = True
        if self._find_sections("AENET"):
            has_potential = True

        if has_potential:
            potential_flag = "1"
        else:
            potential_flag = "0"

        mapping = {
            1: self._first_value("GENERAL", "TITLE", ""),
            2: self._first_value("GENERAL", "NDENS", "0"),
            3: self._first_value("GENERAL", "CUT-OFF", ""),
            4: self._first_value("GENERAL", "MAX-MOVES", ""),
            5: self._first_value("GENERAL", "R-SPACING", "0.1"),
            6: self._bool_line(self._first_value("GENERAL", "MOVEOUT", "0")),
            7: self._first_value("GENERAL", "COLL-NUMBER", "0"),
            8: self._first_value("GENERAL", "PRINT-STEP", "10000"),
            9: f'{self._first_value("GENERAL", "RUN-TIME", "300")} {self._first_value("GENERAL", "SAVE-TIME", "2")}',
            10: " ".join(str(value) for value in self._exp_type_counts()),
            11: exp_datafile,
            12: exp_point_range,
            13: exp_scale,
            14: exp_sigma,
            15: exp_use_rfactor,
            16: exp_renorm,
            17: exp_read_coeffs,
            18: exp_compton_supr_coeff,
            19: str(len(self._find_sections("COS"))),
            20: str(len(self._find_sections("COORD"))),
            21: str(len(self._find_sections("AVCOORD"))),
            22: potential_flag,
            23: self._fnc_free_to_fixed(self._first_value("GENERAL", "FNC-TYPE", "NONE")),
            24: self._first_value("GENERAL", "BIN-SHIFT", "0"),
            25: self._first_value("GENERAL", "XMAX-FACTOR", "1"),
            27: self._first_value("GENERAL", "HST_BUFFSIZE", "0"),
            28: self._first_value("GENERAL", "HST-STEP-FACTOR", "1"),
            30: self._first_value("GENERAL", "RELOAD", "0"),
            33: self._first_value("GENERAL", "THREADS", "1"),
        }
        return mapping.get(line_no, self._compat_values.get(line_no, "0"))

    def _apply_virtual_line(self, line_no: int, text: str) -> None:
        """固定形式互換の項目値を自由形式データへ反映する。

        Args:
            line_no: 固定形式版 I/F の 1 始まり項目番号。
            text: 自由形式へ反映する文字列。

        Notes:
            対応する項目はセクションとキーへ変換する。自由形式に直接対応する
            キーがない互換項目は ``_compat_values`` に保持する。
        """
        self._index(line_no)
        if line_no == 1:
            self._set_value("GENERAL", "TITLE", text)
        elif line_no == 2:
            self._set_value("GENERAL", "NDENS", text)
        elif line_no == 3:
            self._set_value("GENERAL", "CUT-OFF", text)
        elif line_no == 4:
            self._set_value("GENERAL", "MAX-MOVES", text)
        elif line_no == 5:
            self._set_value("GENERAL", "R-SPACING", text)
        elif line_no == 6:
            self._set_value("GENERAL", "MOVEOUT", self._bool_int(text))
        elif line_no == 7:
            self._set_value("GENERAL", "COLL-NUMBER", text)
        elif line_no == 8:
            self._set_value("GENERAL", "PRINT-STEP", text)
        elif line_no == 9:
            tokens = text.split()
            self._set_value("GENERAL", "RUN-TIME", tokens[0])
            if len(tokens) > 1:
                self._set_value("GENERAL", "SAVE-TIME", tokens[1])
        elif line_no == 10:
            self._set_exp_flags([int(float(v)) for v in text.split()[:4]])
        elif 11 <= line_no <= 18:
            exp = self._first_exp(create=True)
            key_map = {
                11: "DATAFILE", 12: "POINT-RANGE", 13: "SCALE", 14: "SIGMA",
                15: "USE-RFACTOR", 16: "RENORM", 17: "READ-COEFFS",
                18: "COMPTON-SUPR-COEFF",
            }
            key = key_map[line_no]
            if line_no >= 15:
                text = self._bool_int(text)
            exp[key] = [text]
        elif line_no == 23:
            tokens = text.split()
            if tokens:
                mode = int(float(tokens[0]))
            else:
                mode = 0
            free = self._FNC_TO_FREE.get(mode)
            if free is None:
                raise ValueError(f"未対応の FNC switch です: {mode}")
            value = " ".join([free] + tokens[1:])
            self._set_value("GENERAL", "FNC-TYPE", value)
        elif line_no == 24:
            self._set_value("GENERAL", "BIN-SHIFT", text)
        elif line_no == 25:
            self._set_value("GENERAL", "XMAX-FACTOR", text)
        elif line_no == 27:
            self._set_value("GENERAL", "HST_BUFFSIZE", text)
        elif line_no == 28:
            self._set_value("GENERAL", "HST-STEP-FACTOR", text)
        elif line_no == 30:
            self._set_value("GENERAL", "RELOAD", text)
        elif line_no == 33:
            self._set_value("GENERAL", "THREADS", text)
        else:
            self._compat_values[line_no] = text

    def _set_exp_flags(self, flags: Sequence[int]) -> None:
        """固定形式の実験データフラグを ``[ EXP ]`` 群へ反映する。

        Args:
            flags: ``GR``, ``ND``, ``XRD``, ``EXAFS`` の有効状態を表す整数列。

        Notes:
            有効な種別だけを残し、既存の同種セクションは内容を保持する。
            対象種別が未作成の場合は必要最低限のキーを持つセクションを作成する。
        """
        types = ["GR", "ND", "XRD", "EXAFS"]
        existing = self._find_sections("EXP")
        preserved = []
        for name, values in self._sections:
            if name != "EXP":
                preserved.append((name, values))
        for flag, exp_type in zip(flags, types):
            if not flag:
                continue
            match = None
            for value in existing:
                current_type = value.get("TYPE", [""])[0].upper()
                if current_type == exp_type:
                    match = value
                    break

            if match is None:
                match = {"TYPE": [exp_type], "DATAFILE": [""], "POINT-RANGE": ["1 1"], "SIGMA": ["1"]}
            preserved.append(("EXP", match))
        self._sections = preserved

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
        """自由形式の真偽値を固定形式互換トークンへ変換する。

        Args:
            value: ``0``、``1``、または真偽を表す文字列。

        Returns:
            ``".true."`` または ``".false."``。
        """
        bool_value = RmcPotDatFree._bool_int(value)
        if bool_value == "1":
            return ".true."
        return ".false."

    def _fnc_free_to_fixed(self, value: str) -> str:
        """自由形式の ``FNC-TYPE`` を固定形式互換表現へ変換する。

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

    def get(self, section: str, key: str, index: int = 0, default: Optional[str] = None) -> Optional[str]:
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

    def add_section(self, section: str) -> int:
        """空の自由形式セクションを末尾へ追加する。

        Args:
            section: 追加するセクション名。

        Returns:
            追加した同名セクションの 0 始まり位置。
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
        """1 行目 comment を str で返す。"""
        return str(self.get_line(1).split()[0])

    def set_comment(
        self,
        comment: str,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """1 行目 comment を更新。"""
        self._logger.info(f"[rmc_pot_dat_free] set_comment = {comment}")
        self._config.rmc_comment = comment
        self.set_line(1, comment, auto_write=auto_write)

    def get_density(self) -> float:
        """
        2 行目 density を float で返す。

        Notes:
            例)
            0.0842566414       ! number densit

            - 系の数密度（number density） 単位は原子数 / Å^3。
            - cfg ファイル中の原子数とシミュレーションボックス体積の
              関係で一致させる必要がある（二重定義）
        """
        # return float(self.get_line(2).split()[0])
        try:
            return float(self.get_line(2).split()[0])

        except (IndexError, ValueError):
            if self._config.number_density_A3 is not None:
                return float(self._config.number_density_A3)

            raise ValueError(
                "number density が未設定です。"
                " .dat の 2 行目にもなく、config.number_density_A3 も None です。"
            )

    def set_density(
        self,
        rho: Union[int, float],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """2 行目 density を更新。"""
        self._logger.info(f"[rmc_pot_dat_free] set_density = {rho}")
        self._config.number_density_A3 = float(rho)
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
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        3 行目 cut offs を更新。可変長対応。
        それ以上原子同士が近づかない距離

        Notes:
            Fe Si B の３つのときは 6つのパターンが生まれる

            Fe–Fe
            Fe–Si
            Fe–B
            Si–Si
            Si–B
            B–B

            6つが必要

            cutoff の与え方（固定フォーマット版 RMC_POT の厳密仕様）:

                cutoff は「原子種の組み合わせごと」に 1 つずつ値を並べる。
                原子種数を ntypes とすると、必要となる cutoff の数は

                    ntypes * (ntypes + 1) / 2

                である。

                並べる順序は RMC_POT 固定フォーマットの既定順で、以下のように
                “11, 12, 13, …, 22, 23, …, 33, …” のような三角行列形式で並べる。

            例1:
                3 元系（Fe, Si, B）の場合（ntypes = 3）

                必要な cutoff は 6 個：
                    11, 12, 13, 22, 23, 33

                set_cutoffs へ渡すリストは次のように 6 要素で指定する：

                    set_cutoffs([c11, c12, c13, c22, c23, c33])

                実際の実行例：

                    set_cutoffs([2.3, 2.1, 2.0, 2.3, 2.1, 2.0])

            例2:
                2 元系（A, B）の場合（ntypes = 2）

                必要な cutoff は 3 個：
                    11, 12, 22

                set_cutoffs([c11, c12, c22])

            注意:
                - cutoff の個数は必ず ntypes*(ntypes+1)/2 と一致させること。
                - 固定フォーマット版 RMC_POT ではこの並びと個数が崩れると、
                  直後の行（maximum moves 等）の読み込み位置がずれ、実行時エラーになる。
                - 可変長の free-format (#003) ではこの限りではないが、
                  本クラスは固定フォーマット互換を前提としている。

        Args:
            values (Sequence[Union[int|float]]):
                上記の定義に従い、原子種組み合わせごとの cutoff を並べたリスト。
                原子種ごとのカットオフ距離リストを指定する。
                要素数は ntypes に応じて可変（3 要素に限定しない）

            auto_write (bool | None):
                True の場合は即時書き出し。None はインスタンス既定値に従う。
        """
        seq = list(values)
        self._logger.info(f"[rmc_pot_dat_free] set_cutoffs = {seq}")
        for v in seq:
            if not isinstance(v, (int, float)):
                raise TypeError(f"cut offs には数値のみを指定してください: {v!r}")

        self._config.rmc_cutoffs = seq

        # set_line はコメントを保持したまま値部を置換する
        self.set_line(3, seq, auto_write=auto_write)

    def get_max_moves(self) -> Tuple[float, float]:
        """
        4 行目 maximum moves を (m1, m2) で返す。

        Notes:
            例)
            0.01 0.01 0.01   ! maximum moves

            - 説明: 原子移動の最大振幅（1 回の move での最大変位）を指定します。複数値が並んでいる場合はタイプごと、
                   または移動タイプごとの設定になっていることがある。単位は Å。
            - 備考: 値が小さいほど受理率が高くなるがサンプリング効率は落ちます
                   調整して受理率を 20–50% 程度に保つのが一般的
        """
        toks = self.get_line(4).split()
        if len(toks) < 2:
            raise ValueError(f"maximum moves 行の要素数が不足: {toks!r}")
        return float(toks[0]), float(toks[1])

    def set_maximum_moves(
        self,
        values: Sequence[Union[int, float]],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        4 行目 maximum moves を可変長で更新する。

        Args:
            values (Sequence[Union[int, float]]):
                任意個数の maximum move 値。順序はそのまま書き込み。

            auto_write (bool | None):
                True の場合即時保存。None の場合はインスタンス既定に従う。
        """
        seq = list(values)
        self._logger.info(f"[rmc_pot_dat_free] set_maximu_moves = {seq}")

        # 各要素が数値であることのみ検査する
        for v in seq:
            if not isinstance(v, (int, float)):
                raise ValueError(f"maximum moves には数値のみ指定してください: {v!r}")

        self._config.rmc_max_moves = seq

        # 4 行目へそのまま書き込む
        self.set_line(4, seq, auto_write=auto_write)

    def get_r_spacing(self) -> float:
        """
        5 行目 r spacing を float で返す。i
        近接分布関数 g(r) のビン幅（r の刻み幅）。単位は Å。
        RMC の g(r) や部分 g(r) を計算する際、距離 r の空間を等間隔に区切ってヒストグラムを作成します。
        この ビン間隔（dr） を指定するのが R-SPACING

        Notes:
            例:
                0.025        ! r spacing

                - 備考: 小さいほど解像度は上がるが計算負荷が増える
        """
        try:
            toks = self.get_line(5).split()
            if toks:
                return float(toks[0])
        except (IndexError, ValueError):
            pass

        if self._config.rmc_r_spacing is not None:
            return float(self._config.rmc_r_spacing)

        raise ValueError(
            "r spacing が未設定です。"
            " .dat の 5 行目にもなく、config.rmc_r_spacing も None です。"
        )

    def set_r_spacing(
        self,
        dr: Union[int, float],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """5 行目 r spacing を更新。"""
        self._logger.info(f"[rmc_pot_dat_free] set_r_spacing = {dr}")
        self._config.rmc_r_spacing = float(dr)
        self.set_line(5, dr, auto_write=auto_write)

    def get_moveout_option(self) -> bool:
        """
        6 行目（whether to use moveout option）を取得する。

        Notes:
            内容:
                - RMC 計算において「moveout オプション」を使用するかどうかを指定するブール値。
                  moveout オプションは、原子のランダム移動試行時に追加的な処理を行う機能であり、
                  一般的には「移動後の局所最適化」や「過大な変位の制限」を目的とする

            マニュアル定義:
                - ラベル: “whether to use moveout option”
                - 型: 論理値（.true. / .false.）
                - 意味:
                    - .true.  : moveout 処理を有効化。
                                → 原子移動試行のたびに補助的な判定・制約が加わる。
                    - .false. : moveout 処理を無効化。
                                → 通常の RMC 移動アルゴリズムを使用。
                - 挙動の詳細は実装依存（例: moveout モジュール内で距離閾値チェックを行うなど）。

            例:
                .true.   ! whether to use moveout option
                    → moveout 処理を有効化（制約付き移動を実施）。
                .false.  ! whether to use moveout option
                    → 通常のランダム移動。

        Returns:
            bool: moveout オプションを有効化している場合は True、無効なら False。
        """
        try:
            token = self.get_line(6).strip().lower()
            if token in (".true.", "true", "t", "1", "yes", "y"):
                return True
            if token in (".false.", "false", "f", "0", "no", "n"):
                return False
        except IndexError:
            pass

        if self._config.rmc_moveout_option is not None:
            return bool(self._config.rmc_moveout_option)

        raise ValueError(
            "moveout option が未設定です。"
            " .dat の 6 行目にもなく、config.rmc_moveout_option も None です。"
        )

    def set_moveout_option(
        self,
        use_moveout: bool,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        6 行目（whether to use moveout option）を更新する。

        Notes:
            内容:
                - moveout オプションを有効化するかどうかを設定する。
                  moveout は RMC における原子移動の特殊処理オプションであり、
                  一般には「移動後の拘束条件」「局所最適化ステップ」「排他領域判定」などを伴う。

            指定方法:
                - True  → .true. を書き込み、有効化。
                - False → .false. を書き込み、無効化。

            例:
                set_moveout_option(True)
                    → moveout 処理を有効にする。
                set_moveout_option(False)
                    → moveout 処理を無効にする。

        Args:
            use_moveout (bool):
                moveout オプションを有効化する場合は True、無効化する場合は False。
            auto_write (bool | None):
                True なら即時保存、None の場合はインスタンス既定に従う。
        """
        token = self._to_bool_token(use_moveout)
        self._logger.info(f"[rmc_pot_dat_free] set_moveout_option = {token}")
        self._config.rmc_moveout_option = bool(use_moveout)
        self.set_line(6, token, auto_write=auto_write)

    def get_num_config_to_collect(self) -> int:
        """
        7 行目（number of configuration to collect）を取得する。

        Notes:
            内容:
                - RMC 実行中に「構成（configuration）」をどの程度の頻度で収集するかを指定する。
                  ここでいう configuration とは、特定ステップ時点の原子配置を指す。
                  解析や平均化、統計処理に利用するため、指定回数ぶんを記録できる。

            マニュアル定義:
                - ラベル: “number of configuration to collect”
                - 単位: 個数（整数）
                - 意味:
                    RMC 計算中に「収集用構成」を保存する数。
                    この値が 0 の場合、多くの実装では「構成を収集しない」または
                    「最終構成のみを保存」として扱われる。

            典型的な設定例:
                0     ! number of configuration to collect
                    → 構成を収集せず、最終結果のみを出力。
                10    ! number of configuration to collect
                    → 全実行中に 10 構成を等間隔で保存。
                100   ! number of configuration to collect
                    → 100 構成を収集（より細かい統計解析に利用）。

            備考:
                - 保存間隔は RMC_POT 内部で自動的に均等分配される。
                - このパラメータは出力用ヒストグラムや g(r) 平均化などに影響を与える。

        Returns:
            int: 収集する構成数。
        """
        tokens = self.get_line(7).split()
        if not tokens:
            raise ValueError("7 行目が空です。")
        try:
            return int(float(tokens[0]))
        except ValueError as exc:
            raise ValueError(f"7 行目に整数以外の値があります: {tokens!r}") from exc

    def set_num_config_to_collect(
        self,
        num_config: int,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        7 行目（number of configuration to collect）を更新する。

        Notes:
            内容:
                - RMC 実行中にどのくらいの頻度で「構成（configuration）」を保存するかを指定する。
                  これは構造平均化や g(r) 平均などの統計解析に使う複数構成を得るための設定。

            指定方法:
                - 0 の場合:
                    → 構成を収集しないか、最終構成のみを保存。
                - 正の整数値:
                    → 指定数の構成を収集。
                      RMC_POT はシミュレーション全体を等間隔に分割して収集ステップを決定する。

            例:
                set_num_config_to_collect(0)
                    → 収集しない（最終構成のみ）。
                set_num_config_to_collect(20)
                    → 全体で 20 構成を等間隔で保存。

        Args:
            num_config (int):
                収集する構成数（0 以上の整数）
            auto_write (bool | None):
                True の場合は即時保存。None の場合はインスタンス既定に従う。
        """
        if num_config < 0:
            raise ValueError(f"num_config は 0 以上を指定してください: {num_config}")

        self.set_line(7, str(int(num_config)), auto_write=auto_write)

    def get_print_interval(self) -> int:
        """
        8 行目（step for printing）を取得する。

        Notes:
            内容:
                - RMC_POT の計算進行中、標準出力やログファイルに
                  エネルギー・受理率・コスト関数などの経過情報を
                  どの間隔で出力するかを指定するステップ数。

            マニュアル定義:
                - ラベル: “step for printing”
                - 意味: RMC の実行ループ中で何ステップごとに
                        計算状況（χ²値、受理率、平均変位など）を表示するか。
                - 値の単位: ステップ数（整数）
                - 0 または負値: 無効（出力を行わない、もしくは既定間隔を使用）

            例:
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
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        8 行目（step for printing）を更新する。

        Notes:
            内容:
                - 計算経過を標準出力やログに記録する間隔を指定する。
                  値は「ステップ数」で指定し、0 の場合は無効または既定値使用。

            例:
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

    def get_time_and_save(self) -> Tuple[float, int]:
        """
        9 行目（time limit, step for saving）を取得する。

        Notes:
            内容:
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

            例:
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
        save_interval_step: float,
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        9 行目（time limit, step for saving）を更新する。

        Notes:
            内容:
                - time limit:
                    計算の最大実行時間（分単位, float）。
                    0 の場合は時間制限なし。
                - step for saving:
                    結果ファイルを出力するステップ間隔（整数ステップ）。
                    0 の場合は自動保存を無効化。

            例:
                (60, 1000)
                → 最大 60 分で停止、1000 ステップごとに結果保存。
                (0, 0)
                → 両方無効化（時間制限も保存間隔も設定しない）。

        Args:
            time_limit_min (float): 最大実行時間（単位: 分）
            save_interval_step (float): 保存ステップ時間
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

        values = [self._fmt_number(time_limit_min), str(float(save_interval_step))]
        self._config.rmc_time_and_save = (
            float(time_limit_min),
            int(save_interval_step),
        )
        self.set_line(9, values, auto_write=auto_write)

    def get_data_flags(self) -> Tuple[int, int, int, int]:
        """
        10 行目（g(r), neutron, x-ray, EXAFS の出力フラグ）を取得する。

        Notes:
            各整数は、その物理量の計算・出力を行うかどうかを指定する。

            順序は常に以下で固定される（RMC_POT マニュアル II.E 節より）:
                1. g(r) の計算フラグ
                2. neutron S(Q) の計算フラグ
                3. X-ray F(Q) の計算フラグ
                4. EXAFS χ(k) の計算フラグ

            仕様:
                - 0: 無効（そのデータ種を出力・比較しない）
                - 1: 有効（そのデータ種を出力・比較する）

            例:
                0 0 1 0  ! g(r), neutron, x-ray, EXAFS
                → g(r)=0, neutron=0, x-ray=1, EXAFS=0
                → X線データのみ出力・比較対象とする設定。

        Returns:
            tuple[int, int, int, int]:
                (gr_flag, neutron_flag, xray_flag, exafs_flag)
        """
        try:
            tokens = self.get_line(10).split()
            if len(tokens) >= 4:
                return tuple(int(v) for v in tokens[:4])  # type: ignore[return-value]
        except (IndexError, ValueError):
            pass

        if self._config.rmc_data_flags is not None:
            return tuple(int(v) for v in self._config.rmc_data_flags[:4])  # type: ignore[return-value]

        raise ValueError(
            "data flags が未設定です。"
            " .dat の 10 行目にもなく、config.rmc_data_flags も None です。"
        )

    def set_data_flags(
        self,
        flags: Sequence[int],
        *,
        auto_write: Optional[bool] = True,
    ) -> None:
        """
        10 行目（g(r), neutron, x-ray, EXAFS の出力フラグ）を更新する。

        Notes:
            内容:
                - 10 行目は、4 つの整数値で各データ種の出力可否を指定する。
                  順序は固定:
                    (1) g(r)
                    (2) neutron S(Q)
                    (3) X-ray F(Q)
                    (4) EXAFS χ(k)
                - 各値の意味:
                    0: 無効（出力・比較を行わない）
                    1: 有効（出力・比較を行う）

            例:
                (0, 0, 1, 0)
                [0, 0, 1, 0]
                → g(r)=off, neutron=off, X-ray=on, EXAFS=off
                  → X線 F(Q) のみを比較対象に設定。

        Args:
            flags (Sequence[int]):
                (gr_flag, neutron_flag, xray_flag, exafs_flag) を表す長さ 4 の列。
                tuple でも list でもよい。
            auto_write (bool | None):
                True なら即時保存。None の場合はインスタンス既定に従う。
        """
        values = list(flags)

        if len(values) != 4:
            raise ValueError(
                f"flags は 4 要素 (g(r), neutron, x-ray, EXAFS) が必要です: {values!r}"
            )
        if not all(isinstance(v, int) and v in (0, 1) for v in values):
            raise ValueError(f"flags には 0 または 1 のみ指定可能です: {values!r}")

        self._logger.info(f"[rmc_pot_dat_free] flags: {values!r}")
        self._config.rmc_data_flags = values
        self.set_line(10, [str(v) for v in values], auto_write=auto_write)

    def get_exp_filename(self) -> str:
        """
        11 行目（実験データファイル名）を返す（旧来固定フォーマット）。

        Notes:
            - .dat ファイルの 10 行目には、
              g(r), neutron S(Q), X-ray F(Q), EXAFS χ(k) の順に
              4 つの整数が並びます。これらは各データ種のブロック数を表し、
              0 は「そのデータ種のブロックが無い」ことを意味します。

            - 11 行目以降には、ブロック数が 1 以上のデータ種だけが
              上記の順番で並びます。各データ種について 2 行が 1 ブロックで、
              1 行目が実験データファイル名、
              2 行目が使用点範囲（開始・終了の 2 整数）です。

            - このメソッドは、そのうち最初のブロック（= 11 行目）に書かれている
              実験データファイル名だけを返します。
              例えば 10 行目が ``0 0 1 0`` の場合、11 行目は X-ray F(Q) 用の
              実験データファイル名になります。

            - 実験データファイル（.dat が参照する外部ファイル）のフォーマットは
              次のように固定されています。
              1 行目: データ点数 N（整数）
              2 行目: タイトル行（任意文字列）
              3 行目以降: データ点列

            - データ点列の列構成はデータ種ごとに次のようになります。
              g(r)        : r, g(r)（2 列）
              neutron S(Q): Q, S(Q)（2 列）
              X-ray F(Q)  : Q, F(Q), c_αβ が M 本（2+M 列）
              EXAFS χ(k)  : k, χ(k)（2 列）

            - X-ray F(Q) の場合、c_αβ の本数 M は
              ``M = ntypes * (ntypes + 1) / 2`` で決まります。
              c_αβ の並び順（いわゆる RMC 順）は
              11, 12, 13, …, 22, 23, …, 33 のような上三角の順序です。

            - 典型的な列構成の例として、
              5 列のファイルは 2 元系（Q, F(Q), c11, c12, c22）、
              8 列のファイルは 3 元系（Q, F(Q), c11, c12, c13, c22, c23, c33）
              に対応します。
        """
        try:
            line = self.get_line(11)
            self._logger.info(f'[rmc_pot_dat_free] == get_exp_filename: "{line}"')
            tokens = line.split()
            if tokens:
                return tokens[0]
        except IndexError:
            pass

        if self._config.rmc_exp_filename is not None:
            self._logger.info(
                f'[rmc_pot_dat_free] == get_exp_filename(from config): "{self._config.rmc_exp_filename}"'
            )
            return self._config.rmc_exp_filename

        raise ValueError(
            "実験データファイル名が未設定です。"
            " .dat の 11 行目にもなく、config.rmc_exp_filename も None です。"
        )

    def set_exp_filename(
        self,
        path: Union[str, Path],
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        11 行目（実験データファイル名）を更新する（旧来固定フォーマット）。

        Notes:
            .dat 側の決まり（旧来固定）:
                - 10 行目の順序は常に:
                    g(r), neutron S(Q), X-ray F(Q), EXAFS χ(k)
                - 11 行目は、上記で有効な最初のブロックが X-ray の場合には
                  その「ファイル名行」となる（例: `0 0 1 0`）。
                  本メソッドは **11 行目のみ** を対象として文字列を書き換える。

            実験データファイルの中身（確認用の定義）
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
        self._config.rmc_exp_filename = str(Path(path))
        self.set_line(11, str(Path(path)), auto_write=auto_write)

    def get_exp_range(self) -> Tuple[int, int]:
        """
        12 行目（実験データの読み込み範囲）を取得する。

        Notes:
            - 旧来固定フォーマットでは、
              11 行目が実験データファイル名、
              12 行目が読み込み範囲を表す 2 つの整数になっています。

            - 12 行目の 2 つの整数は、
              「開始インデックス」と「終了インデックス」を 1 始まり（inclusive）で指定します。
              対象は実験データファイルの「データ本体行」であり、
              1 行目の点数 N、2 行目のタイトル行は含みません。

            - 範囲指定の例:
              ``1 290`` → データ本体の 1〜290 行を利用
              ``1 991`` → データ本体の 1〜991 行を利用
                          （実データ点数 N を超える指定は推奨されません）

            - 終了インデックスが実データ点数 N を超えた場合の挙動は
              RMC_POT の版に依存する可能性があります。
              このメソッド自身は読み取りのみを行い、範囲の検査や補正は行いません。
        """
        try:
            toks = self.get_line(12).split()
            # 12 行目は 2 つの整数のみである必要
            if len(toks) == 2:
                start = int(float(toks[0]))
                end = int(float(toks[1]))
                if start >= 1 and end >= start:
                    return start, end

        except (IndexError, ValueError):
            pass

        if self._config.rmc_exp_range is not None:
            return (
                int(self._config.rmc_exp_range[0]),
                int(self._config.rmc_exp_range[1]),
            )

        raise ValueError(
            "実験データ範囲が未設定です。"
            " .dat の 12 行目にもなく、config.rmc_exp_range も None です。"
        )

    def set_exp_range(
        self,
        start: int,
        end: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        12 行目（実験データの読み込み範囲）を更新する。

        Notes:
            【書式（旧来固定フォーマット）】
            - 2 整数のみ（1 始まり・inclusive）
              ・start: 開始インデックス（>=1）
              ・end  : 終了インデックス（>= start）

            【推奨運用】
            - 実験データファイル 1 行目の点数 N を参照し、end を N 以下に揃えること。

        Args:
            start (int): 1 始まりの開始行（inclusive, >=1）
            end (int):   1 始まりの終了行（inclusive, >=start）
            auto_write (bool | None): True で即時保存。None はインスタンス既定に従う。
        """
        if start < 1 or end < start:
            raise ValueError(f"範囲が不正です: start={start}, end={end}")

        # 厳密に「2 トークンのみ」を書き込む
        self._config.rmc_exp_range = (int(start), int(end))
        self.set_line(12, f"{int(start)} {int(end)}", auto_write=auto_write)

    def get_scale_factor(self) -> float:
        """
        13 行目（scale factor）を取得する。

        Notes:
            - 実験 S(Q) や F(Q) に対してスケールを合わせるための係数。
              シミュレーション出力を実験データと正規化するために使用される。
            - 一般的な初期値は 1.0。

        Returns:
            float: スケーリング因子。
        """
        return float(self.get_line(13).split()[0])

    def set_scale_factor(
        self,
        value: float,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        13 行目（scale factor）を設定する。

        Args:
            value (float): スケーリング因子。
            auto_write (bool | None): True で即時保存。
        """
        self.set_line(13, self._fmt_number(value), auto_write=auto_write)

    def get_sigma_factor(self) -> float:
        """
        14 行目（standard deviation / temperature factor）を取得する。

        Notes:
            - メトロポリス法で使用する標準偏差 σ（温度因子）を表す。
            - マニュアルでは “standard deviation” と記載されており、
              サンプルでは「5E-3 0」や「5E-3 1」のように 2 つの値を取る場合がある。
              ここでは先頭値 σ のみを返す。

        Returns:
            float: 標準偏差（σ）。
        """
        try:
            toks = self.get_line(14).split()
            if toks:
                return float(toks[0])
        except (IndexError, ValueError):
            pass

        if self._config.rmc_sigma_factor is not None:
            return float(self._config.rmc_sigma_factor)

        raise ValueError(
            "sigma factor が未設定です。"
            " .dat の 14 行目にもなく、config.rmc_sigma_factor も None です。"
        )

    def set_sigma_factor(
        self,
        sigma: float,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """
        14 行目（standard deviation / temperature factor）を設定する。

        Args:
            sigma (float): 標準偏差（σ）。
            auto_write (bool | None): True で即時保存。
        """
        self._config.rmc_sigma_factor = float(sigma)
        self.set_line(14, self._fmt_number(sigma), auto_write=auto_write)

    def get_flag_15(self) -> bool:
        """
        15 行目（boolean flag 1）を取得する。

        Notes:
            - ブール値 (.true./.false.)。
              通常は S(Q) のバックグラウンド補正や平滑化の有無を指定する。

        Returns:
            bool: True の場合は有効化。
        """
        return self.get_line(15).strip().lower().startswith(".t")

    def set_flag_15(
        self,
        value: bool,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """15 行目（boolean flag 1）を設定する。"""
        self.set_line(15, self._to_bool_token(value), auto_write=auto_write)

    def get_flag_16(self) -> bool:
        """
        16 行目（boolean flag 2）を取得する。

        Notes:
            - ブール値 (.true./.false.)。
              データ重み付けを行うかどうかを示すことが多い。

        Returns:
            bool: True の場合は有効化。
        """
        return self.get_line(16).strip().lower().startswith(".t")

    def set_flag_16(
        self,
        value: bool,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """16 行目（boolean flag 2）を設定する。"""
        self.set_line(16, self._to_bool_token(value), auto_write=auto_write)

    def get_flag_17(self) -> bool:
        """
        17 行目（boolean flag 3）を取得する。

        Notes:
            - ブール値 (.true./.false.)。
              追加オプション（誤差正規化・スムージングなど）を制御する場合がある。

        Returns:
            bool: True の場合は有効化。
        """
        return self.get_line(17).strip().lower().startswith(".t")

    def set_flag_17(
        self,
        value: bool,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """17 行目（boolean flag 3）を設定する。"""
        self.set_line(17, self._to_bool_token(value), auto_write=auto_write)

    def get_flag_18(self) -> bool:
        """
        18 行目（boolean flag 4）を取得する。

        Notes:
            - ブール値 (.true./.false.)。
              一般的に、データ処理や誤差解析の補助機能をオン/オフする。

        Returns:
            bool: True の場合は有効化。
        """
        return self.get_line(18).strip().lower().startswith(".t")

    def set_flag_18(
        self,
        value: bool,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """18 行目（boolean flag 4）を設定する。"""
        self.set_line(18, self._to_bool_token(value), auto_write=auto_write)

    def get_angle_constraint_count(self) -> int:
        """
        19 行目（number of cos. distr of bond angles constraint）を取得する。

        Notes:
            - ボンド角度分布に基づく制約数。
              0 の場合、角度分布制約を適用しない。

        Returns:
            int: 角度制約数。
        """
        return int(float(self.get_line(19).split()[0]))

    def set_angle_constraint_count(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """19 行目（角度制約数）を設定する。"""
        self.set_line(19, str(int(value)), auto_write=auto_write)

    def get_coord_constraint_count(self) -> int:
        """
        20 行目（number of coordination constraints）を取得する。

        Note:
            - 配位数に基づく制約の数。
              0 の場合は適用しない。

        Returns:
            int: 配位数制約の数。
        """
        return int(float(self.get_line(20).split()[0]))

    def set_coord_constraint_count(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """20 行目（配位数制約数）を設定する。"""
        self.set_line(20, str(int(value)), auto_write=auto_write)

    def get_avg_coord_constraint_count(self) -> int:
        """
        21 行目（number of average coordination constraints）を取得する。

        Note:
            - 平均配位数に関する制約数。
              0 の場合は制約なし。

        Returns:
            int: 平均配位数制約の数。
        """
        return int(float(self.get_line(21).split()[0]))

    def set_avg_coord_constraint_count(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """21 行目（平均配位数制約数）を設定する。"""
        self.set_line(21, str(int(value)), auto_write=auto_write)

    def get_potential_flag(self) -> int:
        """
        22 行目（potential flag）を取得する。

        Note:
            - ポテンシャル使用のフラグまたは選択番号。
              0 の場合はポテンシャル未使用。

        Returns:
            int: ポテンシャルフラグ。
        """
        return int(float(self.get_line(22).split()[0]))

    def set_potential_flag(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """22 行目（ポテンシャルフラグ）を設定する。"""
        self.set_line(22, str(int(value)), auto_write=auto_write)

    def get_fnc_switch(self) -> int:
        """
        23 行目（FNC switch）の先頭番号を取得する。

        Note:
            - 0: FNC なし
            - 1: 通常 FNC。初期構造が FNC 距離範囲内にあることを要求する。
            - 2: FNC 距離範囲を初期構造に合わせて調整して開始する。
            - 3: 範囲外ペアを許して開始し、範囲内へ近づく move を受理する。
            - 4: flexible molecule / bonded potential。通常 FNC ではなく topology を使う。

        Returns:
            int: FNC switch の先頭番号。
        """
        return int(float(self.get_line(23).split()[0]))

    def get_fnc_options(self) -> List[str]:
        """
        23 行目（FNC switch）の先頭番号以降のオプションを取得する。

        Returns:
            List[str]: 例: ["-D_FF_OPLS", "-D_FLEX", "-DORI_ANGLE"]
        """
        toks = self.get_line(23).split()
        return toks[1:]

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
        """
        23 行目（FNC switch）を設定する。

        Args:
            value: True/False または RMC_POT の FNC switch 番号。
                True は 1、False は 0 に変換する。
                int を渡した場合は、その番号指定を最優先する。
            opt: FNC switch 番号の後ろに付ける追加オプション。
                例: "-D_FF_OPLS -D_FLEX -DORI_ANGLE -DORI_BOND"
            keep_existing_opt: opt が None の場合に、既存行の追加オプションを保持する。
                ただし value が bool の場合は通常の有効/無効操作なので保持しない。
            auto_write: True 指定で即時保存。None の場合はインスタンス既定に従う。

        Examples:
            set_fnc_switch(True)
                -> "1"
            set_fnc_switch(False)
                -> "0"
            set_fnc_switch(3)
                -> "3"
            set_fnc_switch(4, opt="-D_FF_OPLS -D_FLEX -DORI_ANGLE -DORI_BOND")
                -> "4 -D_FF_OPLS -D_FLEX -DORI_ANGLE -DORI_BOND"
        """
        is_bool_input = isinstance(value, bool)
        mode = self._coerce_fnc_switch_value(value)

        if opt is not None:
            options = self._coerce_fnc_options(opt)
        elif keep_existing_opt and not is_bool_input:
            options = self.get_fnc_options()
        else:
            options = []

        tokens = [str(mode)] + options
        self.set_line(23, " ".join(tokens), auto_write=auto_write)

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
        """
        24 行目（initial bin shift）を取得する。

        Note:
            - g(r) 等のヒストグラム初期シフト値。
              0 はシフトなし。

        Returns:
            int: 初期ビンシフト。
        """
        return int(float(self.get_line(24).split()[0]))

    def set_initial_bin_shift(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """24 行目（initial bin shift）を設定する。"""
        self.set_line(24, str(int(value)), auto_write=auto_write)

    def get_xmax_used(self) -> float:
        """
        25 行目（xmax used in the run）を取得する。

        Note:
            - g(r) 等の計算に用いる最大 r 値。
              スケール因子的に使われることもある。

        Returns:
            float: xmax の値。
        """
        return float(self.get_line(25).split()[0])

    def set_xmax_used(
        self,
        value: float,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """25 行目（xmax used in the run）を設定する。"""
        self.set_line(25, self._fmt_number(value), auto_write=auto_write)

    def get_num_atoms_per_move(self) -> int:
        """
        26 行目（number of atoms moved in a single move）を取得する。

        Note:
            - 1 回の move 操作で同時に動かす原子の数。
              通常は 1。

        Returns:
            int: 移動させる原子数。
        """
        try:
            return int(float(self.get_line(26).split()[0]))

        except (IndexError, ValueError):
            if self._config.rmc_num_atoms_per_move is not None:
                return int(self._config.rmc_num_atoms_per_move)

            raise ValueError(
                "num_atoms_per_move が未設定です。"
                " .dat の 26 行目にもなく、config.rmc_num_atoms_per_move も None です。"
            )

    def set_num_atoms_per_move(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """26 行目（number of atoms moved）を設定する。"""
        self._config.rmc_num_atoms_per_move = int(value)
        self.set_line(26, str(int(value)), auto_write=auto_write)

    def get_history_buffer_size(self) -> int:
        """
        27 行目（size of the history buffer）を取得する。

        Note:
            - 受理率など過去情報を保持する履歴バッファサイズ。
              統計の平滑化に使用される。

        Returns:
            int: バッファサイズ。
        """
        return int(float(self.get_line(27).split()[0]))

    def set_history_buffer_size(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """27 行目（history buffer size）を設定する。"""
        self.set_line(27, str(int(value)), auto_write=auto_write)

    def get_display_update_interval(self) -> int:
        """
        28 行目（number of display update between each history buffering）を取得する。

        Returns:
            int: 表示更新の間隔。
        """
        return int(float(self.get_line(28).split()[0]))

    def set_display_update_interval(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """28 行目（display update interval）を設定する。"""
        self.set_line(28, str(int(value)), auto_write=auto_write)

    def get_custom_move_flag(self) -> int:
        """
        29 行目（indicator of custom move）を取得する。

        Returns:
            int: カスタムムーブ使用フラグ（0/1）。
        """
        return int(float(self.get_line(29).split()[0]))

    def set_custom_move_flag(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """29 行目（custom move flag）を設定する。"""
        self.set_line(29, str(int(value)), auto_write=auto_write)

    def get_load_histogram_flag(self) -> int:
        """
        30 行目（whether to load the histogram from file）を取得する。

        Returns:
            int: 0 ならロードしない、1 ならロードする。
        """
        return int(float(self.get_line(30).split()[0]))

    def set_load_histogram_flag(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """30 行目（load histogram flag）を設定する。"""
        self.set_line(30, str(int(value)), auto_write=auto_write)

    def get_max_atoms_per_cell(self) -> int:
        """
        31 行目（maximum number of atoms in a gridcell）を取得する。

        Returns:
            int: グリッドセル内最大原子数。
        """
        return int(float(self.get_line(31).split()[0]))

    def set_max_atoms_per_cell(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """31 行目（max atoms per gridcell）を設定する。"""
        self.set_line(31, str(int(value)), auto_write=auto_write)

    def get_swap_settings(self) -> Tuple[int, int]:
        """
        32 行目（fraction of swaps, allow flag）を取得する。

        Returns:
            tuple[int, int]: (swap_fraction, allow_flag)
        """
        toks = self.get_line(32).split()
        if len(toks) < 2:
            raise ValueError("32 行目は 2 つの整数が必要です。")
        return int(float(toks[0])), int(float(toks[1]))

    def set_swap_settings(
        self,
        fraction: int,
        allow_flag: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """32 行目（swap fraction と許可フラグ）を設定する。"""
        self.set_line(32, f"{int(fraction)} {int(allow_flag)}", auto_write=auto_write)

    def get_thread_count(self) -> int:
        """
        33 行目（total number of threads to use）を取得する。

        Returns:
            int: 使用スレッド数。
        """
        return int(float(self.get_line(33).split()[0]))

    def set_thread_count(
        self,
        value: int,
        *,
        auto_write: Optional[bool] = None,
    ) -> None:
        """33 行目（スレッド数）を設定する。"""
        self.set_line(33, str(int(value)), auto_write=auto_write)

RmcPotDatFree = RmcPotDat
