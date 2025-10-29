#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
K.KOBAYASHI
"""
import os
import subprocess
from ase.io import read, write

from rmc_dft.config import Config
from rmc_dft.vasp.vasp_log import VaspLog
from rmc_dft.vasp.util.poscar2cfg import poscar2cfg
from rmc_dft.vasp.util.xdatcar2poscar import xdatcar2poscar

from x_logger import XLogger


class Vasp:
    """
    RMD-DFT  のため VASP構造作成 / VASPパラメータ入力 / 実行 /解析用のクラス
    """

    def __init__(
        self,
        vasp_log: VaspLog,
        input_name: str,
        mpi_cmd: str = None,
        mpi_flag: str = None,
        num_procs: int = Config.num_procs,
        vasp_bin: str = Config.vasp_bin,
        job_cmd: str = None,
        logger: XLogger = None,
    ):
        """
        Args:
            vasp_log (VaspLog):
            input_name (str): input_name.vasp
            mpi_cmd (str):
            num_procs (int):
            vasp_bin (str):
            logger (XLogger):  ろがー
        """
        self._vasp_log: VaspLog = vasp_log
        self._input_name = input_name

        if not logger:
            logger = XLogger()
        self._logger = logger
        self._logger.debug("== create Vasp()")

        self.mpi_cmd = mpi_cmd or "mpirun"  # 規定のMPIコマンド
        self.mpi_flag = mpi_flag or "-np"
        self.num_procs = num_procs or Config.num_procs
        self.vasp_bin = vasp_bin or Config.vasp_bin
        self.job_cmd = job_cmd or Config.job_cmd

    def preprocess(self, input_name: str, element_info: str = "label.txt"):
        """
        RMC-DFT において、RMCの結果を持っている状態で、VASP を動かすための前処理

        CFG -> POSCAR (VASP5形式)

        Args:
            input_name (str): xxx.vasp 名前における xxxに相当する名前
            element_info (str):

        Returns:

        """
        # RMC_POT で 結果の CFG から変換した **.vasp に対して
        # element 情報を加える
        # VASP5 形式にする (cfg変換はVASP4形式を吐き出す、RMC_POT は cfg には元素記号を含まないために VASP4 形式のみになる
        self._logger.info("== preprocess()")
        self._logger.info(f"   add_element_name({input_name}.vasp)")
        self.ensure_vasp5_format(
            poscar_name=f"{input_name}.vasp", element_info=element_info
        )

        # POSCAR についても同様の処理を行う
        self._logger.info(f"   add_element_name(POSCAR)")
        self.ensure_vasp5_format(poscar_name="POSCAR", element_info=element_info)

    def postprocess(
        self,
        log_dir: str,
        input_name: str | None = None,
    ):
        """

        Args:
            log_dir:
            input_name:

        Returns:

        """
        self._logger.info("== postprocess()")

        if not input_name:
            input_name = self._input_name

        # VASP のログから必要な結果を取得する
        self._vasp_log.collect_result()

        # VASP のログを指定ディレクトリに保存する
        self._vasp_log.backup_result(log_dir)

        # もし、VASP4 形式ならば VASP5 形式に変換する(重複作業OK)
        self.ensure_vasp5_format(f"{input_name}.vasp")
        self.ensure_vasp5_format("XDATCAR")

        self._logger.info(f"== xdatcar2poscar({input_name})")
        self.xdatcar2poscar(input_name)

        self._logger.info(f"== poscar2cfg({input_name})")
        self.poscar2cfg(input_name)

    def run(
        self,
        mode: str = "local",
        job_cmd: str = None,
        postprocess: bool = True,
        preprocess: bool = True,
        blocking: bool = True,
    ) -> bool:
        """
        VASP を実行する

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

        # preprocess
        if preprocess:
            self.preprocess(self._input_name)

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

        # postprocess
        if postprocess:
            self.postprocess(self._input_name)
        return True

        self._logger.info("=== run()")
        # subprocess.run(f"{Config.vasp_bin}", check=True, shell=True)
        subprocess.run(
            ["mpirun", "-np", f"{Config.num_procs}", f"{Config.vasp_bin}"], check=True
        )
        return True

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

    @staticmethod
    def poscar2cfg(
        cfg_name: str = "aaa",
    ):
        """
        Convert VASP XDATCAR/POSCAR を RMC CFG 形式に変換する

        Args:
            cfg_name: str = "aaa": Name of the output file without extension.

        Returns:
            bool: 正しく終わったデー
        """
        xdatcar2poscar(cfg_name)
        poscar2cfg(cfg_name)
        return True

    def ensure_vasp5_format(
        self,
        poscar_name: str = "aaa.vasp",
        element_info: str | None = None,
    ) -> bool:
        """
        VASPファイルの6行目にラベルを設定する
        VASP4 type POSCAR to VASP5 type POSCAR
        繰り返し実行しても副作用はない

        RMC pot の cfg 形式は元素名がないために、POSCAR 形式に変換したときに困る場合があるので
        VASP5 形式にする( cfg2poscar は element 情報がない VASP4 形式)

        Args:
            poscar_name (str): POSCARファイル名
            element_info (str): element 情報があるファイル名

        Returns:
            bool: True/False
        """
        if element_info is None:
            element_info = "label.txt"

        # element 情報があるファイルを開く
        try:
            with open(element_info, "r") as file:
                label_line = file.readline().strip()
        except FileNotFoundError:
            print(f"File not found.")

        with open(poscar_name, "r") as file:
            lines = file.readlines()
            label_place = 6
        if 1 <= label_place <= len(lines):
            lines[label_place - 1] = label_line + "\n"  # 改行を付けて置換

            # ファイルに上書き保存
            with open(poscar_name, "w") as file:
                file.writelines(lines)
            self._logger.info(f"{poscar_name} label back.")
        else:
            self._logger.info("error: line number out of range.")

        return True

    #
    # Utilities
    #

    def xdatcar2poscar(
        self,
        input_name: str | None = None,
    ):
        """
        Copy XDATCAR to a new file with the specified name (... .vasp).

        Args:
            input_name (str): Name of the new file to create. Without extension.
        Returns:
            bool: 正しく終わったデー
        """
        self._logger.info(f"== xdatcar2poscar({input_name})")
        xdatcar2poscar(input_name)

    @staticmethod
    def pdb2poscar(pdb_name: str = "aaa"):
        atoms = read((str + ".pdb"), format="pdb")
        write((str + ".vasp"), atoms, format="vasp", direct=True)
