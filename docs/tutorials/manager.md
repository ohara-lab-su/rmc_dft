# 変数マネージャ

## コボッタの内部変数管理をマネージャーを使って扱う

標準で コボッタ制御 python に用意しているもの

- コボッタ内部変数は python から扱えるようにしてます。
- コボッタ内部変数の書き出しは読み出しを python から使えます

## コボッタマネージャー

現状のpythoでは``` cleint.move("P110")``` のような内部変数呼び出しでのメソッド動作
が可能ですが、あくまで管理の主体はコボッタです。
このマネージャは
```move(var.P110)``` のようにコボッタ内部のように座標を扱うことを簡単に行うことを想定していて。
マネージャーを使って一括でコボッタの内部変数やり取りがやりやすいよう設計しています。

## コボッタinstanceと接続せずに座標系のマネージャーとしてつかう


```python
from cobotta2 import Config, CobottaCtrl, RobotVarManager
from x_logger import XLogger

Config.load_yaml("config_cobotta1.yaml")
logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
client = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, logger=logger)
var = RobotVarManager()

client.turn_on_motor()
client.take_arm()

client.move("P110")

# ある値を内部変数値に入れる
var.P10 = [0, 0, 0, 0, 0, 0]
var["P11"] = client.get_current_position()
var.P12 = [0, 0, 0, 0, 0, 0]

print(var.P10)
print(var["P11"])
print(var["P12"])

client.move(var.P10)
client.move(var.P11)
client.move(var.P12)
```

```python
var = CobottaVarManager()
# 内部値 P10-P20 まで [0,0,0,0,0,0] にする
var.set_vars("P", 10, 20, [0,0,0,0,0,0])
```

```python
var = CobottaVarManager()
# 内部値 P10に、値を登録
var.set_var("P", 10,[0,0,0,0,0,0])
```

### 内部変数値のファイルへの書き出し

```python
var = CobottaVarManager()
var.P11 = client.get_current_position()
var.save('save_name.json')
```

### ファイル値を内部変数値へ書き出す

```python
var = CobottaVarManager()
var.load('save_name.json')
print(var.P10)
```

### cobotta値を内部変数値へ書き出す

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10- P20
var.read_vars_from_robot("P", 10, 20)
```

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10- P20
var.read_var_from_robot("P", 10)
```

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10
var.read_var_from_robot("P10")
```

### 内部変数値を cobotta へ書き出す

```python
from cobotta2 import CobottaVarmanager
var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0,0,0,0,0,0]
var.P11 = [0,0,0,0,0,0]

# 内部値 P10-P20 を robot_instance P10-P20 へ書き出し
var.write_vars_to_cobotta("P", 10, 20)
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0, 0, 0, 0, 0, 0]

# 内部値 P10 を robot_instance P10 へ書き出し
var.write_var_to_robot("P", 10)
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0, 0, 0, 0, 0, 0]

# 内部値 P10 を robot_instance P10 へ書き出し
var.write_var_to_robot("P10")
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

var.load('save_name.json')

# 現在持っている内部変数を全て robot_instance に書き出す
var.write_all_to_robot()
```

## CobottaCtrl 単独で制御するとき

```python
from cobotta2 import Config, CobottaCtrl
from x_logger import XLogger

async def main():
    Config.load_yaml("config_cobotta1.yaml")
    logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
    client = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, logger=logger)

    result = client.current_position()
    print(result)

    client.disconnect()

if __name__ == "__main__":
    main()

```


### コボッタinstanceと接続せずに座標系のマネージャーとしてつかう

```python
from cobotta2 import Config, CobottaCtrl, RobotVarManager
from x_logger import XLogger

Config.load_yaml("config_cobotta1.yaml")
logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
client = CobottaCtrl(cobotta_ip=Config.COBOTTA_IP, logger=logger)
var = RobotVarManager()

client.turn_on_motor()
client.take_arm()

client.move("P110")

# ある値を内部変数値に入れる
var.P10 = [0, 0, 0, 0, 0, 0]
var["P11"] = client.get_current_position()
var.P12 = [0, 0, 0, 0, 0, 0]

print(var.P10)
print(var["P11"])
print(var["P12"])

client.move(var.P10)
client.move(var.P11)
client.move(var.P12)
```

```python
var = CobottaVarManager()
# 内部値 P10-P20 まで [0,0,0,0,0,0] にする
var.set_vars("P", 10, 20, [0,0,0,0,0,0])
```

```python
var = CobottaVarManager()
# 内部値 P10に、値を登録
var.set_var("P", 10,[0,0,0,0,0,0])
```

### 内部変数値のファイルへの書き出し

```python
var = CobottaVarManager()
var.P11 = client.get_current_position()
var.save('save_name.json')
```

### ファイル値を内部変数値へ書き出す

```python
var = CobottaVarManager()
var.load('save_name.json')
print(var.P10)
```

### cobotta値を内部変数値へ書き出す

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10- P20
var.read_vars_from_robot("P", 10, 20)
```

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10- P20
var.read_var_from_robot("P", 10)
```

```python
var = CobottaVarManager()
var.attach_robot(client)  # cobotta_instance セット

# robot_instance 内部を読み込む P10
var.read_var_from_robot("P10")
```

### 内部変数値を cobotta へ書き出す

```python
from cobotta2 import CobottaVarmanager
var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0,0,0,0,0,0]
var.P11 = [0,0,0,0,0,0]

# 内部値 P10-P20 を robot_instance P10-P20 へ書き出し
var.write_vars_to_cobotta("P", 10, 20)
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0, 0, 0, 0, 0, 0]

# 内部値 P10 を robot_instance P10 へ書き出し
var.write_var_to_robot("P", 10)
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

# 内部変数を書き換え
var.P10 = [0, 0, 0, 0, 0, 0]

# 内部値 P10 を robot_instance P10 へ書き出し
var.write_var_to_robot("P10")
```

```python
from cobotta2 import CobottaVarmanager

var = CobottaVarManager(cobotta)

var.load('save_name.json')

# 現在持っている内部変数を全て robot_instance に書き出す
var.write_all_to_robot()
```
