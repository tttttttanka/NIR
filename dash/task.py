import os
import time
import pandas as pd


class Task:

    def __init__(self, params: dict, folder: str, index: int):
        self.params = params
        self.index = index
        self.folder = folder

        self.run_path = os.path.join("runs", folder)
        os.makedirs(self.run_path, exist_ok=True)

        self.log_path = os.path.join(self.run_path, "log.txt")
        self.results_path = os.path.join(self.run_path, "results.csv")

    def log(self, text: str):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


    def param(self, key: str, default=None):
        if key not in self.params:
            if default is not None:
                return default
            self.log(f"[ОШИБКА] Параметр '{key}' не найден.")
            raise ValueError(f"Missing parameter: {key}")
        return float(self.params[key])

    def step(self, name: str, value):
        self.log(f"   {name}: {value:.4f}")
        time.sleep(0.4)


    def solve(self):
        self.log(f"\nСерия {self.index + 1} ")

        try:
            # Основные параметры
            m = self.param("m")
            g = self.param("g")
            h = self.param("h")
            V = self.param("V")
            T = self.param("T")
            
            # Константы
            SPECIFIC_HEAT = self.param("SPECIFIC_HEAT")

        except Exception as e:
            self.log(f"[ОШИБКА] Невозможно вычислить серию: {str(e)}")
            return

        self.log(f"Параметры: m={m}, g={g}, h={h}, V={V}, T={T}")

        # --- Потенциальная энергия ---
        E_pot = m * g * h
        self.step("E_pot (потенциальная)", E_pot)

        # --- Кинетическая энергия ---
        E_kin = 0.5 * m * V ** 2
        self.step("E_kin (кинетическая)", E_kin)

        # --- Полная энергия ---
        E_total = E_pot + E_kin
        self.step("E_total (полная)", E_total)

        # --- Новая формула (тепловая энергия) ---
        Q = m * SPECIFIC_HEAT * (T - 20)
        self.step("E_heat (тепловая)", Q)

        row = {
            "series": self.index + 1,

            "m": m,
            "g": g,
            "h": h,
            "V": V,
            "T": T,

            "SPECIFIC_HEAT": SPECIFIC_HEAT,

            "E_pot": E_pot,
            "E_kin": E_kin,
            "E_total": E_total,
            "Q": Q,

        }

        # Если файла нет — создаём
        if not os.path.exists(self.results_path):
            df = pd.DataFrame([row])
            df.to_csv(self.results_path, index=False)
        else:
            df = pd.read_csv(self.results_path)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(self.results_path, index=False)

        self.log("Серия завершена.\n")
