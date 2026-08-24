"""
RMC-VASP の手動実行順序を指定する設定ファイル。

上から順に実行する。
手動シーケンス終了後は、rmc_vasp_script_sequence.py 側の
通常 RMC-DFT ループへ戻る。
"""

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
    "rmc_init_5.py",
    "rmc_vasp_init_6.py",
]
