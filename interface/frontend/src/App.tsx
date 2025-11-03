import { useEffect, useState } from "react";
import { runTask, getHistory } from "./api/api";
import type { TaskParams, HistoryEntry } from "./types/Task";
import "./App.css";

export default function App() {
  const [params, setParams] = useState<TaskParams | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    const h = await getHistory();
    setHistory(h);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const obj = JSON.parse(reader.result as string);
        setParams(obj);
      } catch {
        alert('Файл должен быть JSON вида {"a1":1,"b1":2}');
      }
    };
    reader.readAsText(file);
  }

  async function handleRun() {
    if (!params) {
      alert("Нет параметров");
      return;
    }

    await runTask(params);   // вычисляем
    await loadHistory();     // обновляем историю
  }

  return (
    <div className="app-container">
      <h1>Расчет</h1>

      <div
        className="drop-zone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        Перетащите файл (.txt)
      </div>

      {params && (
        <div>
          <h3>Параметры:</h3>
          <pre>{JSON.stringify(params, null, 2)}</pre>
        </div>
      )}

      <button className="run-btn" onClick={handleRun}>
        Запустить
      </button>

      <h2>История</h2>

      <table className="history-table">
        <thead>
          <tr>
            <th>A1</th>
            <th>B1</th>
            <th>RES1</th>
            <th>RES2</th>
            <th>RES3</th>
          </tr>
        </thead>

        <tbody>
          {history.map((row, idx) => (
            <tr key={idx}>
              <td>{row.A1}</td>
              <td>{row.B1}</td>
              <td>{row.RES1}</td>
              <td>{row.RES2}</td>
              <td>{row.RES3}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
