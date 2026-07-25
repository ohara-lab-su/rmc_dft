"""
K.NAKADA, kengo.nakada@gmail.com
"""


class ConfigError(Exception):
    """
    設定ファイルまたは入力構造が不正な場合の例外。

    JSON 設定の必須キー不足、POSCAR の形式不整合、未知の constraint source など、
    ユーザー入力に起因するエラーをこの例外にまとめる。
    """
