# PacScript を制御する

基本的に特別な場合を除いて、推奨してないが、直接デンソーのスクリプトを使うことができる

## 内部のスクリプトを run する

*) 必ず、local で直接 CobottaCtrl を使うときは、終了時には disconnect する
KeyboardInterrupt を含めて異常終了するときは disconnect しておく

```python
from cobotta2 import Config, CobottaCtrl, MotionMode

Config.load_yaml("config_cobotta2.yaml")
logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
cobotta = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, arm_name="Arm", logger=logger)

try:
    cobotta.reset_error()
    
    cobotta.turn_on_motor()
    cobotta.release_arm()
    
    name = "Pro1.pcs"  # 拡張子はあってもなくてもいい

    # take_script() とは排他的なので注意
    cobotta.take_script(name)
    cobotta.run_script()
    cobotta.wait_for_complete()

except KeyboardInterrupt as e:
    logger.error(e)
except Exception as e:
    loggger.error(e)
finally:
    cobotta.disconnect()

```

## 内部に Script を upload する

```python
from cobotta2 import Config, CobottaCtrl, MotionMode

Config.load_yaml("config_cobotta2.yaml")

logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
cobotta = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, arm_name="Arm", logger=logger)

file_content = """
Sub Main 

	TakeArm Keep = 0
	
	' 下降動作    P[61]に下降
	Move L, @0 P[61]

End Sub
"""
# Pro2.pcs に file_content の内容をアップロードする
cobotta.upload_content_to_cobotta(file_content, "Pro2.pcs")
print(cobotta.get_cobotta_file_names())

```

## 内部の Script 一覧


```python
from cobotta2 import Config, CobottaCtrl, MotionMode

Config.load_yaml("config_cobotta1.yaml")

logger = XLogger(log_level="debug", logger_name=Config.CLIENT_LOGGER_NAME)
cobotta = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, arm_name="Arm", logger=logger)

print(cobotta.get_cobotta_file_names())

```

## 内部の Script Download

*) 必ず、local で直接 CobottaCtrl を使うときは、終了時には disconnect する
KeyboardInterrupt を含めて異常終了するときは disconnect しておく

```python
from cobotta2 import Config, CobottaCtrl
from x_logger import XLogger


Config.load_yaml("config_cobotta1.yaml")

logger = XLogger(log_level="debug", logger_name=Config.CLIENT_LOGGER_NAME)
cobotta = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, arm_name="Arm", logger=logger)

print(cobotta.get_cobotta_file_names())
cobotta.download_file_from_cobotta("P62.pcs")

```
