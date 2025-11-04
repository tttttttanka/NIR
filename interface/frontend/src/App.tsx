import { useState, useEffect } from "react";
import { runTask, getHistory } from "./api/api";
import type { TaskParams, HistoryEntry } from "./types/Task";
import "./App.css";

export default function App() {
  const [params, setParams] = useState<TaskParams>({ a1: 0, b1: 0 });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [fileName, setFileName] = useState<string>("");

  useEffect(() => {
    loadHistory();
  }, []);

  /* Drag & Drop */
  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();

    const file = e.dataTransfer.files[0];
    if (!file) return;

    if (!file.name.endsWith(".txt")) {
      alert("Разрешён только .txt");
      return;
    }

    setFileName(file.name);   // Сохраняем имя файла

    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = () => {
      try {
        const obj = JSON.parse(reader.result as string);
        setParams(obj);
      } catch {
        alert("Ошибка: содержимое файла должно быть JSON");
      }
    };
  }

  async function loadHistory() {
    try {
      const data = await getHistory();
      setHistory(data);
    } catch {
      console.log("Ошибка загрузки истории");
    }
  }

  async function handleRun() {
    try {
      await runTask(params);
      await loadHistory();
    } catch {
      alert("Ошибка запроса");
    }
  }

  return (
    <div className="app-container">
      <h1>Расчёт</h1>

      <div className="glass-block">
        <h3>Параметры</h3>

        {/* Ползунок A1 */}
        <div className="slider-block">
          <label>A1: {params.a1}</label>
          <input
            type="range"
            min={0}
            max={50}
            step={0.1}
            value={params.a1}
            onChange={(e) => setParams({ ...params, a1: Number(e.target.value) })}
            className="slider"
          />
        </div>

        {/* Ползунок B1 */}
        <div className="slider-block">
          <label>B1: {params.b1}</label>
          <input
            type="range"
            min={0}
            max={60}
            step={0.1}
            value={params.b1}
            onChange={(e) => setParams({ ...params, b1: Number(e.target.value) })}
            className="slider"
          />
        </div>

        <div
          className="drop-zone"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          Перетащите файл .txt
        </div>

        {fileName && (
          <p>
            Файл принят: <b>{fileName}</b>
          </p>
        )}

        <button className="run-btn" onClick={handleRun}>
          Запустить
        </button>
      </div>

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
          {history.map((h, i) => (
            <tr key={i}>
              <td>{h.A1}</td>
              <td>{h.B1}</td>
              <td>{h.RES1}</td>
              <td>{h.RES2}</td>
              <td>{h.RES3}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
