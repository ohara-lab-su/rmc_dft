# API の加え方

cobotta_ctrl.py (コボッタ制御クラス) にメソッドやプロパティを追加した時。
基本的には fastapi_frame で自動的に処理される(client/server両方)が、
API と、APIの引数と戻り値をSPECに定義しておく必要がある。

## SPEC の追加

- server_fastapi
  - spec_ctrl.py: SPEC 追加
  - models: SPEC から用いているモデル(APIの引数処理)が新たにあれば追加

## pyi の変更
- server_fastapi
  - make.py: *.pyi 自動作成(なくても問題ないが、アルトエディタで便利)をする
