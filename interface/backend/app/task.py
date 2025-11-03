import time
import random
import csv
import os

CSV_FILE = "history.csv"

class Task:
    def __init__(self, params):
        self.a1 = params.a1
        self.b1 = params.b1

    def solve(self):
        time.sleep(1)

        result = {
            "RES1": random.randint(1, 10),
            "RES2": random.randint(1, 10),
            "RES3": random.randint(1, 10),
        }

        self.save_to_csv(result)
        return result

    def save_to_csv(self, result):
        file_exists = os.path.isfile(CSV_FILE)

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(["A1", "B1", "RES1", "RES2", "RES3"])

            writer.writerow([self.a1, self.b1,
                             result["RES1"],
                             result["RES2"],
                             result["RES3"]])
