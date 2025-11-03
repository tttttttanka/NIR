from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import TaskParams
from .task import Task
import csv, os

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run")
def run_task(data: TaskParams):
    task = Task(data)
    result = task.solve()
    return {"result": result}


@app.get("/history")
def get_history():
    CSV_FILE = "history.csv"
    if not os.path.exists(CSV_FILE):
        return []

    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "A1": float(row["A1"]),
                "B1": float(row["B1"]),
                "RES1": float(row["RES1"]),
                "RES2": float(row["RES2"]),
                "RES3": float(row["RES3"]),
            })
    return rows
