"""
RMC-VASP の手動実行順序を指定する設定ファイル。

manual_sequence:
    上から順に実行する。

continue_rmc_dft:
    False:
        manual_sequence に書いた処理だけを実行して終了する。
        sequence を通常スクリプトの補完として使う場合。

    True:
        manual_sequence を実行した後、
        rmc_vasp_script_sequence.py の通常 RMC-DFT ループへ移る。
        sequence script 単独で一連の計算を継続させる場合。
"""

# False: sequence に書いた処理だけで終了
# True : sequence 終了後、通常の RMC-DFT を継続
continue_rmc_dft = False

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
    "rmc_init_5.py",
    "rmc_vasp_init_6.py",
]
