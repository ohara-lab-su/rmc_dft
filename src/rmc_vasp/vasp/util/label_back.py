
def label_back(file_path:str="aaa.vasp"):
    file_read="label.txt"
    try:
        with open(file_read, 'r') as file:
                label_line = file.readline().strip()
    except FileNotFoundError:
        print(f"File not found.")

    with open(file_path, 'r') as file:
        lines = file.readlines()
        label_place = 6
    if 1 <= label_place <= len(lines):
        lines[label_place - 1] = label_line + '\n'  # 改行を付けて置換

        # ファイルに上書き保存
        with open(file_path, 'w') as file:
            file.writelines(lines)
        print(f"{file_path} label back.")
    else:
        printf("error: line number out of range.")

    return True


