#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com
K.KOBAYASHI
"""
import os
import subprocess
from typing import Any, Dict, List, Optional

from ase.io import read, write

from rmc_dft.config import Config
from rmc_dft.vasp.vasp_log import VaspLog
from rmc_dft.vasp.util.poscar2cfg import (
    vasp2cfg,
    contcar2cfg,
    poscar2cfg,
    convert_to_cfg,
)
from rmc_dft.vasp.util.copy_contcar_to_vasp import copy_contcar_to_vasp
from rmc_dft.vasp.util.copy_vasp_to_poscar import copy_vasp_to_poscar
from rmc_dft.vasp.util.xdatcar2poscar import xdatcar2poscar
from rmc_dft.vasp.util.make_poscar import PotcarBuilder

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

        # for VASP INCAR
        self._incar_keys: Dict[str, Any] = {
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
        # 各キーに対応する property / get_xxx, set_xxx をクラスに動的追加
        for key in list(self._incar_keys.keys()):
            self._install_property(key)

    #
    # INTCAR
    #

    def _install_property(self, key: str) -> None:
        """
        属性アクセスを get_{KEY} / set_{KEY} にバインド。
        それらが存在しなければ辞書を既定動作とする。
        """

        def fget(inst: Vasp, k: str = key) -> Any:
            getter = getattr(inst, f"get_{k}", None)
            if callable(getter):
                return getter()  # 高度な getter を必ず経由
            return inst._incar_keys.get(k)  # 既定（辞書）取得

        def fset(inst: Vasp, value: Any, k: str = key) -> None:
            setter = getattr(inst, f"set_{k}", None)
            if callable(setter):
                setter(value)  # 高度な setter を必ず経由
            else:
                inst._incar_keys[k] = value  # 既定（辞書）更新

        # クラスに property を貼る（以後 instance.k で fget/fset が必ず呼ばれる）
        setattr(self.__class__, key, property(fget, fset))

    def set_EDIFF(self, EDIFF: float) -> None:
        self._incar_keys["EDIFF"] = float(EDIFF)
        self._incar_keys["EDIFFG"] = float(EDIFF) * 10

    def get_EDIFFG(self) -> float:
        self._incar_keys["EDIFFG"] = float(self.EDIFF) * 10
        return self._incar_keys["EDIFFG"]

    #
    # RMC-DFT の VASP 側の init/preprocess/postprocess
    #

    def init(self, input_name: str = None):
        """POSCAR から cfg を作る"""
        if input_namei is None:
            input_name = self._input_name

        self._logger.info("== init()")

        # POSCAR から CFG を作成
        self._logger.info(f"== poscar2cfg({input_name})")
        self.poscar2cfg(_input_name)

    def preprocess(
        self,
        input_name: str,
        element_info: str = "label.txt",
    ) -> bool:
        """
        vasp 前処理

        xxx.vasp (VASP4) --> xxx.vasp (VASP5)

        Args:
            input_name (str): xxx.vasp 名前における xxxに相当する名前
            element_info (str):

        Returns:
            bool:
        """
        self._logger.info("== preprocess()")

        # RMC_POT で 結果の CFG から変換した **.vasp に対して
        # element 情報を加える(VASP5 形式にする)
        # cfg変換はVASP4形式を吐き出す
        # RMC_POT は cfg には元素記号を含まないために VASP4 形式のみになる

        self._logger.info(f"   add_element_name({input_name}.vasp)")
        self.ensure_vasp5_format(
            poscar_name=f"{input_name}.vasp",
            element_info=element_info,
        )

        # input_name.vasp --> POSCAR
        copy_vasp_to_poscar(input_name)

        # # POSCAR についても同様の処理を行う
        # self._logger.info(f"   add_element_name(POSCAR)")
        # self.ensure_vasp5_format(
        #     poscar_name="POSCAR",
        #     element_info=element_info,
        # )

        return True

    def postprocess(
        self,
        log_dir: str,
        input_name: str | None = None,
    ) -> bool:
        """
        後処理

        Args:
            log_dir (str):
            input_name (str):

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
        # self.ensure_vasp5_format(f"{input_name}.vasp")
        # self.ensure_vasp5_format("XDATCAR")

        # self._logger.info(f"== xdatcar2poscar({input_name})")
        # self.xdatcar2poscar(input_name)

        # self._logger.info(f"== poscar2cfg({input_name})")
        # self.poscar2cfg(input_name)

        # CONTCAR -> CFG
        self.contcar2cfg(input_name)
        return True

    #
    # VASP run
    #

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

    @staticmethod
    def make_potential(
        elements: list[str],
        output: str = "POTCAR",
    ) -> bool:
        """
        PotcarBuilder クラスを使って POTCAR を生成

        Args:
            elements (list):  Li Mn O など
            output (str): ディクトリ付きならば bb/POTCAR などと書けばいい

        Returns:

        """
        # builder = PotcarBuilder("~/potpaw_PBE.64")
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

    def to_incar(self) -> str:
        """
        設定してある VASP の INCAR タグを表示

        Returns:
            str:

        """
        lines = []
        for k, v in self._incar_keys.items():
            if v is None:
                continue
            if isinstance(v, bool):
                s = ".TRUE." if v else ".FALSE."
            elif isinstance(v, (list, tuple)):
                s = " ".join(str(x) for x in v)
            else:
                s = str(v)
            lines.append(f"{k} = {s}")
        return "\n".join(lines)

    def write_incar(self, filepath: Optional[str] = None) -> str:
        """
        既存の to_incar() を用いて INCAR テキストを生成し、指定パスに書き出し
        相対 / 絶対どちらのパスでも可。

        Args:
            filepath (str, optional): 出力ファイルのパス。
                None の場合はカレントディレクトリに 'INCAR' として出力。

        Returns:
            str: 書き出したファイルの絶対パス
        """
        if filepath is None:
            filepath = "INCAR"

        incar_text: str = self.to_incar()

        dirpath = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(incar_text if incar_text.endswith("\n") else incar_text + "\n")

        return os.path.abspath(filepath)


if __name__ == "__main__":
    logger = XLogger()
    vasp_log = VaspLog(logger=logger)
    vasp = Vasp(
        vasp_log,
        input_name="INCAR",
        mpi_cmd="mpirun",
        mpi_flag="-np",
        num_procs=1,
        vasp_bin="vasp_std",
        job_cmd=None,
        logger=logger,
    )
    print(vasp.NSW)
    print(vasp.EDIFF)
    print(vasp.EDIFFG)
    print(vasp.get_EDIFFG())
    print(vasp.to_incar())
