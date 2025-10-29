# 基本制御方法

## 前提

- コボッタサーバーが立ち上がっている

## コボッタサーバーを使って制御する基本

```python
import asyncio

from cobotta2 import Config
from cobotta2.server import AsyncCobottaClient
from x_logger import XLogger

async def main():
    Config.load_yaml("config_cobotta1.yaml")
    logger = XLogger(log_level="info", logger_name=Config.CLIENT_LOGGER_NAME)
    client = AsyncCobottaClient(config=Config, logger=logger)

    result = await client.current_position()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

```


## 制御サーバーを立ち上げるための設定など

- server_fastapi 以下 (FastAPIを用いたサーバ)
