#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rmc_dft import Config
from rmc_dft import RmcPotHst


def main():
    # --------------------------------------------------------------
    # HST ロード
    # --------------------------------------------------------------
    # cfg = Config("config.yml")  # sim01.hst を読む想定
    # hst = RmcPotHst(config=cfg)
    hst = RmcPotHst(cfg_name="aaa")

    # --------------------------------------------------------------
    # 総ループ数
    # --------------------------------------------------------------
    total_loops = hst.get_num_loops()
    print(f"Total loops = {total_loops}")
    print("=" * 80)

    # --------------------------------------------------------------
    # loop_index=None で全量取得（各 getter の正常性検証）
    # --------------------------------------------------------------
    print("全ループ取得（loop_index=None）")
    print("-" * 80)

    all_generated = hst.get_generated()
    all_tried = hst.get_tried()
    all_accepted = hst.get_accepted()
    all_time = hst.get_time()
    all_tpg = hst.get_tried_per_gen()
    all_apt = hst.get_acc_per_tried()
    all_chi2_tot = hst.get_chi2_tot()
    all_chi2_set1 = hst.get_chi2_set1()

    print(f"len(generated) = {len(all_generated)}")
    print(f"len(tried)     = {len(all_tried)}")
    print(f"len(accepted)  = {len(all_accepted)}")
    print(f"len(time)      = {len(all_time)}")
    print(f"len(tpg)       = {len(all_tpg)}")
    print(f"len(apt)       = {len(all_apt)}")
    print(f"len(chi2_tot)  = {len(all_chi2_tot)}")
    print(f"len(chi2_set1) = {len(all_chi2_set1)}")

    print("=" * 80)

    # --------------------------------------------------------------
    # 各ループごとの値取得（全 API を loop_index 指定で取得）
    # --------------------------------------------------------------
    print("各ループごとの詳細（全メソッド検証）")
    print("-" * 80)

    for loop in range(total_loops):
        gen = hst.get_generated(loop)
        tri = hst.get_tried(loop)
        acc = hst.get_accepted(loop)
        tim = hst.get_time(loop)
        tpg = hst.get_tried_per_gen(loop)
        apt = hst.get_acc_per_tried(loop)
        ctot = hst.get_chi2_tot(loop)
        cset = hst.get_chi2_set1(loop)

        print(
            f"[loop {loop:4d}] "
            f"generated={gen:10d}  tried={tri:10d}  accepted={acc:6d}  "
            f"time={tim:4d}  "
            f"tpg={tpg:.6f}  apt={apt:.6f}  "
            f"chi2_tot={ctot:.6e}  chi2_set1={cset:.6e}"
        )

    print("=" * 80)
    print("全メソッド検証完了")


if __name__ == "__main__":
    main()
