import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Находим элемент <div id="root"></div> из HTML
const root = document.getElementById("root")!;

// Создаём корневой React-контейнер и рендерим приложение внутрь него
ReactDOM.createRoot(root).render(
  // StrictMode включает дополнительные проверки React (только в dev)
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
