# コボッタ内部変数

コボッタ内部変数をpythonから直接扱う

## cobotta 内部変数の管理

- Manager を使って内部変数値を管理する
  - 内部変数値に入れる
    - instance.P10 = [xxx,xxx,xxx,xxx,xxx,xxx]
    - set_var("P", 10, [xxx,xxx,xxx,xxx,xxx,xxx])
  - 内部変数値を取り出す
    - print(instance.P10)
  - 内部変数値をファイルに書き出す
  - ファイルを内部変数値に読み込む
  - 内部変数値を cobotta に書き出す
  - cobotta から内部変数値に値を入れる
