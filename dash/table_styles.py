# Стили для таблицы DataTable
# Для DataTable используются пропсы style_*, которые нельзя заменить на CSS классы

TABLE_STYLES = {
    "style_table": {"overflowX": "auto"},
    "style_cell": {
        "padding": "8px",
        "textAlign": "left",
        "fontSize": "14px",
        "fontFamily": "Arial",
        "minWidth": "80px",
    },
    "style_header": {
        "backgroundColor": "#5b7cff",
        "color": "white",
        "fontWeight": "600",
        "textAlign": "center",
    },
    "style_data": {
        "backgroundColor": "white",
        "color": "black",
    },
    "style_data_conditional": [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#f8f9fa",
        },
        {
            "if": {"state": "selected"},
            "backgroundColor": "#b3d9ff",
        },
    ],
}




