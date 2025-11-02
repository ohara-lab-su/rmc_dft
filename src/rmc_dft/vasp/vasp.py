#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com (1st, 3rd varsion)
K.KOBAYASHI (2nd version)
"""
import os
from typing import Any, Dict, List, Optional
import subprocess
import shutil

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
        vasp_log: VaspLog,
        vasp_name: str,
        incar_name: str = "INCAR",
        kpoints_name: str = "KPOINTS",
        auto_write: bool = True,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = Config.num_procs,
        vasp_bin: str = Config.vasp_bin,
        job_cmd: str = None,
        logger: XLogger = None,
    ):
        """
        Args:
            vasp_log (VaspLog): VASP の log 解析管理
            vasp_name (str): POSCAR などに関連する系の識別名（例: "aaa.vasp" or "POSCAR）
            incar_name (str): INCAR
            kpoints_name (str): KPOINTS
            mpi_cmd (str): 例 "mpirun"
            mpi_flag (str): 例 "-np"
            num_procs (int): 並列数
            vasp_bin (str): 実行バイナリ（例: "vasp_std"）
            job_cmd (str): ジョブ投入コマンド（None ならローカル実行）
            logger (XLogger):  ろがー
        """
        if not logger:
            logger = XLogger()
        self._logger = logger
        self._logger.debug("== create Vasp()")

        # INCAR ファイルのOUTファイル入出力インスタンスの移譲を受ける
        self._vasp_log: VaspLog = vasp_log

        self._vasp_name: str = vasp_name
        self.incar_name: str = incar_name
        self.kpoints_name: str = kpoints_name

        # -------------------------------
        # デフォルト値定義
        # -------------------------------
        self._incar_defaults: dict[str, object] = {
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

        # デフォルト KPOINTS ファイル内容
        self.kpoints_defaults = """K-Points
0
Monkhorst-Pack or Gamma
1 1 1
0 0 0
"""

        # VASP 実行系設定
        self.mpi_cmd = mpi_cmd or "mpirun"  # 規定のMPIコマンド
        self.mpi_flag = mpi_flag or "-np"
        self.num_procs: int = num_procs or Config.num_procs
        self.vasp_bin: str = vasp_bin or Config.vasp_bin
        self.job_cmd = job_cmd or Config.job_cmd

        # --- INCAR ---
        self._incar = VaspIncar(
            incar_name=self.incar_name,
            auto_write=self.auto_write,
            logger=self._logger,
        )
        # INCAR が存在すれば読み込み、なければデフォルトで新規作成
        if not os.path.exists(self.incar_name):
            for key, val in self.incar_defaults.items():
                self._incar.set(key, val)

        # --- KPOINTS ---
        self._kpoints = VaspKpoints(
            kpoints_name=self.kpoints_name,
            auto_write=self.auto_write,
            logger=self._logger,
        )
        # KPOINTS が存在すれば読み込み、なければデフォルトで新規作成
        if not os.path.exists(self.kpoints_name):
            with open(self.kpoints_name, "w") as f:
                f.write(self.kpoints_defaults)

    # --- 委譲メソッド群 (INCAR) ---
    def get_tag(self, key: str):
        """INCAR の値を取得"""
        return self._incar.get(key)

    def set_tag(self, key: str, value):
        """INCAR の値を設定"""
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

    def init(self, cfg_name: str = None):
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

    def preprocess(
        self,
        vasp_name: str = "aaa",
        element_info: str = "label.txt",
    ) -> bool:
        """
        vasp 前処理

        基本的に Vasp Class は相手がなんであれ動くようにする
        それは入力が常に VASP であることを仮定していて、
        相手のプログラム側の postprocess or convert してから動かすことを全手とする

        xxx.vasp (VASP4) --> xxx.vasp (VASP5)

        Args:
            vasp_name (str): xxx.vasp 名前における xxxに相当する名前
            element_info (str):

        Returns:
            bool:
        """
        self._logger.info("== preprocess()")
        return True

    def postprocess(
        self,
        log_dir: str = "log_vasp",
        cfg_name: str | None = None,
    ) -> bool:
        """
        後処理

        1) DATA-collect
        2) BACKUP
        3) CONTCAR --> POSCAR
        4) CONTCAR --> CFG (for RMC_POT)


        Args:
            log_dir (str):
            cfg_name (str): POSCAR -> cfg_name.cfg

        Returns:
            bool:
        """
        self._logger.info("== postprocess()")

        if not cfg_name:
            cfg_name = self._cfg_name
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

    #
    # VASP run
    #

    def run(
        self,
        mode: str = "local",
        job_cmd: str = None,
        postprocess: bool = False,
        preprocess: bool = False,
        blocking: bool = True,
    ) -> bool:
        """
        VASP を実行する

        local 実行
        FI_PROVIDER="TCP"
        I_MPI_FABRICS="shm:tcp"
        I_MPI_DEBUG="5"

        Args:
            mode (str): "local" vasp_bin
                        "mpi" mpi_cmd + mpi_flag + num_procs + vasp_bin
                        "job" job_cmd + vasp_bin
            job_cmd (str): ジョブコマンド(mode=job時に使う)
                        　　優先順番
                           instance(job_cmd=xxx)< set_job_cmd(xxx) < run(job_cmd=xxx)
            postprocess (bool): RMC-VASP 用の postprocess を run 中に行う
            preprocess (bool): RMC-VASP 用の postprocess を run 中に行う
            blocking (bool):  subprocessをブロッキングで起動(default: True)

        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"=== run(mode={mode}) ===")

        # すべてのモードで共通の環境変数を定義
        env = os.environ.copy()

        ########################
        if preprocess:
            self.preprocess(self._input_name)
        ########################

        if mode == "local":
            # MPI build された vasp を local で動かすためのもの (infinibandを使わない)
            env["FI_PROVIDER"] = "tcp"
            env["I_MPI_FABRICS"] = "shm:tcp"
            env["I_MPI_DEBUG"] = "5"
            cmd = ["mpirun", "-np", "1", f"{self.vasp_bin}"]
            # cmd = [self.vasp_bin]

        elif mode == "mpi":
            cmd = [self.mpi_cmd, self.mpi_flag, str(self.num_procs), self.vasp_bin]

        elif mode == "job":
            if not job_cmd:
                job_cmd = self.job_cmd
            cmd = [job_cmd]

        else:
            raise ValueError(f"未知の mode: {mode}")

        self._logger.info("Executing: " + " ".join(cmd))
        subprocess.run(cmd, check=True, env=env)

        ########################
        if postprocess:
            self.postprocess(self._input_name)
        ########################

        return True

        self._logger.info("=== run()")
        # subprocess.run(f"{Config.vasp_bin}", check=True, shell=True)
        subprocess.run(
            ["mpirun", "-np", f"{Config.num_procs}", f"{Config.vasp_bin}"], check=True
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
        element_info: str | None = None,
        logger: XLogger = None,
    ) -> bool:
        return ensure_vasp5_format(poscar_name, element_info, logger=logger)

    @staticmethod
    def make_potential(
        elements: list[str],
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
        self,
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

        Args:
            cfg_name: str = "aaa": Name of the output file without extension.

        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"== poscar2cfg({cfg_name})")
        # xdatcar2poscar(cfg_name)
        poscar2cfg(cfg_name)
        return True

    def xdatcar2poscar(
        self,
        input_name: str | None = None,
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
        xdatcar2poscar(input_name)
        return True

    @staticmethod
    def pdb2poscar(pdb_name: str = "aaa"):
        atoms = read((str + ".pdb"), format="pdb")
        write((str + ".vasp"), atoms, format="vasp", direct=True)


if __name__ == "__main__":
    _logger = XLogger()
    _vasp_log = VaspLog(logger=_logger)
    vasp = Vasp(
        _vasp_log,
        vasp_name="INCAR",
        mpi_cmd="mpirun",
        mpi_flag="-np",
        num_procs=1,
        vasp_bin="vasp_std",
        job_cmd=None,
        logger=_logger,
    )
    print(vasp.NSW)
    print(vasp.EDIFF)
    print(vasp.EDIFFG)
    print(vasp.get_EDIFFG())
    # print(vasp.to_incar())
