#!/usr/bin/env python
"""
K.NAKADA, Kengo.nakada@gmail.com
K.KOBAYASHI
"""
import os
import sys
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import subprocess
import shutil

from rmc_dft.config import Config
from rmc_dft.rmc_pot.rmc_pot_dat import RmcPotDat
from rmc_dft.rmc_pot.rmc_pot_log import RmcPotLog

from rmc_dft.rmc_pot.util.cfg2poscar import cfg2poscar
from rmc_dft.util import ensure_vasp5_format

from x_logger import XLogger


class RmcPot:
    """
    Utility class for managing and running local RMC commands.
    And parsing configuration files.
    """

    def __init__(
        self,
        *,
        rmc_log: Optional[RmcPotLog] = None,  # instance
        rmc_dat: Optional[RmcPotDat] = None,  # instance
        config: Optional[Config] = None,  # Config(),  # instance
        cfg_name: Optional[str] = None,
        use_free_format: bool = False,
        logger: Optional[XLogger] = None,  # XLogger(),  # instance
    ) -> None:
        """
        config インスタンスを与えると、cfg_name はいらない

        Args:
            rmc_log: RMC_POT のログ処理用のインスタンス
            rmc_dat: RMC_POT のDAT処理用のインスタンス
            config (Config): 全てのインスタンスが同じ Config()
            logger (XLogger): 全てインスタンスが同じ XLogger()
            cfg_name (str): cfg-filename
        """
        # ------------------------------------------------------------
        # 1. logger と config を決定
        # ------------------------------------------------------------
        # （引数で与えればそれを使う／なければ新規作成）
        self._logger: XLogger = logger or XLogger()
        self._config: Config = config or Config()
        self._use_free_format: bool = use_free_format

        # ------------------------------------------------------------
        # 2. cfg_name の決定
        # ------------------------------------------------------------
        # config インスタンスが cfg_name を持っていれば、それを使っても良い
        # 逆に引数で明示された cfg_name は config に反映する
        if cfg_name is None:
            cfg_name = self._config.cfg_name
        else:
            self._config.cfg_name = cfg_name

        # このクラス自身も cfg_name を内部保持する
        self._cfg_name: str = cfg_name

        # Config 内の auto_write を取り出して内部保持
        self._auto_write: bool = self._config.auto_write

        # ------------------------------------------------------------
        # 3. RMC ログ処理クラスの準備
        # ------------------------------------------------------------
        # 引数で外部から渡されていなければ、ここで新規作成
        if rmc_log is None:
            rmc_log = RmcPotLog(
                config=self._config,
                logger=self._logger,
            )

        self._rmc_log: RmcPotLog = rmc_log

        # RMC ログクラスに cfg_name を反映
        # self._logger.info("")
        self._logger.info(f"[rmc_pot] == rmc_log.set_cfg_name({cfg_name})")
        self._rmc_log.set_cfg_name(cfg_name)

        # ------------------------------------------------------------
        # 4. RMC データ処理クラス (.dat) の準備
        # ------------------------------------------------------------
        # 外部指定なければ新規作成する
        if rmc_dat is None:
            rmc_dat = RmcPotDat(
                cfg_name=self._cfg_name,
                auto_write=self._auto_write,
                config=self._config,
                use_free_format=self._use_free_format,
                logger=self._logger,
            )
            rmc_dat.init()

        self._rmc_dat: RmcPotDat = rmc_dat
        # self._logger.info("")
        self._logger.info("[rmc_pot] == rmc_pot_dat()")

    @property
    def rmc_dat(self):
        return self._rmc_dat

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name = cfg_name
        self._config.cfg_name = cfg_name

        # rmc_dat に cfg_name をセットする
        if self._rmc_dat:
            self._rmc_dat.set_cfg_name(cfg_name)

        # rmc_log に cfg_name をセットする
        if self._rmc_log:
            self._rmc_log.set_cfg_name(cfg_name)

    # --------------------
    # 互換 I/F
    # --------------------
    def set_tag(self, tag_name: str, *args) -> None:
        """
        RmcPotData 側の set_xxx メソッドを呼び出す互換I/F。

        Args:
            tag_name (str): タグ名（例: 'cutoffs', 'potential'）
            *args: set_xxx に渡す引数
        """
        method_name = f"set_{tag_name.lower()}"
        method = getattr(self._rmc_dat, method_name, None)
        if method is None:
            raise AttributeError(
                f"RmcPotData に '{method_name}' が定義されていません。"
            )
        method(*args)

    def get_tag(self, tag_name: str, *args):
        """
        RmcPotData 側の get_xxx メソッドを呼び出す互換I/F。

        Args:
            tag_name (str): タグ名（例: 'cutoffs', 'potential'）
            *args: get_xxx に渡す引数（必要な場合）

        Returns:
            Any: 対応する get_xxx の戻り値
        """
        method_name = f"get_{tag_name.lower()}"
        method = getattr(self._rmc_dat, method_name, None)
        if method is None:
            raise AttributeError(
                f"RmcPotData に '{method_name}' が定義されていません。"
            )
        return method(*args)

    def init(self, cfg_name: str):
        """
        RMC-DFT は RMC から始める。しかし構造ファイルは VASP ベースから
        スタートするので、rmc_pot 側での初期化はこのルーチンでは明示的にしない
        互換のフェイクI/F

        Args:
            cfg_name:

        Returns:

        """
        pass

    def preprocess(self) -> bool:
        """
         RMC_POT の実行前に必要な入力ファイルを検査する。

        このコードを動かすときは RMC_POT 入力が揃っている前提とする
         1. 実験プロファイル（例: fesi04_smbt-rmc.txt）が実行カレントに存在しないときは止める
         2. label.txt が存在しないと止める

         *) 初期の構造変換は誤解が起きやすいので RmcPot クラスでは Preprocess() で勝手にやらないようにする


         Returns:
             bool:
                 必要な入力ファイルがすべて存在し、実験データファイル名を
                 正常に取得できた場合は ``True``。
                 入力不足または設定不正の場合は ``False``。
        """
        self._logger.info("[rmc_pot] == preprocess()")

        ##################################################
        # aaa.cfg が存在しないときは止める(構造情報)
        if not os.path.exists(f"{self._cfg_name}.cfg"):
            self._logger.error(f"**Error**: {self._cfg_name}.cfg が見つかりません。")
            return False
            # sys.exit(-1)

        ##################################################
        # aaa.dat が存在しないときは止める(INPUT)
        if not os.path.exists(f"{self._cfg_name}.dat"):
            self._logger.error(f"**Error**: {self._cfg_name}.dat が見つかりません。")
            return False
            # sys.exit(-1)

        # 実行カレント（実行したPythonのパス）を基準にする
        work_dir = os.getcwd()
        self._logger.info(f"[rmc_pot] work_dir   = {work_dir}")

        ##################################################
        # Config から element_info を取得
        label_name = self._config.element_info

        if isinstance(label_name, str):
            # ファイル名として扱う
            label_name_path = os.path.join(
                work_dir,
                label_name,
            )

            if not os.path.exists(label_name_path):
                self._logger.error(f"**Error**: {label_name_path} が見つかりません。")
                return False

        ##################################################
        # RmcPotDat から実験データのファイル名を取得(実験データ)
        exp_name = self._rmc_dat.get_exp_filename()

        if exp_name is False:
            self._logger.error(
                "[rmc_pot] **Error**: " "実験データファイル名を取得できません。"
            )
            return False
            # sys.exit(-1)

        self._logger.info(f"[rmc_pot] == get_exp_name: {exp_name}")

        exp_name_path = os.path.join(
            work_dir,
            exp_name,
        )

        self._logger.info(f"[rmc_pot] target_exp_name_path = {exp_name_path}")
        self._logger.info("[rmc_pot] .")

        # ファイルの存在チェック
        if not os.path.exists(exp_name_path):
            self._logger.error(f"**Error**: {exp_name_path} が見つかりません。")
            return False

        return True

    def postprocess(
        self,
        log_dir: Optional[str] = None,
        cfg_name: Optional[str] = None,
        element_info: Optional[Union[str, Sequence[str]]] = None,
    ) -> bool:
        """
        後処理

        RMC 後に DFT を動かすにあたっての
        1) DATA-collect
        2) BACKUP
        3) xxx.CFG --> POSCAR (VASP4) 変換(xxx.vasp) --> VASP5 変換(xxx.vasp)

        他のコードを使っても基本は poscar 経由を念頭におくので
        postprocess は poscar にしておけば他のライブラリを使っても
        齟齬は出ない

        Args:
            log_dir (str): RMC用の log_dir
            cfg_name (str): cfg_name と vasp_name は等しいとする(デフォルトはコンストラの引数での cfg_name)
            element_info (str | list): 元素情報

        Returns:
            bool:

        """
        self._logger.info("")
        self._logger.info(f"[rmc_pot] == postprocess()")

        if log_dir is None:
            log_dir = self._config.rmc_log_dir
        self._logger.info(f"[rmc_pot] log_dir(RMC) = {log_dir}")

        if cfg_name is None:
            cfg_name = self._cfg_name
        self._logger.info(f"[rmc_pot] cfg_name = {cfg_name}")

        if element_info is None:
            # element_info = "label.txt"
            element_info = self._config.element_info

        self._logger.info(f"[rmc_pot] element_info = {element_info}")

        # DATA-collect
        self._rmc_log.collect_result()

        # BACKUP-RESULT
        self._rmc_log.backup_result(
            log_dir=log_dir,
            cfg_name=cfg_name,
        )

        # RMC_POT 結果から、POSCAR (VASP4 style) 作成
        # --> xxx.vasp
        # self._logger.info("")
        self._logger.info(f"[rmc_pot] == cfg2poscar({cfg_name}.vasp)")
        self.cfg2poscar(
            cfg_name=cfg_name,
            vasp_name=cfg_name,
            element_info=element_info,
        )

        ###########################
        # cfg2poscar update のため廃止
        # # VASP4 --> VASP5
        # self._logger.info(f"== ensure vasp5 format ({cfg_name}.vasp)")
        # self.ensure_vasp5_format(
        #     poscar_name=f"{cfg_name}.vasp",
        #     element_info=element_info,
        # )
        ###########################

        # ここで POSCAR にすると入力の元になった POSCAR があると
        # 干渉するので method の使い方で破綻する恐れがある。

        # xxx.vasp --> POSCAR
        # shutil.copy(f"{cfg_name}.vasp", "POSCAR")

        return True

    def check_fnc_cutoff_consistency(self, cfg_name: Optional[str] = None) -> bool:
        """
        RMC_POT 実行前に、*.fnc の rmin と *.dat の hard-sphere cutoff の
        整合性を確認する。

        FNC の constraint type 番号と原子種ペアを固定対応させず、
        *.fnc に記録された実際の原子 index ペアと *.cfg の原子種別ブロックから
        対応する RMC 原子タイプを決定する。
        """
        if cfg_name is None:
            cfg_name = self._cfg_name

        dat_path = "%s.dat" % cfg_name
        fnc_path = "%s.fnc" % cfg_name
        cfg_path = "%s.cfg" % cfg_name

        if not os.path.exists(fnc_path):
            self._logger.info(
                "[rmc_pot] FNC file not found. skip FNC/cutoff check: %s" % fnc_path
            )
            return True

        if not os.path.exists(dat_path):
            self._logger.error("[rmc_pot] **Error**: DAT file not found: %s" % dat_path)
            return False

        if not os.path.exists(cfg_path):
            self._logger.error("[rmc_pot] **Error**: CFG file not found: %s" % cfg_path)
            return False

        cutoffs = self._read_dat_cutoffs(dat_path)
        fnc_rmin = self._read_fnc_rmin_values(fnc_path)
        fnc_pairs = self._read_fnc_pairs(fnc_path)
        atom_types = self._read_cfg_atom_types(cfg_path)

        if len(fnc_rmin) == 0:
            self._logger.error(
                "[rmc_pot] **Error**: FNC rmin values could not be read from %s"
                % fnc_path
            )
            return False

        if len(fnc_pairs) == 0:
            self._logger.error(
                "[rmc_pot] **Error**: FNC atom pairs could not be read from %s"
                % fnc_path
            )
            return False

        if len(atom_types) == 0:
            self._logger.error(
                "[rmc_pot] **Error**: atom types could not be read from %s"
                % cfg_path
            )
            return False

        number_of_types = max(atom_types.values())
        expected_cutoff_count = number_of_types * (number_of_types + 1) // 2

        if len(cutoffs) != expected_cutoff_count:
            self._logger.error(
                "[rmc_pot] **Error**: cutoff count is inconsistent with CFG atom types: "
                "cutoffs=%d expected=%d atom_types=%d"
                % (len(cutoffs), expected_cutoff_count, number_of_types)
            )
            return False

        checked = set()
        ok = True

        for atom_index1, atom_index2, type_id in fnc_pairs:
            if type_id not in fnc_rmin:
                self._logger.error(
                    "[rmc_pot] **Error**: FNC range is not defined: fnc_type=%d"
                    % type_id
                )
                ok = False
                continue

            if atom_index1 not in atom_types or atom_index2 not in atom_types:
                self._logger.error(
                    "[rmc_pot] **Error**: FNC atom index is outside CFG range: "
                    "atom1=%d atom2=%d" % (atom_index1, atom_index2)
                )
                ok = False
                continue

            atom_type1 = atom_types[atom_index1]
            atom_type2 = atom_types[atom_index2]
            pair_key = (
                type_id,
                min(atom_type1, atom_type2),
                max(atom_type1, atom_type2),
            )

            if pair_key in checked:
                continue
            checked.add(pair_key)

            cutoff_index = self._get_cutoff_index(
                atom_type1,
                atom_type2,
                number_of_types,
            )
            cutoff = cutoffs[cutoff_index]
            rmin = fnc_rmin[type_id]

            if rmin < cutoff:
                self._logger.error(
                    "[rmc_pot] **Error**: FNC/cutoff inconsistency: "
                    "fnc_type=%d atom_types=%d-%d rmin=%.8f < cutoff=%.8f"
                    % (type_id, atom_type1, atom_type2, rmin, cutoff)
                )
                ok = False
                continue

            self._logger.info(
                "[rmc_pot] FNC/cutoff check: "
                "fnc_type=%d atom_types=%d-%d rmin=%.8f >= cutoff=%.8f"
                % (type_id, atom_type1, atom_type2, rmin, cutoff)
            )

        if not ok:
            self._logger.error("[rmc_pot] Stop before RMC_POT run.")
            return False

        self._logger.info("[rmc_pot] FNC/cutoff consistency check: OK")
        return True

    @staticmethod
    def _read_dat_cutoffs(dat_path: str) -> List[float]:
        """
        *.dat の cutoff 値を読む。

        固定形式の ``! cut offs`` と自由形式の ``CUT-OFF =`` の両方を扱う。
        """
        values = []

        with open(dat_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                lower = stripped.lower()

                if "cut offs" in lower:
                    text = line.split("!")[0]
                elif lower.startswith("cut-off") and "=" in line:
                    text = line.split("=", 1)[1]
                else:
                    continue

                for word in text.split():
                    try:
                        value = float(word)
                    except ValueError:
                        continue
                    values.append(value)

                break

        return values

    @staticmethod
    def _read_fnc_rmin_values(fnc_path: str) -> Dict[int, float]:
        """
        *.fnc の rmin 行を読む。
        """
        with open(fnc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        index = 0
        while index < len(lines):
            line = lines[index]
            if "No. of possible rmin-rmax pairs" in line:
                break
            index += 1

        if index >= len(lines):
            return {}

        count_line_index = index + 1
        rmin_line_index = index + 2

        if rmin_line_index >= len(lines):
            return {}

        try:
            count = int(lines[count_line_index].strip())
        except ValueError:
            return {}

        words = lines[rmin_line_index].split()
        if len(words) < count:
            return {}

        result = {}
        type_id = 1
        while type_id <= count:
            result[type_id] = float(words[type_id - 1])
            type_id += 1

        return result

    @staticmethod
    def _read_fnc_pairs(fnc_path: str) -> List[Tuple[int, int, int]]:
        """
        *.fnc から一意な ``(atom1, atom2, constraint_type)`` を読む。
        """
        with open(fnc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        marker = 0
        while marker < len(lines):
            if "No. of possible rmin-rmax pairs" in lines[marker]:
                break
            marker += 1

        if marker >= len(lines):
            return []

        cursor = marker + 4
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

        if cursor >= len(lines):
            return []

        try:
            atom_count = int(lines[cursor].split()[0])
        except (IndexError, ValueError):
            return []

        cursor += 1
        pairs = []
        seen = set()
        atom_entry_count = 0

        while cursor < len(lines) and atom_entry_count < atom_count:
            if not lines[cursor].strip():
                cursor += 1
                continue

            header = lines[cursor].split()
            cursor += 1

            if len(header) < 2:
                return []

            try:
                atom_index = int(header[0])
                neighbour_count = int(header[1])
            except ValueError:
                return []

            atom_entry_count += 1

            if neighbour_count == 0:
                continue

            if cursor + 1 >= len(lines):
                return []

            try:
                neighbours = [int(value) for value in lines[cursor].split()]
                constraint_types = [
                    int(value) for value in lines[cursor + 1].split()
                ]
            except ValueError:
                return []

            cursor += 2

            if len(neighbours) != neighbour_count:
                return []
            if len(constraint_types) != neighbour_count:
                return []

            for neighbour, constraint_type in zip(
                neighbours,
                constraint_types,
            ):
                atom1 = min(atom_index, neighbour)
                atom2 = max(atom_index, neighbour)
                key = (atom1, atom2, constraint_type)

                if key in seen:
                    continue

                seen.add(key)
                pairs.append(key)

        return pairs

    @staticmethod
    def _read_cfg_atom_types(cfg_path: str) -> Dict[int, int]:
        """
        RMC_POT Version 3 の *.cfg から、RMC atom index とtypeの対応を作る。

        cfg2poscar.py と同じ配置規則を使用する。

        - 8行目: 全原子数
        - 9行目: type数
        - 19行目以降: 各typeの定義ブロック
        - 各typeブロックは4行
        - ブロック先頭行の第1要素が、そのtypeの原子数
        - 座標はtype順に連続して並ぶ
        """
        with open(cfg_path, "r", encoding="utf-8") as f:
            datlines = f.read().split("\n")

        if len(datlines) < 18:
            return {}

        try:
            total_atoms = int(datlines[7].split()[0])
            number_of_types = int(datlines[8].split()[0])
        except (IndexError, ValueError):
            return {}

        if total_atoms < 1 or number_of_types < 1:
            return {}

        type_counts = []
        line_index = 17

        for _ in range(number_of_types):
            line_index += 1

            if line_index >= len(datlines):
                return {}

            words = datlines[line_index].split()
            if len(words) == 0:
                return {}

            try:
                atom_count = int(words[0])
            except ValueError:
                return {}

            if atom_count < 1:
                return {}

            type_counts.append(atom_count)

            line_index += 3

        if sum(type_counts) != total_atoms:
            return {}

        atom_types: Dict[int, int] = {}
        atom_index = 1

        for atom_type, atom_count in enumerate(type_counts, start=1):
            for _ in range(atom_count):
                atom_types[atom_index] = atom_type
                atom_index += 1

        return atom_types

    @staticmethod
    def _get_cutoff_index(
        atom_type1: int,
        atom_type2: int,
        number_of_types: int,
    ) -> int:
        """
        RMC の上三角順 cutoff 配列における0始まりindexを返す。

        例: 3 typeの場合
            (1,1), (1,2), (1,3), (2,2), (2,3), (3,3)
        """
        type1 = min(int(atom_type1), int(atom_type2))
        type2 = max(int(atom_type1), int(atom_type2))

        if type1 < 1 or type2 > number_of_types:
            raise ValueError(
                "atom type is outside range: %d-%d, number_of_types=%d"
                % (type1, type2, number_of_types)
            )

        index = 0
        current_type1 = 1

        while current_type1 < type1:
            index += number_of_types - current_type1 + 1
            current_type1 += 1

        index += type2 - type1
        return index

    def run(
        self,
        cfg_name: Optional[str] = None,
        blocking: Optional[bool] = True,
        save_stdout: Optional[bool] = True,
    ) -> bool:
        """
        RMC を実行する

        Args:
            cfg_name (str):
            blocking (bool)_:  subprocessをブロッキングで起動(default: True)
            save_stdout (bool): True ならログをファイルに保存

        Returns:
            bool: 正しく終わったデー
        """
        if cfg_name is None:
            cfg_name = self._cfg_name
        self._logger.info(f"[rmc_pot] == run(cfg_name={cfg_name})")

        # --- ログ出力準備 ---
        log_filename = f"{cfg_name}.log"
        self._logger.info(f"[rmc_pot] log_filename = {cfg_name}.log")

        if save_stdout:
            f = open(log_filename, "w", encoding="utf-8")
        else:
            f = None

        # --- 環境変数での OMP などの設定
        env = os.environ.copy()

        if self._config.rmc_omp_num_threads is not None:
            env["OMP_NUM_THREADS"] = str(self._config.rmc_omp_num_threads)

        # 2025 あたりの rmc_pot
        # subprocess.run([f"{self._config.rmc_bin}", f"{cfg_name}"], check=True)
        # 2014 あたりの rmc_pot
        # subprocess.run([f"{self._config.rmc_bin}", f"{cfg_name}", "y"], check=True)
        # 2014 あたりの書式で 2025 でも動く
        cmd = [f"{self._config.rmc_bin}", f"{cfg_name}", "y"]

        # --- blocking=True の場合（従来通り run()） ---
        if blocking:
            try:
                # subprocess.run(
                proc = subprocess.Popen(
                    cmd,
                    # check=True,
                    # stdout=f,
                    # stderr=f,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # --- リアルタイムで読みながら画面にも表示し、ログにも書く ---
                for line in proc.stdout:
                    sys.stdout.write(line)  # 画面へ
                    if f is not None:
                        f.write(line)  # ログへ

                stderr_text = proc.stderr.read()
                if stderr_text:
                    sys.stderr.write(stderr_text)
                    if f is not None:
                        f.write(stderr_text)

                return_code = proc.wait()

                if return_code != 0:
                    self._logger.error(
                        "[rmc_pot] **Error**: "
                        f"RMC_POT exited with return code {return_code}"
                    )
                    return False

            except OSError as e:
                self._logger.error(f"[rmc_pot] **Error**: {e}")
                return False
            finally:
                if f is not None:
                    f.close()
            return True

        # --- blocking=False の場合（Python終了後も生存） ---
        # 完全デタッチ（Python が死んでも RMC_POT が継続）
        p = subprocess.Popen(
            cmd,
            env=env,
            stdout=f,
            stderr=f,
            text=True,
            preexec_fn=os.setsid,
        )

        # ログファイルは閉じてよい（プロセスが保持している）
        if f is not None:
            f.close()

        # 非同期開始なので True を返して Python は先に進む
        return True

    #
    # Utilities
    #

    @staticmethod
    def ensure_vasp5_format(
        poscar_name: str,
        element_info: Optional[str] = None,
        logger: XLogger = XLogger(),
    ) -> bool:
        """
        RMC_POT には元素種の情報がなくて、VASP4 の POSCAR 相当のものしか
        変換では作ることができない。そのために、VASP4 形式の POSCASR に
        元素種の情報を付加する。そのための method (utility)

        Args:
            poscar_name:
            element_info:
            logger:

        Returns:

        """
        return ensure_vasp5_format(
            poscar_name,
            element_info,
            logger=logger,
        )

    def cfg2poscar(
        self,
        cfg_name: Optional[str] = None,
        vasp_name: Optional[str] = None,
        element_info: Optional[Union[str, Sequence[str]]] = None,
    ) -> bool:
        """
        CFG から POSCAR 変換

        CFG からそのまま作るので、そのままだと元素種の情報がないので
        VASP4 形式の POSCAR となる。

        Args:
            cfg_name (str):  xxx.cfg（拡張子なしのベース名を想定）
            vasp_name (str): xxx.vasp（拡張子なしのベース名を想定）
            element_info (str or Sequence[str]): ["Fe","Si",,,]
        """
        if cfg_name is None:
            cfg_name = self._cfg_name
        if vasp_name is None:
            vasp_name = cfg_name

        self._logger.info(f"[rmc_pot] cfg_name  = {cfg_name}")
        self._logger.info(f"[rmc_pot] vasp_name = {vasp_name}")

        cfg2poscar(
            cfg_name=cfg_name,
            vasp_name=vasp_name,
            element_info=element_info,
        )

        # POSCAR を後に上書きしちゃうので保存しておく
        # 繰り返し作業するとそれも上書きされるのでほぼ意味はないが
        if os.path.exists("POSCAR"):
            shutil.copy("POSCAR", "POSCAR.bak")

        # xxx.vasp を POSCAR 名でもコピー
        shutil.copy((vasp_name + ".vasp"), "POSCAR")
        return True
