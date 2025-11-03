import type { TaskParams, RunResponse, HistoryEntry } from "../types/Task";

export async function runTask(params: TaskParams): Promise<RunResponse> {
  const res = await fetch("http://127.0.0.1:8000/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    throw new Error("Ошибка запроса");
  }
  return res.json();
}

export async function getHistory(): Promise<HistoryEntry[]> {
  const res = await fetch("http://127.0.0.1:8000/history");

  if (!res.ok) {
    throw new Error("Ошибка запроса");
  }

  return res.json();
}

