def get_nth_line(file_path, n):
    with open(file_path, 'r', encoding='utf-8') as file:
        for current_line_number, line in enumerate(file, start=1):
            if current_line_number == n:
                return line.strip()  # 改行文字を除く
    return None  # n行目が存在しない場合

def get_label(cname: str = "aaa.vasp") -> str:
    """
    Get label from the VASP file.

    Args:
        cname (str): Name of the VASP file without extension.

    Returns:
        str: Label extracted from the file.
    """
    # The label is in the 6th line of the file
    try:
        with open(cname + ".vasp", 'r', encoding='utf-8') as file:
            for _ in range(6):
                first_line = file.readline().strip()
                return first_line
    except FileNotFoundError:
        print(f"File {cname}.vasp not found.")
        return ""
