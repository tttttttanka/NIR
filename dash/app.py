import os
import json
import base64
import pandas as pd
import threading
import time
from datetime import datetime
import plotly.graph_objs as go
import numpy as np

from dash import Dash, html, dcc, dash_table, no_update, callback_context
from dash.dependencies import Input, Output, State

from task import Task
from table_styles import TABLE_STYLES

BASE_DIR = "runs"
os.makedirs(BASE_DIR, exist_ok=True)

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Расчёт"

# Глобальные переменные для хранения параметров
current_parameters = {}
parameter_series = pd.DataFrame()
available_parameters = []

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

def generate_parameter_series(parameters_dict):
    series_dict = {}
    
    for param_name, param_value in parameters_dict.items():
        if isinstance(param_value, list):
            series_dict[param_name] = param_value
        else:
            series_dict[param_name] = [param_value]
    
    from itertools import product
    combinations = list(product(*series_dict.values()))
    
    series_df = pd.DataFrame(combinations, columns=series_dict.keys())
    return series_df

def create_input_parameters_table():
    global parameter_series
    if parameter_series.empty:
        return html.Div("Загрузите параметры", className="empty-state")
    
    columns = [{"name": col, "id": col} for col in parameter_series.columns]
    
    return html.Div([
        dash_table.DataTable(
            id="input-parameters-table",
            data=parameter_series.to_dict("records"),
            columns=columns,
            page_size=10,
            page_action="native",
            editable=True,
            **TABLE_STYLES
        )
    ])

def create_history_table():
    df = load_history_df()
    if df.empty:
        return html.Div("Нет данных", className="empty-state")
    
    columns = []
    for col in df.columns:
        col_config = {"name": col, "id": col}
        if col == "run":
            col_config["editable"] = False
        columns.append(col_config)
    
    return html.Div([
        html.Div([
            html.Button("Импортировать результаты", id="import-results-btn", n_clicks=0),
            html.Button("Обновить историю", id="refresh-history-btn", n_clicks=0),
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
    
    # 3D график: E_total от двух параметров
    if 'E_total' in df.columns and len(existing_inputs) >= 2:
        param_x = existing_inputs[0]
        param_y = existing_inputs[2] if len(existing_inputs) > 2 else existing_inputs[1]
        
        fig_3d = go.Figure()
        fig_3d.add_trace(go.Scatter3d(
            x=df[param_x],
            y=df[param_y], 
            z=df['E_total'],
            mode='markers',
            marker=dict(
                size=8,
                color=df['E_total'],
                colorscale='Viridis',
                opacity=0.7,
                colorbar=dict(title='E_total')
            ),
            text=df.apply(lambda row: f"{param_x}: {row[param_x]:.2f}<br>{param_y}: {row[param_y]:.2f}<br>E_total: {row['E_total']:.2f}", axis=1),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        
        fig_3d.update_layout(
            title=f"3D: E_total от {param_x} и {param_y}",
            scene=dict(
                xaxis_title=param_x,
                yaxis_title=param_y,
                zaxis_title='E_total'
            ),
            height=500,
        )
        graphs.append(dcc.Graph(figure=fig_3d, id='3d-plot'))
    
    # График E_kin от V
    if 'E_kin' in df.columns and 'V' in df.columns:
        sorted_df = df.sort_values(by='V')
        
        fig_kin = go.Figure()
        fig_kin.add_trace(go.Scatter(
            x=sorted_df['V'], 
            y=sorted_df['E_kin'],
            mode='markers+lines',
            marker=dict(size=8, opacity=0.7, color='red'),
            line=dict(width=2, color='red')
        ))
        
        fig_kin.update_layout(
            title="Кинетическая энергия от скорости",
            xaxis_title="Скорость (V)",
            yaxis_title="Кинетическая энергия (E_kin)",
            height=400
        )
        graphs.append(dcc.Graph(figure=fig_kin, id='kinetic-plot'))
    
    # График E_pot от h
    if 'E_pot' in df.columns and 'h' in df.columns:
        sorted_df = df.sort_values(by='h')
        
        fig_pot = go.Figure()
        fig_pot.add_trace(go.Scatter(
            x=sorted_df['h'], 
            y=sorted_df['E_pot'],
            mode='markers+lines',
            marker=dict(size=8, opacity=0.7, color='green'),
            line=dict(width=2, color='green')
        ))
        
        fig_pot.update_layout(
            title="Потенциальная энергия от высоты",
            xaxis_title="Высота (h)",
            yaxis_title="Потенциальная энергия (E_pot)",
            height=400
        )
        graphs.append(dcc.Graph(figure=fig_pot, id='potential-plot'))
    
    return html.Div(graphs)

app.layout = html.Div(
    className="main-container",
    children=[
        html.H1("Расчёт параметров"),
        
        dcc.Upload(
            id='upload-parameters',
            className="upload-zone",
            children=html.Div(['Перетащите JSON файл или ', html.A('выберите файл')]),
            multiple=False
        ),
        html.Div(id="uploaded-parameters-info", className="uploaded-file-name"),
        
        html.Div(id="input-parameters-container"),
        
        html.Button("Запустить расчеты", id="run-btn", n_clicks=0),
        
        html.H3("Лог вычислений"),
        html.Div(
            "Лог появится здесь после запуска",
            id="log-container",
            className="log-container"
        ),
        
        dcc.Store(id="current-run-id", data=None),
        dcc.Store(id="is-running", data=False),
        dcc.Interval(id="log-interval", interval=1000, disabled=True, n_intervals=0),
        
        html.H3("История расчетов"),
        html.Div(id="table-container", children=create_history_table()),
        
        html.H3("Графики результатов"),
        html.Div(id="plots-container", children=create_plots())
    ]
)

@app.callback(
    Output("uploaded-parameters-info", "children"),
    Output("input-parameters-container", "children"),
    Input("upload-parameters", "contents"),
    State("upload-parameters", "filename"),
)
def load_parameters(contents, filename):
    global current_parameters, parameter_series, available_parameters
    
    if contents is None:
        return "", create_input_parameters_table()
    
    try:
        content_str = contents.split(",")[1]
        decoded = base64.b64decode(content_str).decode("utf-8")
        parameters_dict = json.loads(decoded)
        
        current_parameters = parameters_dict
        available_parameters = list(parameters_dict.keys())
        parameter_series = generate_parameter_series(parameters_dict)
        
        info_text = f"Загружены параметры: {', '.join(available_parameters)} | Серий: {len(parameter_series)}"
        
        return info_text, create_input_parameters_table()
        
    except Exception as e:
        return f"Ошибка: {str(e)}", create_input_parameters_table()

@app.callback(
    Output("current-run-id", "data"),
    Output("is-running", "data"),
    Output("log-interval", "disabled"),
    Input("run-btn", "n_clicks"),
    State("input-parameters-table", "data"),
    prevent_initial_call=True,
)
def run_calculations(n_clicks, table_data):
    global parameter_series, available_parameters
    
    if not table_data:
        return None, False, True
    
    parameter_series = pd.DataFrame(table_data)
    
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
                    error_msg = f"Ошибка в серии {idx + 1}: {str(e)}"
                    with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                        f.write(error_msg + "\n")
            
            with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                f.write(f"\nВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ\n")
                
        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            with open(os.path.join(BASE_DIR, folder, "log.txt"), "a", encoding="utf-8") as f:
                f.write(error_msg + "\n")
    
    thread = threading.Thread(target=run_tasks_thread, daemon=True)
    thread.start()
    
    return folder, True, False

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
    
    if "ВСЕ РАСЧЕТЫ ЗАВЕРШЕНЫ" in log_content and is_running:
        return log_content, False, True
    
    return log_content, is_running, False

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