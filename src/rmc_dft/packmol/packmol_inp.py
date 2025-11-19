#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
"""


class PackmolInp:
    """
    Packmol の .inp ファイルを構築するための単純なクラス。

    builder = PackmolInp(
        tolerance=2.3,
        output_xyz="result.xyz",
        box_length=L)

    builder.add_structure("Fe.xyz", N_Fe)
    builder.add_structure("Si.xyz", N_Si)
    builder.add_structure("B.xyz", N_B)

    builder.write("packmol.inp")
    """

    def __init__(
        self,
        tolerance: float,
        output_xyz: str,
        box_length: float,
    ):
        self.tolerance = tolerance
        self.output_xyz = output_xyz
        self.box_length = box_length
        self.structure_blocks = []

    def add_structure(
        self,
        xyz_file: str,
        number: int,
    ) -> None:
        """
        1つの分子（元素）に対する structure ブロックを登録する。
        """
        block = {
            "xyz": xyz_file,
            "number": number,
        }
        self.structure_blocks.append(block)

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        .inp ファイルを書き出す。
        """
        L = self.box_length

        with open(inp_file, "w") as f:
            # ヘッダ
            f.write(f"tolerance {self.tolerance}\n")
            f.write("filetype xyz\n")
            f.write(f"output {self.output_xyz}\n\n")

            # 各 structure ブロック
            for blk in self.structure_blocks:
                xyz = blk["xyz"]
                num = blk["number"]

                f.write(f"structure {xyz}\n")
                f.write(f"  number {num}\n")
                f.write(f"  inside box 0.0 0.0 0.0  {L:.6f} {L:.6f} {L:.6f}\n")
                f.write("end structure\n\n")
