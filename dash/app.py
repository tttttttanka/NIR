import os
import json
import pandas as pd
from datetime import datetime

from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output, State

from task import Task

# --- Папка для истории ---
BASE_DIR = "runs"
os.makedirs(BASE_DIR, exist_ok=True)

# --- Dash App ---
app = Dash(__name__)
app.title = "Расчёт параметров"

# --- Вспомогательная функция: загрузить всю историю в pandas ---
def load_history_df():
    rows = []
    for folder in os.listdir(BASE_DIR):
        csv_path = os.path.join(BASE_DIR, folder, "results.csv")
        if os.path.exists(csv_path):
            try:
                df_part = pd.read_csv(csv_path)
                df_part["run"] = folder  # для отслеживания вычисления
                rows.append(df_part)
            except:
                pass
    if rows:
        return pd.concat(rows, ignore_index=True)
    return pd.DataFrame(columns=["A1", "B1", "SUM", "DIFF", "DIV", "run"])


# --- Интерфейс ---
app.layout = html.Div(
    style={"maxWidth": "700px", "margin": "0 auto", "padding": "20px"},
    children=[
        html.H1("Расчёт параметров"),

        html.H3("Параметры"),

        # === БЛОК A1 ===
        html.Div([
            html.Div([
                html.Span("A1:", style={"fontWeight": "600"}),
                html.Span(id="a1-value", style={"marginLeft": "6px"})
            ]),
            dcc.Slider(
                id="a1",
                min=0,
                max=50,
                step=0.1,
                value=0
            ),
        ], style={"marginBottom": "25px"}),

        # === БЛОК B1 ===
        html.Div([
            html.Div([
                html.Span("B1:", style={"fontWeight": "600"}),
                html.Span(id="b1-value", style={"marginLeft": "6px"})
            ]),
            dcc.Slider(
                id="b1",
                min=0,
                max=60,
                step=0.1,
                value=0
            ),
        ], style={"marginBottom": "25px"}),

        # === Drag and Drop загрузка ===
        dcc.Upload(
            id='upload-file',
            children=html.Div([
                'Перетащите файл .txt или ',
                html.A('выберите файл')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '8px',
                'textAlign': 'center',
                'marginBottom': '20px',
            },
            multiple=False
        ),
        html.Div(id="uploaded-file-name", style={"marginBottom": "20px"}),

        html.Button("Запустить расчёт", id="run-btn", n_clicks=0),

        html.H3("История расчётов", style={"marginTop": "30px"}),

        html.Div(id="table-container")
    ]
)


# =====================================================================
# 📌 1. Обновление LABEL со значением слайдеров A1 и B1
# =====================================================================
@app.callback(
    Output("a1-value", "children"),
    Output("b1-value", "children"),
    Input("a1", "value"),
    Input("b1", "value")
)
def update_slider_labels(a1, b1):
    return f"{a1}", f"{b1}"


# =====================================================================
# 📌 2. Обработка загрузки файла
# =====================================================================
@app.callback(
    Output("uploaded-file-name", "children"),
    Output("a1", "value"),
    Output("b1", "value"),

    Input("upload-file", "contents"),
    State("upload-file", "filename"),
)
def load_file(contents, filename):
    if contents is None:
        return "", 0, 0

    # читаем текстовый JSON внутри файла
    content_str = contents.split(",")[1]
    import base64
    decoded = base64.b64decode(content_str).decode("utf-8")

    try:
        obj = json.loads(decoded)
        return f"Файл принят: {filename}", obj["a1"], obj["b1"]
    except:
        return "Ошибка: файл должен содержать JSON", 0, 0


# =====================================================================
# 📌 3. Запуск расчёта
# =====================================================================
@app.callback(
    Output("table-container", "children"),
    Input("run-btn", "n_clicks"),
    State("a1", "value"),
    State("b1", "value"),
)
def run_calculation(n_clicks, a1, b1):
    if n_clicks == 0:
        df = load_history_df()
    else:
        # создаём новую папку run
        folder = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_path = os.path.join(BASE_DIR, folder)
        os.makedirs(run_path, exist_ok=True)

        # выполняем задачу
        task = Task(a1, b1, folder)
        task.solve()

        df = load_history_df()

    # --- таблица pandas → Dash DataTable ---
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"padding": "8px", "textAlign": "center"},
        style_header={"backgroundColor": "#5b7cff", "color": "white", "fontWeight": "600"},
    )


# =====================================================================

if __name__ == "__main__":
    app.run(debug=True)
