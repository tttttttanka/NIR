import os
import time
import pandas as pd

class Task:
    def __init__(self, a1, b1, folder):
        self.a1 = float(a1)
        self.b1 = float(b1)
        self.folder = folder

        self.path = os.path.join("runs", folder)
        os.makedirs(self.path, exist_ok=True)

        self.log_path = os.path.join(self.path, "log.txt")
        self.csv_path = os.path.join(self.path, "results.csv")

    def log(self, text):
        """Записывает строку в log.txt"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def solve(self):
        self.log("Старт вычислений")
        time.sleep(0.5)

        # словарь: имя_шагa → функция(операция)
        operations = {
            "SUM": lambda a, b: a + b,
            "DIFF": lambda a, b: a - b,
            "DIV": lambda a, b: a / b if b != 0 else None,
        }

        results = {}

        # выполняем все операции циклом
        for name, func in operations.items():
            value = func(self.a1, self.b1)
            results[name] = value
            self.log(f"{name} = {value}")
            time.sleep(2)

        self.log("Вычисления завершены")

        # --- сохраняем CSV через pandas ---
        df = pd.DataFrame([{
            "A1": self.a1,
            "B1": self.b1,
            **results
        }])
        df.to_csv(self.csv_path, index=False)

        return results

