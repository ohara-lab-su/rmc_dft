# Config

サーバーなどのクラスにデーターを与える時に、一括で与えるために用いる。個別に与えることも可能だが、項目が多いのでこちらを使うのがおすすめ。
通常は、クラスとして使えばいいが。同時に、異なる設定で Config を用いる時は、インスタンスで Config を使う必要がある。いかに例を示す。

- config.yaml
```yaml
SERVER_IP: "10.170.10.33"
SERVER_PORT: 8000
COBOTTA_IP: "10.170.10.35"
CLIENT_LOGGER_NAME: "Cobotta1_Client"
SERVER_LOGGER_NAME: "Cobotta1_Server"
TIMEOUT: 5
LOGGER_LEVEL: "debug"
COBOTTA_CAMERA_IP: None
```

## Config (クラスモード)

Config をクラスメソッドとクラス変数としてつかう(simple)
```python
from cobotta2 import Config
from cobotta2.server import AsyncCobottaClient

Config.load_yaml('cobotta_server.yaml')

print(Config.SERVER_IP)
print(Config.SERVER_PORT)


client = AsyncCobottaClient(config=Config)
```

## Config (インスタンスモード)

```python
from cobotta2 import Config
from cobotta2.server import AsyncCobottaClient, AsyncCobottaStateClient

config = Config("cobotta_server.yaml")
config_state = Config("cobotta_server_sate.yaml")

client = AsyncCobottaClient(config=config)
state = AsyncCobottaStateClient(config=config_state)
```
