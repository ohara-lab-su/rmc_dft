#!/usr/bin/env python
"""
K.NAKADA, kengo.nakada@gmail.com (2nd version)
K.KOBAYASHI (1st version)
"""
import os
import sys

import glob
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

from x_logger import XLogger


class VaspLog:
    """
    VASP の出力ファイルを計算後に整理・解析するクラス
    """

    def __init__(self, logger: XLogger = None):
        if not logger:
            logger = XLogger()
        self._logger = logger

    #
    # Vcopy 互換
    #

    @staticmethod
    def _exists_either(
        path: Path,
    ) -> bool:
        """通常 or .gz のどちらかが存在するか"""
        return path.exists() or path.with_suffix(path.suffix + ".gz").exists()

    def _copy_either(
        self,
        src: Path,
        dst: Path,
    ) -> None:
        """通常 or .gz を copy。必要に応じて .gz 拡張子を付与"""
        if src.exists():
            shutil.copyfile(src, dst)
            self._logger.info(f"cp {src} --> {dst}")
        else:
            gzsrc = src.with_suffix(src.suffix + ".gz")
            if gzsrc.exists():
                gzdst = Path(str(dst) + ".gz")
                shutil.copyfile(gzsrc, gzdst)
                self._logger.info(f"cp {gzsrc} --> {gzdst}")

    def _move_either(
        self,
        src: Path,
        dst: Path,
    ) -> None:
        """通常 or .gz を move。必要に応じて .gz 拡張子を付与"""
        if src.exists():
            shutil.move(src, dst)
            self._logger.info(f"move {src} --> {dst}")
        else:
            gzsrc = src.with_suffix(src.suffix + ".gz")
            if gzsrc.exists():
                gzdst = Path(str(dst) + ".gz")
                shutil.move(gzsrc, gzdst)
                self._logger.info(f"move {gzsrc} --> {gzdst}")

    def vcopy(self, suffix: str) -> None:
        """
        Vcopy と同等の整理処理を実行（Vcopy2 は未実装）。

        Args:
            suffix (str): 付与する接尾辞（例: "A1" など）
        """
        # --- 事前チェック：OUTCAR or OUTCAR.gz 必須 ---
        if not (Path("OUTCAR").exists() or Path("OUTCAR.gz").exists()):
            raise FileNotFoundError("STOP: OUTCAR and OUTCAR.gz file not found.")

        pid_suffix = f".{os.getpid()}"

        # === copy: INCAR, KPOINTS, POSCAR ===
        for name in ("INCAR", "KPOINTS", "POSCAR", "DOSCAR", "PROCAR", "POTCAR"):
            src = Path(name)
            dst = Path(f"{name.lower()}{suffix}")
            if self._exists_either(dst):
                dst = Path(f"{name.lower()}{suffix}{pid_suffix}")
            self._copy_either(src, dst)

        # === move: OUTCAR, OSZICAR, CHG, CONTCAR, XDATCAR, DOSCAR, EIGENVAL, PROCAR, IBZKPT, PCDAT ===
        for name in (
            "OUTCAR",
            "OSZICAR",
            "CHG",
            "CONTCAR",
            "XDATCAR",
            "DOSCAR",
            "EIGENVAL",
            "PROCAR",
            "IBZKPT",
            "PCDAT",
        ):
            src = Path(name)
            dst = Path(f"{name.lower()}{suffix}")
            if self._exists_either(dst):
                dst = Path(f"{name.lower()}{suffix}{pid_suffix}")
            self._move_either(src, dst)

        # === move: vasprun.xml ===
        src = Path("vasprun.xml")
        dst = Path(f"vasprun{suffix}.xml")
        if self._exists_either(dst):
            dst = Path(f"vasprun{suffix}{pid_suffix}.xml")
        self._move_either(src, dst)

        # === CONTCAR → POSCAR (copy, .gz対応) ===
        #   直前で CONTCAR は move 済み（contcar{suffix}[.gz] に退避）。
        contcar = Path(f"contcar{suffix}")
        contcar_gz = contcar.with_suffix(".gz")

        if contcar.exists() or contcar_gz.exists():
            src_path = contcar_gz if contcar_gz.exists() else contcar
            self._logger.info(f"cp {src_path.name} --> POSCAR")
            if src_path.suffix == ".gz":
                with gzip.open(src_path, "rb") as fin, open("POSCAR", "wb") as fout:
                    shutil.copyfileobj(fin, fout)
            else:
                shutil.copyfile(src_path, "POSCAR")
            # csh版の chmod u+x POSCAR poscar$suffix を踏襲
            os.chmod("POSCAR", 0o744)
            poscar_backup = Path(f"poscar{suffix}")
            if poscar_backup.exists():
                os.chmod(poscar_backup, 0o744)

        # === copy: CHGCAR ===
        chgcar = Path("CHGCAR")
        dst = Path(f"chgcar{suffix}")
        if self._exists_either(dst):
            dst = Path(f"chgcar{suffix}{pid_suffix}")
        self._copy_either(chgcar, dst)

        # === copy: WAVECAR ===
        wavecar = Path("WAVECAR")
        dst = Path(f"wavecar{suffix}")
        if self._exists_either(dst):
            dst = Path(f"wavecar{suffix}{pid_suffix}")
        self._copy_either(wavecar, dst)

        self._logger.info("Vcopy completed.")

    # grep on python
    @staticmethod
    def get_E0(
        input_filename: str = "OSZICAR",
        output_filename: str = "grep_E0_OSZICAR.txt",
        key: str = "E0",
    ):
        """
        OSZICAR から E0 を取り出して、ファイル保存する
        (廃止予定)

        Args:
            input_filename:
            output_filename:
            key:

        Returns:

        """
        input_file = "OSZICAR"
        output_file = "grep_E0_OSZICAR.txt"
        key = "E0"

        with open(output_file, "w") as outfile:
            with open(input_file, "r") as f:
                for line in f.readlines():
                    if key in line:
                        print(line)
                        outfile.writelines(line)

    def collect_result(self):
        """
        VASPのログからひつようなじょうほうをとりだして、保存する
        This function is used to grep energy from OUTCAR file.
        """
        self.get_E0()
        self._logger.info("grep energy from OUTCAR file finished.")

    def backup_result(
        self,
        log_dir: str = "log",
    ):
        """
        Copy VASP log files to the specified directory.

        Args:
            log_dir (str): Directory to copy the log files to.
        """
        import shutil
        import os

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        files_to_copy = [
            "grep_E0_OSZICAR.txt",
            "OUTCAR",
            "OSZICAR",
            "vasprun.xml",
            "XDATCAR",
            "CONTCAR",
            "POSCAR",
            "KPOINTS",
        ]

        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy(file_name, log_dir)
                self._logger.info(f"Copied {file_name} to {log_dir}")
            else:
                self._logger.info(f"{file_name} does not exist, skipping.")

    def remove_file(self, filename: str) -> None:
        """存在するファイルを削除"""
        if os.path.exists(filename):
            os.remove(filename)
            self._logger.info(f"removed: {filename}")

    def remove_pattern(self, pattern: str) -> None:
        """ワイルドカードパターンで一致するファイルを削除"""
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                self._logger.info(f"removed: {f}")
            except FileNotFoundError:
                pass

    def clean(
        self,
        suffixes: List[str] = None,
    ) -> None:
        """
        Args:
            suffixes (str):

        Returns:

        """
        base_files = [
            "AECCAR0",
            "AECCAR1",
            "AECCAR2",
            "LOCPOT",
            "CHG",
            "CHGCAR",
            "CHGCAR_sum",
            "PARCHG",
            "CONTCAR",
            "DOSCAR",
            "EIGENVAL",
            "IBZKPT",
            "OSZICAR",
            "PCDAT",
            "WAVECAR",
            "XDATCAR",
            "PROCAR",
            "OUTCAR",
            "TMPCAR",
            "OUTPAR",
            "ELFCAR",
            "REPORT",
            "vasprun.xml",
            "vaspout.h5",
            "PROJCAR",
            "LOCPROJ",
        ]

        # 共通ワイルドカード削除（lobster, wannier90, job system）
        patterns = [
            "p4vasp.log",
            "*.lobster",
            "lobsterout",
            "*.werr",
            "*.wout",
            "wannier90.chk",
            "wannier90.amn",
            "wannier90.eig",
            "wannier90.mmn",
            "wannier90_*.xsf",
            "wannier90_centres.xyz",
            "UNK*.1",
            "UNK*.2",
            "LSF_*",
            "PBS_*",
            "tmp.*",
        ]

        if not suffixes:
            # 引数なし：通常ファイル削除
            for f in base_files:
                self.remove_file(f)
            for p in patterns:
                self.remove_pattern(p)

        else:
            # 引数あり：サフィックス付きファイル削除
            for suf in suffixes:
                for f in base_files:
                    self.remove_file(f.lower() + suf)
                    self.remove_file(f.lower() + suf + ".gz")
                    self.remove_file(f.upper() + suf)
                    self.remove_file(f.upper() + suf + ".gz")

                # 特殊ケース
                self.remove_file(f"vasprun{suf}.xml")
                self.remove_file(f"vaspout{suf}.h5")
                self.remove_file(f"vasprun{suf}.xml.gz")
                self.remove_file(f"vaspout{suf}.h5.gz")


if __name__ == "__main__":
    vasp_log = VaspLog()
    vasp_log.collect_result()
