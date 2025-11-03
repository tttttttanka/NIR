import pandas as pd
import os

FILE = "history.csv"

# создать файл, если нет
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["name", "a", "b", "result"])
    df.to_csv(FILE, index=False)


def add_record(a, b, result):
    df = pd.read_csv(FILE)

    name = f"RES{len(df) + 1}"

    new_row = {"name": name, "a": a, "b": b, "result": result}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(FILE, index=False)
    return name


def get_history():
    return pd.read_csv(FILE)
