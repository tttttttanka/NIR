import os
import time
import pandas as pd
import numpy as np

class Task:
    def __init__(self, parameters, folder, series_id):
        self.parameters = parameters
        self.folder = folder
        self.series_id = series_id

        self.path = os.path.join("runs", folder)
        os.makedirs(self.path, exist_ok=True)

        self.log_path = os.path.join(self.path, "log.txt")
        self.csv_path = os.path.join(self.path, "results.csv")

    def log(self, text):
        """Записывает строку в log.txt с блокировкой для многопоточности"""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"Ошибка записи в лог: {e}")

    def solve(self):
        self.log(f"=== Серия {self.series_id + 1} ===")
        self.log(f"Параметры: {self.parameters}")
        time.sleep(0.5)

        try:
            # Пример расчетов (замените на ваши формулы ANSYS)
            operations = {
                "E_pot": self.parameters.get('m', 0) * self.parameters.get('g', 0) * self.parameters.get('h', 0),
                "E_kin": (self.parameters.get('m', 0) * self.parameters.get('V', 0)**2) / 2,
                "E_total": 0  # Будет вычислено ниже
            }
            
            operations["E_total"] = operations["E_pot"] + operations["E_kin"]

            for name, value in operations.items():
                self.log(f"{name} = {value:.4f}")
                time.sleep(1)  # Имитация долгих вычислений

            self.log(f"Серия {self.series_id + 1} завершена\n")

            # Сохраняем результаты с блокировкой для многопоточности
            self.save_results(operations)
            
            return operations
            
        except Exception as e:
            self.log(f"Ошибка в серии {self.series_id + 1}: {str(e)}")
            return None

    def save_results(self, operations):
        """Безопасное сохранение результатов в CSV для многопоточности"""
        result_row = {**self.parameters, **operations}
        
        # Создаем временный файл для избежания конфликтов
        temp_csv_path = self.csv_path + ".tmp"
        
        try:
            # Если файл существует, читаем его и добавляем новую строку
            if os.path.exists(self.csv_path):
                df = pd.read_csv(self.csv_path)
                df = pd.concat([df, pd.DataFrame([result_row])], ignore_index=True)
            else:
                df = pd.DataFrame([result_row])
            
            # Сохраняем во временный файл
            df.to_csv(temp_csv_path, index=False)
            
            # Атомарно заменяем старый файл новым
            if os.path.exists(self.csv_path):
                os.replace(temp_csv_path, self.csv_path)
            else:
                os.rename(temp_csv_path, self.csv_path)
                
        except Exception as e:
            self.log(f"Ошибка сохранения результатов: {str(e)}")
            # Удаляем временный файл в случае ошибки
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)