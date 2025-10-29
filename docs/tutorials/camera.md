# カメラ

*) 必ず、local で直接 CobottaCtrl を使うときは、終了時には disconnect する
KeyboardInterrupt を含めて異常終了するときは disconnect しておく

## python からの基本的な使い方

```python
from cobotta2 import Config, CobottaCtrl, MotionMode

Config.load_yaml("config_cobotta2.yaml")
logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
cobotta = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, arm_name="Arm", logger=logger)

try:
    cobotta.reset_error()
    
    # カメラでの画像認識の個数（認識の成功失敗判定に使う)
    cobotta.I2 = 0
    
    # カメラの画像認識の結果が入る座標、ワーク座標
    # 現在の座標を安全のための初期位置として記録
    cobotta.P10 = cobotta.get_current_position()

    # take_script() と take_camera() は排他的なので注意
    # take_camera() 事前に take_arm() していたら release_arm する
    cobotta.release_arm()
    
    while True:
        logger.info("---------- カメラで画像認識 -------------------")
        
        # EVP2 ガイダンスで作成した カメラの画像認識モデルを選ぶ
        evp_script_name = "try_camera"
        
        # EVP2_03.pcs の名前はなんでもよい。ただし、既存のcobotta内部のスクリプトを上書きしてしまうので注意
        cobotta.take_camera(evp_script_name, "EVP2_03.pcs")
        cobotta.run_script()
    
        cobotta.wait_for_complete()
        logger.info(f"Result(num): {cobotta.I2}")
        if cobotta.I2 == 1:
            break
        logger.error(f"*** ターゲットが見つけられません ***")
        logger.error(f"*** 3sec 後に retry します ***")
        time.sleep(3)
    
    logger.error(f"***")
    logger.info(f"Result(pos): {cobotta.P10}")
    logger.error(f"***")
    
    logger.info("----------- 画像認識のセンターへmove  --------------")
    cobotta.take_arm()
    cobotta.move("P10", motion_mode=MotionMode.LINE, offset=(0,0,0), path_blend="@E", speed=50)
    cobotta.wait_for_complete()
    
except KeyboardInterrupt as e:
    logger.error(e)
except Exception as e:
    loggger.error(e)
finally:
    cobotta.disconnect()

```

## カメラのキャリブレート
