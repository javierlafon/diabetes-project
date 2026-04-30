import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os  # Necesario para leer variables de entorno

# --- 1. CARGA DE DATOS ---
try:
    # Nota: Asegúrate de que la ruta sea correcta en tu repositorio de Render
    df = pd.read_csv('../etl/diabetic_data_clean.csv')
    df['has_diabetes_secondary'] = ((df['diag_2_group'] == 'Diabetes') | (df['diag_3_group'] == 'Diabetes'))
except Exception as e:
    print(f"Error al cargar el CSV: {e}")

# --- 2. INICIALIZACIÓN DE LA APP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server  # EXPOSICIÓN DEL SERVIDOR PARA GUNICORN/RENDER

# --- 3. DISEÑO (LAYOUT) ---
app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Análisis Diabético", 
                        className="text-center text-primary my-4"), width=12)
    ]),
    
    # --- SECCIÓN 1: FILTROS GLOBALES ---
    dbc.Row([
        dbc.Col([
            html.Label("Segmentar por Género:", className="fw-bold"),
            dcc.Dropdown(
                id='gender-filter',
                options=[{'label': g, 'value': g} for g in df['gender'].unique() if pd.notna(g)] + [{'label': 'Todos', 'value': 'all'}],
                value='all',
                className="text-dark"
            ),
        ], width=3),
        
        dbc.Col([
            html.Label("Rango de Edad (Aproximada):", className="fw-bold"),
            dcc.RangeSlider(
                id='age-slider',
                min=df['age_numeric'].min(),
                max=df['age_numeric'].max(),
                value=[df['age_numeric'].min(), df['age_numeric'].max()],
                marks={i: {'label': f'{i}a', 'style': {'color': 'white', 'fontSize': '12px'}} 
                       for i in range(0, 101, 10)},
                step=5
            ),
        ], width=9),
    ], className="mb-4 p-3 border border-secondary rounded bg-dark shadow"),

    # --- FILAS DE GRÁFICOS ---
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-volumen')]), color="secondary", outline=True), width=6),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-edad')]), color="secondary", outline=True), width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-stay-diag')]), color="secondary", outline=True), width=6),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-diabetes')]), color="secondary", outline=True), width=6),
    ], className="mb-4"),

    html.Hr(className="my-5", style={"borderTop": "2px solid #3498db"}),
    
    dbc.Row([
        dbc.Col(html.H2("Distribución de Hospitalización", className="text-center text-info mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Ajustar detalle (Bins):", className="fw-bold"),
                    dcc.Slider(id='hist-bins', min=5, max=30, step=1, value=14, 
                               marks={i: str(i) for i in range(5, 31, 5)}),
                    html.Label("Mostrar Indicadores:", className="mt-4 fw-bold"),
                    dcc.Checklist(
                        id='hist-indicators',
                        options=[{'label': ' Media', 'value': 'mean'}, {'label': ' Mediana', 'value': 'median'}],
                        value=['mean', 'median'],
                        labelStyle={'display': 'block'},
                        inputStyle={"margin-right": "10px"}
                    ),
                ])
            ], color="dark", outline=True, className="h-100")
        ], width=3),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-distribucion')]), color="dark", outline=True), width=9),
    ], className="mb-5"),

    html.Hr(className="my-5", style={"borderTop": "2px solid #3498db"}),
    
    dbc.Row([
        dbc.Col(html.H2("Impacto de la Estabilidad del Tratamiento", className="text-center text-info mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Tipo de Visualización:", className="fw-bold"),
                    dcc.Dropdown(
                        id='treatment-view-type',
                        options=[
                            {'label': 'Conteo Total', 'value': 'group'},
                            {'label': 'Porcentaje Apilado (100%)', 'value': 'relative'}
                        ],
                        value='group',
                        clearable=False,
                        className="text-dark"
                    ),
                    html.P("Este gráfico cruza el estado de reingreso con los cambios en la medicación.", 
                           className="text-muted small mt-4")
                ])
            ], color="dark", outline=True, className="h-100")
        ], width=3),
        dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id='graph-estabilidad')]), color="dark", outline=True), width=9),
    ], className="mb-5"),
])

# --- 4. CALLBACKS ---

@app.callback(
    [Output('graph-volumen', 'figure'),
     Output('graph-edad', 'figure'),
     Output('graph-stay-diag', 'figure'),
     Output('graph-diabetes', 'figure')],
    [Input('gender-filter', 'value'),
     Input('age-slider', 'value')]
)
def update_global_graphs(gender, age_range):
    dff = df[(df['age_numeric'] >= age_range[0]) & (df['age_numeric'] <= age_range[1])]
    if gender and gender != 'all':
        dff = dff[dff['gender'] == gender]

    vol_data = dff['diag_1_group'].value_counts().reset_index()
    fig1 = px.bar(vol_data, y='diag_1_group', x='count', orientation='h',
                  title='1. EL ESCENARIO (Volumen)', color='count', color_continuous_scale='Blues')
    fig1.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'})

    age_avg = dff.groupby('age_numeric')['time_in_hospital'].mean().reset_index()
    fig2 = px.bar(age_avg, x='age_numeric', y='time_in_hospital',
                  title=' 3 - EL RELOJ BIOLÓGICO', color='time_in_hospital', color_continuous_scale='Reds')
    fig2.add_trace(go.Scatter(x=age_avg['age_numeric'], y=age_avg['time_in_hospital'],
                              mode='lines+markers', line=dict(color='white', width=2), name='Tendencia'))
    fig2.update_layout(template='plotly_dark', showlegend=False)

    avg_stay = dff.groupby('diag_1_group')['time_in_hospital'].mean().reset_index().sort_values('time_in_hospital')
    fig3 = px.bar(avg_stay, x='time_in_hospital', y='diag_1_group', orientation='h',
                  title='4 - EL NUDO (Costo de Tiempo)', color='time_in_hospital', color_continuous_scale='Oranges')
    fig3.update_layout(template='plotly_dark')

    reingreso = pd.crosstab(dff['has_diabetes_secondary'], dff['readmitted_status'], normalize='index') * 100
    reingreso = reingreso.reset_index()
    reingreso['has_diabetes_secondary'] = reingreso['has_diabetes_secondary'].map({True: 'Sin Diab. Sec.', False: 'Con Diab. Sec.'})
    fig4 = px.bar(reingreso, y='has_diabetes_secondary', x=[c for c in reingreso.columns if c != 'has_diabetes_secondary'],
                  title='5 - El Fantasma del Reingreso', color_discrete_sequence=['#27ae60', '#f39c12', '#c0392b'], orientation='h')
    fig4.update_layout(template='plotly_dark', barmode='stack')

    return fig1, fig2, fig3, fig4

@app.callback(
    Output('graph-distribucion', 'figure'),
    [Input('hist-bins', 'value'),
     Input('hist-indicators', 'value')]
)
def update_histogram(bins, indicators):
    fig = px.histogram(df, x='time_in_hospital', nbins=bins, marginal="box",
                       title='2 - Distribución de Días en el Hospital',
                       color_discrete_sequence=['skyblue'], opacity=0.7)
    if 'mean' in indicators:
        mean_v = df['time_in_hospital'].mean()
        fig.add_vline(x=mean_v, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_v:.2f}")
    if 'median' in indicators:
        med_v = df['time_in_hospital'].median()
        fig.add_vline(x=med_v, line_dash="solid", line_color="green", annotation_text=f"Mediana: {med_v:.2f}")
    fig.update_layout(template='plotly_dark', xaxis_title="Días", yaxis_title="Frecuencia")
    return fig

@app.callback(
    Output('graph-estabilidad', 'figure'),
    [Input('treatment-view-type', 'value')]
)
def update_treatment(view_type):
    order = ['Stable', 'Low Instability', 'High Instability']
    fig = px.histogram(
        df, 
        x='treatment_status', 
        color='readmitted_status',
        barmode=view_type,
        category_orders={'treatment_status': order},
        color_discrete_sequence=px.colors.sequential.Viridis,
        text_auto='.0f' if view_type == 'group' else False, 
        title='6 - Análisis de Reingreso según Estabilidad del Tratamiento'
    )
    if view_type == 'relative':
        fig.update_layout(barnorm='percent', yaxis_title="Porcentaje (%)")
    else:
        fig.update_layout(yaxis_title="Cantidad de Pacientes")
    fig.update_layout(template='plotly_dark', xaxis_title="Estado del Tratamiento")
    return fig

# --- EJECUCIÓN ---
if __name__ == '__main__':
    # Configuración para que Render asigne el puerto automáticamente
    port = int(os.environ.get("PORT", 8050))
    app.run(host='0.0.0.0', port=port, debug=False)