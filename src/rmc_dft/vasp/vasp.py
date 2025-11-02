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
from rmc_dft.vasp.vasp_incar_writer import VaspIncarWriter
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
from rmc_dft.vasp.util.ensure_vasp5_format import ensure_vasp5_format
from rmc_dft.vasp.util.make_potcar import VaspPotcarBuilder

from x_logger import XLogger


class Vasp:
    """
    RMD-DFT  のため VASP構造作成 / VASPパラメータ入力 / 実行 /解析用のクラス
    """

    def __init__(
        self,
        vasp_log: VaspLog,
        vasp_name: str,
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
            mpi_cmd (str): 例 "mpirun"
            mpi_flag (str): 例 "-np"
            num_procs (int): 並列数
            vasp_bin (str): 実行バイナリ（例: "vasp_std"）
            job_cmd (str): ジョブ投入コマンド（None ならローカル実行）
            logger (XLogger):  ろがー
        """
        self._vasp_name: str = vasp_name

        # INCAR ファイルのOUTファイル入出力インスタンスの移譲を受ける
        self._vasp_log: VaspLog = vasp_log

        if not logger:
            logger = XLogger()
        self._logger = logger
        self._logger.debug("== create Vasp()")

        # 実行系設定
        self.mpi_cmd = mpi_cmd or "mpirun"  # 規定のMPIコマンド
        self.mpi_flag = mpi_flag or "-np"
        self.num_procs: int = num_procs or Config.num_procs
        self.vasp_bin: str = vasp_bin or Config.vasp_bin
        self.job_cmd = job_cmd or Config.job_cmd

        # INCAR (VASP利用のための INCAR 編集なので基本的には名前を変更しない)
        self.incar_name: str = "INCAR"

        # INCAR の値管理
        self._logger.info(f"== VaspIncar({self.incar_name})")
        self._incar_logic: VaspIncar = VaspIncar(incar_name=self.incar_name)

        # INCAR 書き込み管理 (実態としては INCAR 読み書きの中心となる)
        self._incar_writer: VaspIncarWriter = VaspIncarWriter(
            incar_name=self.incar_name
        )

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

        # ファイルが既にある場合は、その内容で _incar_keys を更新しておく
        # （get_*/property アクセス互換のための初期化）
        self._sync_incar_keys_from_file()

        # 各キーに対応する property / get_xxx, set_xxx をクラスに動的追加
        for key in list(self._incar_keys.keys()):
            self._install_property(key)

    #
    # INTCAR
    #

    def _sync_incar_keys_from_file(self) -> None:
        """
        既存 INCAR の内容を読み出し、辞書 _incar_keys を初期同期する。
        """
        try:
            current: Dict[str, Any] = self._incar_logic.export_dict()
        except Exception:
            current = {}

        for k in self._incar_keys.keys():
            # 既存ファイルに値があれば反映。なければ既定値のまま
            if k in current:
                self._incar_keys[k] = current[k]

    def _install_property(self, key: str) -> None:
        """
        属性アクセスを get_{KEY} / set_{KEY} にバインド。
        それらが無い場合でも、値の取得は「ファイル --> 辞書」の順で行い、
        値の設定は「VaspIncar + VaspIncarWriter + Dict (local)」を同時更新する。
        """

        # def fget(inst: Vasp, k: str = key) -> Any:
        #     getter = getattr(inst, f"get_{k}", None)
        #     if callable(getter):
        #         return getter()  # 高度な getter を必ず経由
        #     return inst._incar_keys.get(k)  # 既定（辞書）取得

        # def fset(inst: Vasp, value: Any, k: str = key) -> None:
        #     setter = getattr(inst, f"set_{k}", None)
        #     if callable(setter):
        #         setter(value)  # 高度な setter を必ず経由
        #     else:
        #         inst._incar_keys[k] = value  # 既定（辞書）更新

        def fget(inst: "Vasp", k: str = key) -> Any:
            # 1) 高度 getter があれば優先
            getter = getattr(inst, f"get_{k}", None)
            if callable(getter):
                return getter()

            # 2) VastIncar（= 現在のファイル内容）を優先
            value = inst._incar_logic.get_value(k)
            if value is not None:
                return value

            # 3) 互換辞書
            return inst._incar_keys.get(k)

        def fset(inst: "Vasp", value: Any, k: str = key) -> None:
            # 1) 高度 setter があれば優先
            setter = getattr(inst, f"set_{k}", None)
            if callable(setter):
                setter(value)
                return

            # 2) 値の正規化（True/False, list 等はそのまま）
            normalized = value

            # 3) VaspIncar へ反映
            inst._incar_logic.set_value(k, normalized)

            # 4) VaspInvarWriter へ反映（コメント保持の実ファイル編集）
            inst._incar_writer.set_tag(k, normalized)

            # 5) 互換辞書を同期
            inst._incar_keys[k] = normalized

        # クラスに property を貼る（以後 instance.k で fget/fset が必ず呼ばれる）
        setattr(self.__class__, key, property(fget, fset))

    def set_EDIFF(self, EDIFF: float) -> None:
        """
        EDIFF 設定時に EDIFFG を自動調整し、ファイルにも反映する。

        Args:
            EDIFF:

        Returns:

        """
        ediff_val = float(EDIFF)
        self._incar_keys["EDIFF"] = ediff_val
        self._incar_keys["EDIFFG"] = ediff_val * 10

        # 論理層＋物理層へ反映
        self._incar_logic.set_value("EDIFF", ediff_val)
        self._incar_logic.set_value("EDIFFG", ediff_val * 10.0)
        self._incar_writer.set_tag("EDIFF", ediff_val)
        self._incar_writer.set_tag("EDIFFG", ediff_val * 10.0)

    def get_EDIFFG(self) -> float:
        """
        DIFF から EDIFFG を計算（ファイルに値があればそちらを優先）
        """
        file_val = self._incar_logic.get_value("EDIFFG")
        if file_val is not None:
            return float(file_val)

        base = self.EDIFF  # fget 経由でファイル/辞書の順に取得
        val = float(base) * 10.0

        # 互換辞書も同期
        self._incar_keys["EDIFFG"] = val
        return val

    #
    # INCAR の明示操作
    #

    def get_tag(self, tag_name: str) -> Optional[Any]:
        """
        任意タグの現在値を取得（ファイル→辞書の順に評価）。
        """
        tag_upper = tag_name.upper()
        value = self._incar_logic.get_value(tag_upper)
        if value is not None:
            return value
        return self._incar_keys.get(tag_upper)

    def set_tag(self, tag_name: str, value: Any) -> None:
        """
        任意タグを追加・更新。コメント・空行は保持される。
        """
        tag_upper = tag_name.upper()
        self._incar_logic.set_value(tag_upper, value)
        self._incar_writer.set_tag(tag_upper, value)
        self._incar_keys[tag_upper] = value

    def remove_tag(self, tag_name: str) -> None:
        """
        任意タグを削除（コメント・空行は保持）
        """
        tag_upper = tag_name.upper()
        self._incar_logic.remove_value(tag_upper)
        self._incar_writer.remove_tag(tag_upper)
        if tag_upper in self._incar_keys:
            del self._incar_keys[tag_upper]

    def reload_incar(self) -> None:
        """
        外部エディタ等で INCAR が変更された場合に再読み込みする
        論理層＋物理層の両方を再同期し、互換辞書も更新する
        """
        self._incar_logic.reload_incar()
        self._incar_writer = VaspIncarWriter(incar_name=self.incar_name)
        self._sync_incar_keys_from_file()

    #
    # 旧来の to_incar / write_incar 互換
    # INCAR のコメント保持が必要な運用では set_tag()/remove_tag() を使用すること
    #

    def to_incar(self) -> str:
        """
        内部辞書からシリアライズ（コメントは付かない）

        既存 INCAR のコメント保持を要する場合は使用せず、
        set_tag()/remove_tag() とファイルベースで運用する。
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
