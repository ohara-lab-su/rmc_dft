#!/usr/bin/env python3
from rmc_dft import RmcPotLog


r = RmcPotLog(cfg_name="aaa")
r._scan_loops_inspect(0)

# def main(cfg_name: str) -> None:
#     # RMC の cfg_name.log ログファイルを読み込む
#     rmc = RmcPotLog(cfg_name=cfg_name)
#
#     # RMC ブロック数（RMC 単体なら通常 1、RMC–VASP なら 2 以上もあり得る）
#     num_blocks = rmc.get_num_rmc_block()
#
#     print(f"RMC Blocks: {num_blocks}")
#
#     for b in range(num_blocks):
#         num_loops = rmc.get_num_rmc_loop(b)
#         print(f"\n=== RMC BLOCK {b} : Loops = {num_loops} ===")
#
#         for l in range(num_loops):
#             generated = rmc.get_generated(b, l)
#             tried = rmc.get_tried(b, l)
#             accepted = rmc.get_accepted(b, l)
#             gchi2 = rmc.get_global_chi2(b, l)
#             dchi2 = rmc.get_dataset_chi2(b, l)
#             rw = rmc.get_rw(b, l)
#
#             print(f"\n  LOOP {l}")
#             print(f"    GENERATED    : {generated}")
#             print(f"    TRIED        : {tried}")
#             print(f"    ACCEPTED     : {accepted}")
#             print(f"    Global χ²    : {gchi2}")
#             print(f"    Dataset χ²   : {dchi2}")
#             print(f"    Rw (%)       : {rw}")


# if __name__ == "__main__":
#    main("aaa")
