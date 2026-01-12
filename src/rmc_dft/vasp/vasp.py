#!/usr/bin/env python
"""
K.KOBAYASHI
K.NAKADA, kengo.nakada@gmail.com
"""
import os
import sys
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Sequence
import shutil
import subprocess
import json

from ase.io import read, write

from rmc_dft.config import Config
from rmc_dft.vasp.vasp_incar import VaspIncar
from rmc_dft.vasp.vasp_kpoints import VaspKpoints
from rmc_dft.vasp.vasp_log import VaspLog
from rmc_dft.vasp.util.poscar2cfg import (
    vasp2cfg,
    contcar2cfg,
    poscar2cfg,
    convert_to_cfg,
)

# util
from rmc_dft.vasp.util.copy_contcar_to_vasp import copy_contcar_to_vasp
from rmc_dft.vasp.util.copy_vasp_to_poscar import copy_vasp_to_poscar
from rmc_dft.vasp.util.xdatcar2poscar import xdatcar2poscar
from rmc_dft.vasp.util.ensure_vasp5_format import ensure_vasp5_format
from rmc_dft.vasp.util.make_potcar import VaspPotcarBuilder

from x_logger import XLogger

# vasp.py 冒頭（class 外）


class Vasp:
    """
    RMD-DFT  のため VASP構造作成 / VASPパラメータ入力 / 実行 /解析用のクラス
    """

    def __init__(
        self,
        *,
        incar_name: str = "INCAR",
        kpoints_name: str = "KPOINTS",
        vasp_log: VaspLog = None,  # instance (データー解析用)
        vasp_incar: VaspIncar = None,
        vasp_kpoints: VaspKpoints = None,
        config: Optional[Config] = None,  # Config(),  # instance
        logger: Optional[XLogger] = None,  # XLogger(),  # instance
        auto_write: bool = True,
        vasp_name: str = None,
        dft_bin: str = None,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = None,
        job_cmd: str = None,
        make_default_input: bool = False,
    ) -> None:
        """
        config インスタンを与えると終わり

        (*) 歴史的経緯で複雑になっているが、config 与えれば終わり

        Args:
            incar_name (str): INCAR
            kpoints_name (str): KPOINTS
            vasp_log (VaspLog): VASP の log 解析管理 instance
            vasp_incar (VaspIncar):
            vasp_kpoints (VaspKpoints):
            config (Config): 全てのインスタンスが同じ Config
            logger (XLogger): ろがー、全てのインスタンスが同じ XLogger
            auto_write (bool):
            vasp_name (str): POSCAR などに関連する系の識別名（例: "aaa.vasp" or "POSCAR）
            dft_bin (str): 実行バイナリ（例: "vasp_std"）
            mpi_cmd (str): 例 "mpirun" (configがあればいらない)
            mpi_flag (str): 例 "-np" (configがあればいらない)
            num_procs (int): 並列数 (configがあればいらない)
            job_cmd (str): ジョブ投入コマンド（None ならローカル実行）
            make_default_input (bool): インプットファイルを自動作成(既存があるときはそっちを優先)
        """
        self._logger = logger or XLogger()
        self._config: Config = config or Config()
        self._logger.info("== create Vasp()")

        # INCAR/KPOINTS/
        self.incar_name: str = incar_name
        self.kpoints_name: str = kpoints_name

        # write?
        self.auto_write: bool = auto_write

        # aaa.vasp
        if config:
            if vasp_name is None:
                vasp_name: str = config.vasp_name
        if vasp_name is None:
            vasp_name: str = "POSCAR"
        self._vasp_name: str = vasp_name

        # VASP 実行系設定
        self.dft_bin: str = dft_bin or config.dft_bin
        self.mpi_cmd: Optional[str] = mpi_cmd or config.mpi_cmd
        self.mpi_flag: Optional[str] = mpi_flag or config.mpi_flag
        self.num_procs: Optional[int] = num_procs or config.num_procs
        self.job_cmd: Optional[str] = job_cmd or config.job_cmd
        # self.job_cmd = job_cmd

        self._logger.info(f"")
        self._logger.info(f"dft_bin={self.dft_bin}")
        self._logger.info(f"mpi_cmd={self.mpi_cmd}")
        self._logger.info(f"mpi_flag={self.mpi_flag}")
        self._logger.info(f"num_procs={self.num_procs}")
        self._logger.info(f"job_cmd={self.job_cmd}")
        self._logger.info(f"")

        # --- VaspLog() instance ---
        if vasp_log is None:
            vasp_log = VaspLog(logger=self._logger)
        self._vasp_log: VaspLog = vasp_log

        # --- INCAR ---
        self._incar_defaults: Dict[str, object] = {
            # INCAR デフォルト値定義
            "EDIFF": 1e-04,
            "EDIFFG": 1e-05,
            "ISTART": 0,
            "ISMEAR": 0,
            "SIGMA": 0.1,
            "NSW": 2,
            "NELM": 30,
            "IBRION": 2,
            "ISIF": 2,
            "LREAL": "auto",
        }
        if vasp_incar is None:
            vasp_incar = VaspIncar(
                incar_name=self.incar_name,
                auto_write=self.auto_write,
                logger=self._logger,
            )
        self._incar: VaspIncar = vasp_incar

        # --- KPOINTS ---
        if vasp_kpoints is None:
            vasp_kpoints = VaspKpoints(
                kpoints_name=self.kpoints_name,
                auto_write=self.auto_write,
                logger=self._logger,
            )
        self._kpoints: VaspKpoints = vasp_kpoints

        if make_default_input:
            # INCAR が存在すれば読み込み、なければデフォルトで新規作成
            if not os.path.exists(self.incar_name):
                for key, val in self._incar_defaults.items():
                    self._logger.debug(f"set {key} = {val}")
                    self._incar.set(key, val)

            # KPOINTS: 既存があれば読み取り優先。
            # 無ければデフォルトで生成（Monkhorst-Pack 1 1 1, shift 0 0 0）
            if not os.path.exists(self.kpoints_name):
                self._kpoints.set_mode("Monkhorst-Pack")
                self._kpoints.set_grid(1, 1, 1)
                self._kpoints.set_shift(0, 0, 0)
                self._kpoints.write()

    # --- 委譲メソッド群 (INCAR) ---
    def get_tag(self, key: str):
        """INCAR の値を取得"""
        return self._incar.get(key)

    def set_tag(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        INCAR の値を設定

        Example:
            set_tag("NSW", 1)

        Args:
            key (str):
            value (Any):

        Returns:
            None:
        """
        if isinstance(value, int):
            valeue = str(value)
        if isinstance(value, float):
            valeue = str(value)

        self._incar.set(key, value)

    def remove_tag(self, key: str):
        """INCAR の項目を削除"""
        self._incar.remove(key)

    def reload_incar(self):
        """INCAR を再読込"""
        self._incar.reload()

    def export_incar_dict(self):
        """INCAR を辞書で取得"""
        return self._incar.export_dict()

    # --- 委譲メソッド群 (KPOINTS) ---
    def get_kpoints(self, key: str):
        """KPOINTS の値取得（grid/gamma/comment）"""
        return self._kpoints.get_value(key)

    def set_kpoints(self, key: str, value) -> None:
        """
        KPOINTS 値設定。
        明示設定は既存ファイルより優先して上書き。
        """
        self._kpoints.set_value(key, value)

    def reload_kpoints(self) -> None:
        """KPOINTS 再読込"""
        self._kpoints.reload_kpoints()

    def export_kpoints_dict(self):
        """KPOINTS を辞書で取得"""
        return self._kpoints.export_dict()

    #
    # RMC-DFT の VASP 側の init/preprocess/postprocess
    #

    def init(
        self,
        cfg_name: str = None,
    ):
        """
        POSCAR から cfg を作る

        Args:
            cfg_name (str): 出力する cfg_name.cfg

        Returns:

        """
        self._logger.info(f"== init()")

        # if cfg_name is None:
        #     cfg_name = self._vasp_name
        # self._logger.info(f"cfg_name={cfg_name})")

        # # POSCAR から CFG を作成
        # self._logger.info(f"== poscar2cfg(cfg_name={cfg_name})")
        # self.poscar2cfg(cfg_name=cfg_name)

    @staticmethod
    def cat(filename: str) -> None:
        if os.path.exists(filename):
            with open(filename) as f:
                print(f.read(), end="")
        else:
            print(f"[Warning] {filename} not found.")

    def preprocess(
        self,
        vasp_name: str = None,
        element_info: Optional[Union[str, Sequence[str]]] = None,
    ) -> bool:
        """
        vasp 前処理

        基本的に Vasp Class は相手がなんであれ動くようにする
        それは入力が常に VASP であることを仮定していて、
        相手のプログラム側の postprocess or convert してから動かすことを全手とする

        *) 構造変換関係は Vasp() では自動で preprocess に入れない。誤解が生じやすい

        Args:
            vasp_name (str): xxx.vasp 名前における xxxに相当する名前
            element_info (str):

        Returns:
            bool:
        """
        self._logger.info("== preprocess()")
        if vasp_name is None:
            vasp_name = self._vasp_name

        # 実行スクリプトのあるディレクトリを基準にする
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self._logger.info(f"script_dir = {script_dir}")

        for filename in ["INCAR", "KPOINTS", "POTCAR", "POSCAR"]:
            target_path = os.path.join(script_dir, filename)
            self._logger.info(f"target_path = {target_path}")

            # 実験のファイル存在チェック
            if not os.path.exists(target_path):
                self._logger.error(f"**Error**: {target_path} が見つかりません。")
                sys.exit(-1)

        return True

    def postprocess(
        self,
        log_dir: Optional[str] = None,
        cfg_name: Optional[str] = None,
    ) -> bool:
        """
        後処理

        1) DATA-collect
        2) BACKUP
        3) CONTCAR --> POSCAR
        4) CONTCAR --> CFG (for RMC_POT)


        Args:
            log_dir (str): VASP_log_dir_name デフォルトは config() から dft_log_dir を取得
            cfg_name (str): POSCAR -> cfg_name.cfg (デフォルトは config() から cfg_name を取得する)

        Returns:
            bool:
        """
        self._logger.info("== postprocess()")

        if log_dir is None:
            log_dir = self._config.dft_log_dir
        self._logger.info(f"log_dir(VASP)={log_dir})")

        if cfg_name is None:
            cfg_name = self._config.cfg_name
        self._logger.info(f"cfg_name={cfg_name})")

        # DATA-collect
        self._vasp_log.collect_result()

        # BACKUP-DATA
        self._vasp_log.backup_result(log_dir=log_dir)

        # CONTCAR -> POSCAR
        shutil.copyfile("CONTCAR", "POSCAR")

        # CONTCAR -> CFG
        self._logger.info(f"== contcar2cfg(cfg_name={cfg_name}.cfg)")
        self.contcar2cfg(cfg_name=cfg_name)

        return True

    def backup(
        self,
        log_dir: Optional[str] = None,
    ) -> bool:
        if log_dir is None:
            log_dir = self._config.dft_log_dir

        # BACKUP-DATA
        self._vasp_log.backup_result(log_dir=log_dir)
        return True

    #
    # VASP run
    #

    def run(
        self,
        mode: Optional[str] = None,
        job_cmd: Optional[str] = None,
        blocking: bool = True,
    ) -> bool:
        """
        VASP を実行する

        local 実行
        FI_PROVIDER="TCP"
        I_MPI_FABRICS="shm:tcp"
        I_MPI_DEBUG="5"

        Args:
            mode (str): "local" dft_bin
                        "mpi" mpi_cmd + mpi_flag + num_procs + dft_bin
                        "job" job_cmd + dft_bin
            job_cmd (str): ジョブコマンド(mode=job時に使う)
                        　　優先順番
                           instance(job_cmd=xxx)< set_job_cmd(xxx) < run(job_cmd=xxx)
            blocking (bool):  subprocessをブロッキングで起動(default: True)

        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"=== run(mode={mode}) ===")

        # すべてのモードで共通の環境変数を定義
        env = os.environ.copy()

        if mode is None:
            mode = self._config.run_mode

        if mode == "local":
            self._logger.info(f"== local mpi mode")
            # MPI build された vasp を local で動かすためのもの (infinibandを使わない)
            env["FI_PROVIDER"] = "tcp"
            env["I_MPI_FABRICS"] = "shm:tcp"
            env["I_MPI_DEBUG"] = "5"
            cmd = ["mpirun", "-np", "1", f"{self.dft_bin}"]
            # cmd = [self.dft_bin]

        elif mode == "mpi":
            self._logger.info(f"== mpi mode")
            self._logger.info(f"mpi_cmd = {self.mpi_cmd}")
            self._logger.info(f"mpi_flag = {self.mpi_flag}")
            self._logger.info(f"dft_bin = {self.dft_bin}")
            self._logger.info(f"num_procs = {self.num_procs}")

            cmd = [self.mpi_cmd]

            if self.mpi_flag is not None:
                cmd.append(self.mpi_flag)

            if self.num_procs is not None:
                cmd.append(str(self.num_procs))

            cmd.append(f"{self.dft_bin}")

        elif mode == "job":
            self._logger.info(f"== job mode")
            if not job_cmd:
                job_cmd = self.job_cmd
            cmd = [job_cmd]

        else:
            # raise ValueError(f"**Error**: 未知の mode: {mode}")
            self._logger.error(f"**Error**: 未知の mode: {mode}")
            return False

        # dft_bin がパス上に存在するか確認
        if mode != "job":
            if shutil.which(self.dft_bin) is None:
                self._logger.error(
                    f"**Error**: {self.dft_bin} が見つかりません。PATHを確認してください。"
                )
                sys.exit(1)

        self._logger.info(f"move = {mode}")
        # self._logger.info(f"env = {json.dumps(env, indent=2)}")
        self._logger.info(f"cmd = {cmd}")

        try:
            subprocess.run(cmd, check=True, env=env)
        except subprocess.CalledProcessError as e:
            self._logger.error(f"**Error**: {e}")
            self._logger.error("  VASP実行中にエラーが発生")
            self._logger.error("  --> 距離が近すぎることで電子密度がおかい>")
            self._logger.error("  --> 行列問題の解法で転けたとか")
            self._logger.error(
                f"強制STOP ではなくて、そのままRMC側に戻して、ハンドリングする"
            )
            # sys.exit(1)
            return False

        return True

        self._logger.info("=== run()")
        # subprocess.run(f"{Config.dft_bin}", check=True, shell=True)
        subprocess.run(
            ["mpirun", "-np", f"{Config.num_procs}", f"{Config.dft_bin}"], check=True
        )
        return True

    #
    # VASP 側の設定
    #

    def set_mpi(
        self,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = None,
    ):
        """MPI設定書き換え"""
        if mpi_cmd:
            self.mpi_cmd = mpi_cmd
        if num_procs:
            self.num_procs = num_procs
        if mpi_flag:
            self.mpi_flag = mpi_flag

    def set_job_cmd(
        self,
        job_cmd: str = None,
    ):
        if job_cmd:
            self.job_cmd = job_cmd

    #
    # for VASP
    #

    @staticmethod
    def ensure_vasp5_format(
        poscar_name: str,
        element_info: Optional[Union[str, Sequence[str]]] = None,
        logger: Optional[XLogger] = XLogger(),
    ) -> bool:
        if element_info is None:
            element_info = self._config.element_info
        return ensure_vasp5_format(poscar_name, element_info, logger=logger)

    @staticmethod
    def make_potential(
        elements: List[str],
        output: str = "POTCAR",
    ) -> bool:
        """
        VaspPotcarBuilder クラスを使って POTCAR を生成

        Args:
            elements (list):  Li Mn O など
            output (str): ディクトリ付きならば bb/POTCAR などと書けばいい

        Returns:

        """
        # builder = VaspPotcarBuilder("~/potpaw_PBE.64")
        # path = Path(output).expanduser()
        # if path.is_dir():
        #     path = path / "POTCAR"
        builder = PotcarBuilder("~/potpaw_PBE.64")
        builder.build(elements, output=output)
        # builder.build(elements, output=str(path))
        return True

    @staticmethod
    def convert_to_cfg(
        name: str = "aaa",
    ) -> bool:
        convert_to_cfg(name)
        return True

    #
    # Utilities for vasp
    #

    def contcar2cfg(
        self,
        cfg_name: str = "aaa",
    ) -> bool:
        """
        convert CONTCAR to CFG

        Args:
            cfg_name (str):

        Returns:
            bool:
        """
        self._logger.info(f"== poscar2cfg({cfg_name})")
        contcar2cfg(cfg_name)
        return True

    def poscar2cfg(
        self,
        cfg_name: str = "aaa",
    ) -> bool:
        """
        Convert VASP POSCAR を RMC CFG 形式に変換する
        POSCAR の名前は固定、aaa.cfg ファイル名に変換

        Args:
            cfg_name: str = "aaa": Name of the output file without extension.

        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"== poscar2cfg({cfg_name})")
        # xdatcar2poscar(cfg_name)
        return poscar2cfg(cfg_name)

    def xdatcar2poscar(
        self,
        input_name: Optional[str] = None,
    ) -> bool:
        """
        Copy XDATCAR to a new file with the specified name (... .vasp).
        最終結果だけならば CONTCAR で十分

        Args:
            input_name (str): Name of the new file to create. Without extension.
        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"== xdatcar2poscar({input_name})")
        return xdatcar2poscar(input_name)

    @staticmethod
    def pdb2poscar(
        pdb_name: str = "aaa",
    ):
        atoms = read((str + ".pdb"), format="pdb")
        write((str + ".vasp"), atoms, format="vasp", direct=True)


if __name__ == "__main__":
    _logger = XLogger()
    _vasp_log = VaspLog(logger=_logger)
    vasp = Vasp(
        vasp_log=_vasp_log,
        vasp_name="INCAR",
        mpi_cmd="mpirun",
        mpi_flag="-np",
        num_procs=1,
        dft_bin="vasp_std",
        job_cmd=None,
        logger=_logger,
    )
    print(vasp.NSW)
    print(vasp.EDIFF)
    print(vasp.EDIFFG)
    print(vasp.get_EDIFFG())
    # print(vasp.to_incar())
