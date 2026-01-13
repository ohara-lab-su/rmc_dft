#!/usr/bin/env python3
"""
log ファイルからRMCの収束に関する結果を抜き出す。
(こちらが hst の下情報になるが、整理されている形式ではないので注意)
"""
from rmc_dft import RmcPotLog

####################
# test0
# r = RmcPotLog(cfg_name="aaa")
# r._scan_loops_inspect(0)

####################
# test1
# r = RmcPotLog(cfg_name="aaa")
# r._inspect_moves(0)


####################
# test2
# log = RmcPotLog(cfg_name="aaa")
#
# # --- ブロック検出 ---
# blocks = log._scan_rmc_blocks()
# print("blocks =", blocks)
#
# # テストなので block=0 だけ使う
# b_start, b_end = blocks[0]
# if b_end < 0:
#     b_end = len(log._log_lines) - 1
#
# print("block range =", b_start, b_end)
#
# # --- _scan_moves を直接叩く（これがテスト本番） ---
# moves = log._scan_moves(b_start, b_end)
#
# print("=== moves detected ===")
# print("count =", len(moves))
#
# for i, (g, t, a) in enumerate(moves):
#     print(f"{i:3d} : GENERATED={g}, TRIED={t}, ACCEPTED={a}")


####################
# test3
# r = RmcPotLog(cfg_name="aaa")
# print(r.get_generated(0, 0))
# print(r.get_generated(0, 1))
# print(r.get_generated(0, 2))
#
# for i in range(r.get_num_rmc_loop(0)):
#     print(
#         i,
#         r.get_chi2_tot(0, i),
#         r.get_chi2_dataset(0, i),
#         r.get_rw(0, i),
#     )


def main(cfg_name: str) -> None:
    # RMC の cfg_name.log ログファイルを読み込む
    rmc = RmcPotLog(cfg_name=cfg_name)

    # RMC ブロック数（RMC 単体なら通常 1、RMC–VASP なら 2 以上もあり得る）
    num_blocks = rmc.get_num_rmc_block()

    print(f"RMC Blocks: {num_blocks}")

    for b in range(num_blocks):
        num_loops = rmc.get_num_rmc_loop(b)
        print(f"\n=== RMC BLOCK {b} : Loops = {num_loops} ===")

        for l in range(num_loops):
            generated = rmc.get_generated(b, l)
            tried = rmc.get_tried(b, l)
            accepted = rmc.get_accepted(b, l)
            gchi2 = rmc.get_chi2_tot(b, l)
            dchi2 = rmc.get_chi2_dataset(b, l)
            rw = rmc.get_rw(b, l)

            # HST の 8要素に合わせて、ログに存在する 6要素に「比率 2要素」を足す
            tried_per_generated = None
            if generated is not None:
                if generated != 0:
                    if tried is not None:
                        tried_per_generated = tried / generated

            accepted_per_tried = None
            if tried is not None:
                if tried != 0:
                    if accepted is not None:
                        accepted_per_tried = accepted / tried

            print(f"\n  LOOP {l}")
            print(f"    GENERATED    : {generated}")
            print(f"    TRIED        : {tried}")
            print(f"    ACCEPTED     : {accepted}")
            print(f"    TRIED/GENERATED     : {tried_per_generated}")
            print(f"    ACCEPTED/TRIED      : {accepted_per_tried}")
            print(f"    Global χ²    : {gchi2}")
            print(f"    Dataset χ²   : {dchi2}")
            print(f"    Rw (%)       : {rw}")


if __name__ == "__main__":
    main("aaa")
