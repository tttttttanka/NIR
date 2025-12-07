# app.py
import os
import base64
import pandas as pd
import threading
import time
from datetime import datetime
import plotly.graph_objs as go
import yaml

from dash import Dash, html, dcc, dash_table, no_update
from dash.dependencies import Input, Output, State, ALL

from task import Task
from table_styles import TABLE_STYLES

BASE_DIR = "runs"
os.makedirs(BASE_DIR, exist_ok=True)

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Расчёт"

# Глобальные переменные 
parameter_series = pd.DataFrame()
available_parameters = []
yaml_config = {}

# Вспомогательные функции 

def load_history_df():
    if not os.path.exists(BASE_DIR):
        return pd.DataFrame()
    
    rows = []
    for folder in os.listdir(BASE_DIR):
        csv_path = os.path.join(BASE_DIR, folder, "results.csv")
        if os.path.exists(csv_path):
            try:
                df_part = pd.read_csv(csv_path)
                df_part["run"] = folder
                rows.append(df_part)
            except:
                pass
    
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

def create_history_table():
    df = load_history_df()
    if df.empty:
        return html.Div("Нет данных", className="empty-state")
    
    columns = [{"name": col, "id": col, "editable": False if col == "run" else True} for col in df.columns]
    
    return html.Div([
        html.Div([
            html.Button("Сохранить результаты", id="import-results-btn", n_clicks=0,
                        style={"marginRight": "10px", "padding": "6px 12px", "borderRadius": "6px", "border": "none", "backgroundColor": "#2196F3", "color": "#fff", "cursor": "pointer"}),
            html.Button("Обновить историю", id="refresh-history-btn", n_clicks=0,
                        style={"padding": "6px 12px", "borderRadius": "6px", "border": "none", "backgroundColor": "#FF9800", "color": "#fff", "cursor": "pointer"}),
            dcc.Download(id="download-dataframe-csv"),
        ], style={"marginBottom": "10px"}),
        dash_table.DataTable(
            id="history-data-table",
            data=df.to_dict("records"),
            columns=columns,
            page_size=10,
            page_action="native",
            sort_action="native",
            sort_mode="multi",
            filter_action="native",
            editable=True,
            **TABLE_STYLES
        )
    ])

def create_plots():
    df = load_history_df()
    if df.empty:
        return html.Div("Нет данных для графиков", className="empty-state")
    
    input_params = ['m', 'g', 'h', 'V']
    output_params = ['E_pot', 'E_kin', 'E_total']
    
    existing_inputs = [col for col in input_params if col in df.columns]
    existing_outputs = [col for col in output_params if col in df.columns]
    
    if not existing_inputs or not existing_outputs:
        return html.Div("Недостаточно данных", className="empty-state")
    
    graphs = []

    # 3D график E_total
    if 'E_total' in df.columns and len(existing_inputs) >= 2:
        param_x = existing_inputs[0]
        param_y = existing_inputs[2] if len(existing_inputs) > 2 else existing_inputs[1]
        fig_3d = go.Figure()
        fig_3d.add_trace(go.Scatter3d(
            x=df[param_x], y=df[param_y], z=df['E_total'], mode='markers',
            marker=dict(size=8, color=df['E_total'], colorscale='Viridis', opacity=0.7, colorbar=dict(title='E_total')),
            text=df.apply(lambda row: f"{param_x}: {row[param_x]:.2f}<br>{param_y}: {row[param_y]:.2f}<br>E_total: {row['E_total']:.2f}", axis=1),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        fig_3d.update_layout(
            title=f"3D: E_total от {param_x} и {param_y}",
            scene=dict(xaxis_title=param_x, yaxis_title=param_y, zaxis_title='E_total'),
            height=500
        )
        graphs.append(dcc.Graph(figure=fig_3d, id='3d-plot'))

    # E_kin vs V
    if 'E_kin' in df.columns and 'V' in df.columns:
        sorted_df = df.sort_values('V')
        fig_kin = go.Figure()
        fig_kin.add_trace(go.Scatter(x=sorted_df['V'], y=sorted_df['E_kin'], mode='markers+lines',
                                     marker=dict(size=8, opacity=0.7, color='red'),
                                     line=dict(width=2, color='red')))
        fig_kin.update_layout(title="Кинетическая энергия от скорости", xaxis_title="Скорость (V)", yaxis_title="E_kin", height=400)
        graphs.append(dcc.Graph(figure=fig_kin, id='kinetic-plot'))

    # E_pot vs h
    if 'E_pot' in df.columns and 'h' in df.columns:
        sorted_df = df.sort_values('h')
        fig_pot = go.Figure()
        fig_pot.add_trace(go.Scatter(x=sorted_df['h'], y=sorted_df['E_pot'], mode='markers+lines',
                                     marker=dict(size=8, opacity=0.7, color='green'),
                                     line=dict(width=2, color='green')))
        fig_pot.update_layout(title="Потенциальная энергия от высоты", xaxis_title="h", yaxis_title="E_pot", height=400)
        graphs.append(dcc.Graph(figure=fig_pot, id='potential-plot'))

    return html.Div(graphs)

def format_log(log_text):
    """Форматируем лог для красивого отображения с переносами и цветами."""
    html_lines = []
    series_blocks = log_text.split("===")
    for block in series_blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("Серия"):
            html_lines.append(html.Div(f"=== {block} ===", style={"fontWeight": "bold", "marginTop": "10px"}))
        elif block.startswith("Всего серий") or block.startswith("ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ"):
            html_lines.append(html.Div(block, style={"fontWeight": "bold", "color": "green", "marginTop": "10px"}))
        else:
            # Разбиваем на параметры и энергии
            params_part = []
            for part in block.split(" E_"):
                part = part.strip()
                if not part:
                    continue
                if part.startswith("pot"):
                    params_part.append(html.Div(f"E_{part}", style={"marginLeft": "15px", "color": "green"}))
                elif part.startswith("kin"):
                    params_part.append(html.Div(f"E_{part}", style={"marginLeft": "15px", "color": "red"}))
                elif part.startswith("total"):
                    params_part.append(html.Div(f"E_{part}", style={"marginLeft": "15px", "fontWeight": "bold"}))
                elif part.startswith("heat"):
                    params_part.append(html.Div(f"E_{part}", style={"marginLeft": "15px", "color": "orange"}))
                else:
                    params_part.append(html.Div(f"E_{part}", style={"marginLeft": "15px"}))
            html_lines.extend(params_part)
    return html_lines


# Layout 
app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "20px", "fontFamily": "Arial, sans-serif"},
    children=[
        html.H1("Расчёт параметров", style={"textAlign": "center", "marginBottom": "30px"}),

        html.Div([
            dcc.Upload(
                id='upload-parameters',
                multiple=False,
                style={"padding": "20px", "border": "2px dashed #aaa", "borderRadius": "8px", "textAlign": "center", "marginBottom": "20px", "backgroundColor": "#f9f9f9"},
                children=html.Div(['Перетащите файл .yaml или ', html.A('выберите файл')])
            ),
            html.Div(id="uploaded-parameters-info")
        ], style={"marginBottom": "20px"}),

        html.Div(id="input-parameters-container", style={"marginBottom": "20px"}),

        html.Div([
            html.Button("Запустить расчеты", id="run-btn", n_clicks=0,
                        style={"padding": "10px 20px", "fontSize": "16px", "borderRadius": "8px",
                               "backgroundColor": "#4CAF50", "color": "#fff", "border": "none", "cursor": "pointer"})
        ], style={"textAlign": "center"}),

        html.H3("Лог вычислений", style={"marginTop": "30px"}),
        html.Div(
            "Лог появится здесь после запуска",
            id="log-container",
            style={"height": "200px", "overflowY": "scroll", "border": "1px solid #ddd",
                   "padding": "10px", "borderRadius": "8px", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                   "backgroundColor": "#f9f9f9", "marginBottom": "30px"}
        ),

        dcc.Store(id="current-run-id", data=None),
        dcc.Store(id="is-running", data=False),
        dcc.Store(id="series-data", data=[]),
        dcc.Interval(id="log-interval", interval=1000, disabled=True, n_intervals=0),

        html.H3("История расчетов"),
        html.Div(id="table-container", children=create_history_table(), style={"marginBottom": "30px"}),

        html.H3("Графики результатов"),
        html.Div(id="plots-container", children=create_plots())
    ]
)

#  Callbacks 
@app.callback(
    Output("uploaded-parameters-info", "children"),
    Output("input-parameters-container", "children"),
    Input("upload-parameters", "contents"),
    State("upload-parameters", "filename"),
)
def load_parameters(contents, filename):
    global current_parameters, parameter_series, available_parameters, yaml_config
    
    if contents is None:
        return "", html.Div("Загрузите файл параметров")

    try:
        content_str = contents.split(",")[1]
        decoded = base64.b64decode(content_str).decode("utf-8")
        yaml_config = yaml.safe_load(decoded)

        constants = yaml_config.get("constants", {})
        params = yaml_config.get("parameters", {})

        current_parameters = {}
        available_parameters = list(params.keys()) + list(constants.keys())

        # создаём UI: слайдеры + константы
        input_controls = []

        for key, p in params.items():
            input_controls.append(
                html.Div([
                    html.Label(f"{p.get('name', key)} ({key}) [{p.get('unit','')}]"),
                    dcc.Slider(
                        id={'type': 'param', 'key': key},
                        min=float(p.get("min", 0)),
                        max=float(p.get("max", 100)),
                        step=float(p.get("step", 1)),
                        value=float(p.get("default", p.get("min", 0))),
                        marks={float(p.get("min", 0)): str(p.get("min", 0)), float(p.get("max", 100)): str(p.get("max", 100))},
                    ),
                    html.Div(id={'type': 'param-value', 'key': key}, style={"marginTop": "6px"})
                ], style={"padding": "10px", "border": "1px solid #ddd", "marginBottom": "10px", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"})
            )

        for key, c in constants.items():
            input_controls.append(
                html.Div([
                    html.Label(f"{c.get('name', key)} ({key})"),
                    dcc.Input(
                        id={'type': 'const', 'key': key},
                        type="number",
                        value=c.get("value"),
                        readOnly=True,
                        style={"backgroundColor": "#f0f0f0", "width": "200px"}
                    )
                ], style={"padding": "10px", "border": "1px solid #eee", "marginBottom": "10px", "borderRadius": "8px"})
            )

        input_controls.append(
            html.Div([
                html.Button("Добавить серию", id="add-series-btn", n_clicks=0,
                            style={"padding": "6px 12px", "borderRadius": "6px", "border": "none", "backgroundColor": "#2196F3", "color": "#fff", "cursor": "pointer"}),
                html.Div(id="add-series-feedback", style={"marginTop": "6px"})
            ], style={"marginTop": "10px", "marginBottom": "20px"})
        )

        input_controls.append(html.Div(id="series-table-container"))

        info = f"Файл {filename} загружен. Параметров: {len(available_parameters)} (слайдеров: {len(params)}, констант: {len(constants)})"
        return info, html.Div(input_controls)
        
    except Exception as e:
        return f"Ошибка: {str(e)}", html.Div("Не удалось загрузить YAML")

# slider 
@app.callback(
    Output({'type': 'param-value', 'key': ALL}, 'children'),
    Input({'type': 'param', 'key': ALL}, 'value'),
    State({'type': 'param', 'key': ALL}, 'id'),
    prevent_initial_call=False
)
def show_slider_values(values, ids):
    if not values:
        return []
    return [f"{idd.get('key')} = {val}" for val, idd in zip(values, ids)]

#  series
@app.callback(
    Output("series-data", "data"),
    Output("series-table-container", "children"),
    Output("add-series-feedback", "children"),
    Input("add-series-btn", "n_clicks"),
    State("series-data", "data"),
    State({'type': 'param', 'key': ALL}, 'value'),
    State({'type': 'param', 'key': ALL}, 'id'),
    State({'type': 'const', 'key': ALL}, 'value'),
    State({'type': 'const', 'key': ALL}, 'id'),
    prevent_initial_call=True
)
def add_series(n_clicks, series_data, param_values, param_ids, const_values, const_ids):
    global yaml_config
    if yaml_config is None or yaml_config == {}:
        return series_data, no_update, "Сначала загрузите param_config.yaml"
    if series_data is None:
        series_data = []
    row = {}
    if param_ids:
        for val, idd in zip(param_values, param_ids):
            row[idd.get('key')] = val
    if const_ids:
        for val, idd in zip(const_values, const_ids):
            row[idd.get('key')] = val
    series_data.append(row)
    df = pd.DataFrame(series_data)
    table = dash_table.DataTable(
        id="series-data-table",
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        page_size=10,
        page_action="native",
        editable=True,
        **TABLE_STYLES
    ) if not df.empty else html.Div("Нет серий")
    feedback = f"Серия добавлена (всего {len(series_data)})."
    return series_data, table, feedback

# calculations
@app.callback(
    Output("current-run-id", "data"),
    Output("is-running", "data"),
    Output("log-interval", "disabled"),
    Input("run-btn", "n_clicks"),
    State("series-data", "data"),
    prevent_initial_call=True,
)
def run_calculations(n_clicks, series_data):
    global parameter_series
    if not series_data:
        return None, False, True
    parameter_series = pd.DataFrame(series_data)
    if parameter_series.empty:
        return None, False, True
    folder = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

    def run_tasks_thread():
        try:
            with open(os.path.join(BASE_DIR, folder, "log.txt"), "w", encoding="utf-8") as f:
                f.write(f"Всего серий: {len(parameter_series)}\n")
            for idx, row in parameter_series.iterrows():
                try:
                    Task(row.to_dict(), folder, idx).solve()
                    time.sleep(0.1)
                except Exception as e:
                    with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                        f.write(f"Ошибка в серии {idx + 1}: {str(e)}\n")
            with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                f.write("\nВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ\n")
        except Exception as e:
            with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                f.write(f"Ошибка: {str(e)}\n")

    threading.Thread(target=run_tasks_thread, daemon=True).start()
    return folder, True, False

# log 
@app.callback(
    Output("log-container", "children"),
    Output("is-running", "data", allow_duplicate=True),
    Output("log-interval", "disabled", allow_duplicate=True),
    Input("log-interval", "n_intervals"),
    State("current-run-id", "data"),
    State("is-running", "data"),
    prevent_initial_call=True,
)
def update_log(n_intervals, run_id, is_running):
    if not run_id:
        return "", False, True
    log_path = os.path.join(BASE_DIR, run_id, "log.txt")
    if not os.path.exists(log_path):
        return "Ожидание вычислений...", is_running, False
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
    formatted_log = format_log(log_content)
    if "ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ" in log_content and is_running:
        return formatted_log, False, True
    return formatted_log, is_running, False


#history and plots
@app.callback(
    Output("table-container", "children", allow_duplicate=True),
    Output("plots-container", "children", allow_duplicate=True),
    Input("is-running", "data"),
    State("current-run-id", "data"),
    prevent_initial_call=True,
)
def auto_update_on_completion(is_running, run_id):
    if not is_running and run_id:
        time.sleep(0.5)
        return create_history_table(), create_plots()
    return no_update, no_update

@app.callback(
    Output("table-container", "children"),
    Output("plots-container", "children"),
    Input("refresh-history-btn", "n_clicks"),
    State("is-running", "data"),
)
def update_table_and_plots(n_clicks, is_running):
    if n_clicks and not is_running:
        return create_history_table(), create_plots()
    return no_update, no_update

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("import-results-btn", "n_clicks"),
    prevent_initial_call=True,
)
def import_to_csv(n_clicks):
    df = load_history_df()
    if df.empty:
        return no_update
    return dcc.send_data_frame(df.to_csv, "results_import.csv", index=False)


if __name__ == "__main__":
    app.run(debug=True)
