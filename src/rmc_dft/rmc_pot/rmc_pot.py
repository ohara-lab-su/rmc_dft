#!/usr/bin/env python
"""
K.KOBAYASHI
K.NAKADA, Kengo.nakada@gmail.com
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
        rmc_log: RmcPotLog = None,  # instance
        rmc_dat: RmcPotDat = None,  # instance
        config: Optional[Config] = None,  # Config(),  # instance
        logger: Optional[XLogger] = None,  # XLogger(),  # instance
        cfg_name: Optional[str] = None,
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
        self._logger.info(f"== rmc_log.set_cfg_name({cfg_name})")
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
                logger=self._logger,
            )

        self._rmc_dat: RmcPotDat = rmc_dat
        self._logger.info("== rmc_pot_dat()")

    @property
    def rmc_dat(self):
        return self._rmc_dat

    def set_cfg_name(self, cfg_name: str):
        self._cfg_name = cfg_name
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

    def preprocess(self) -> None:
        """
        このコードを動かすときは RMC_POT 入力が揃っている前提とする
        1. 実験プロファイル（例: fesi04_smbt-rmc.txt）が実行カレントに存在しないときは止める
        2. label.txt が存在しないと止める

        *) 初期の構造変換は誤解が起きやすいので RmcPot クラスでは Preprocess() で勝手にやらないようにする
        """
        self._logger.info("== preprocess()")

        ##################################################
        # aaa.cfg が存在しないときは止める(構造情報)
        if not os.path.exists(f"{self._cfg_name}.cfg"):
            self._logger.error(f"**Error**: {self._cfg_name}.cfg が見つかりません。")
            sys.exit(-1)

        ##################################################
        # aaa.dat が存在しないときは止める(INPUT)
        if not os.path.exists(f"{self._cfg_name}.dat"):
            self._logger.error(f"**Error**: {self._cfg_name}.dat が見つかりません。")
            sys.exit(-1)

        # 実行カレント（実行したPythonのパス）を基準にする
        work_dir = os.getcwd()
        self._logger.info(f"work_dir   = {work_dir}")

        ##################################################
        # Config から elemento_info を取得
        label_name = self._config.element_info

        if isinstance(label_name, str):
            # ファイル名として扱う
            exp_name_path = os.path.join(work_dir, label_name)
            if not os.path.exists(exp_name_path):
                self._logger.error(f"**Error**: {exp_name_path} が見つかりません。")
                sys.exit(-1)

        ##################################################
        # RmcPotDat から実験データのファイル名を取得(実験データ)
        exp_name = self._rmc_dat.get_exp_filename()

        self._logger.info(f"== get_exp_name: {exp_name}")
        exp_name_path = os.path.join(work_dir, exp_name)
        self._logger.info(f"target_exp_name_path = {exp_name_path}")
        self._logger.info(f".")

        # ファイルの存在チェック
        if not os.path.exists(exp_name_path):
            self._logger.error(f"**Error**: {exp_name_path} が見つかりません。")
            sys.exit(-1)

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
        self._logger.info(f"== postprocess()")

        if log_dir is None:
            log_dir = self._config.rmc_log_dir
        self._logger.info(f"log_dir(RMC) = {log_dir}")

        if cfg_name is None:
            cfg_name = self._cfg_name
        self._logger.info(f"cfg_name = {cfg_name}")

        if element_info is None:
            # element_info = "label.txt"
            element_info = self._config.element_info

        self._logger.info(f"element_info = {element_info}")

        # DATA-collect
        self._rmc_log.collect_result()

        # BACKUP-RESULT
        self._rmc_log.backup_result(
            log_dir=log_dir,
            cfg_name=cfg_name,
        )

        # RMC_POT 結果から、POSCAR (VASP4 style) 作成
        # --> xxx.vasp
        self._logger.info(f"== cfg2poscar({cfg_name}.vasp)")
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
        self._logger.info(f"== run(cfg_name={cfg_name})")

        # --- ログ出力準備 ---
        log_filename = f"{cfg_name}.log"
        self._logger.info(f"log_filename = {cfg_name}.log")

        if save_stdout:
            f = open(log_filename, "w", encoding="utf-8")
        else:
            f = None

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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # --- リアルタイムで読みながら画面にも表示し、ログにも書く ---
                for line in proc.stdout:
                    sys.stdout.write(line)  # 画面へ
                    if f is not None:
                        f.write(line)  # ログへ
                proc.wait()

            except subprocess.CalledProcessError as e:
                self._logger.error(f"**Error**: {e}")
                sys.exit(-1)
            finally:
                if f is not None:
                    f.close()
            return True

        # --- blocking=False の場合（Python終了後も生存） ---
        # 完全デタッチ（Python が死んでも RMC_POT が継続）
        p = subprocess.Popen(
            cmd,
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
        return ensure_vasp5_format(poscar_name, element_info, logger=logger)

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

        self._logger.info(f"cfg_name  = {cfg_name}")
        self._logger.info(f"vasp_name = {vasp_name}")

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
