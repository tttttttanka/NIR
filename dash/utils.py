import os
from datetime import datetime

def create_calculation_folder():
    folder = f"history/{datetime.now().isoformat().replace(':', '-')}"
    os.makedirs(folder, exist_ok=True)
    return folder

def append_log(folder, text):
    with open(f"{folder}/log.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")
