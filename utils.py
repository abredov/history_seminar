import os
import json


def read_data(folder_name, file_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    filename = os.path.join(folder_name, file_name)
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(dict(), f, ensure_ascii=True)
    with open(filename, encoding="utf-8") as f:
        load_dct = json.load(f)
    return load_dct


def write_data(folder_name, file_name, save_dct):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    filename = os.path.join(folder_name, file_name)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_dct, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    pass
