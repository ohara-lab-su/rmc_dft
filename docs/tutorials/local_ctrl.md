# local_ctrl

サーバー型ではなくてローカルで使う(デバッグ用)

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
