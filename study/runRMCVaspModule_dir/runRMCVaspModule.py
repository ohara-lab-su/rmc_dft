# Python script to run rmc_vasp as a module from code
from vasp.vasp import UtilVasp
from rmc.rmc_pot import UtilRmc
from x_logger.x_logger import XLogger
from rmc_vasp.main import run  # main.py の run() を呼び出す

def main():
    # ロガーの初期化
    logger = XLogger(log_level="debug", logger_name="kobayashi")

    # 実行用オブジェクトの作成
    vasp = UtilVasp(logger=logger)
    rmc = UtilRmc()

    # 実行時の最大ループ数などを設定して実行
    max_loops = 10
    run(vasp, rmc, max=max_loops, logger=logger)

if __name__ == "__main__":
    main()
