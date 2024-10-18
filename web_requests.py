import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import requests
from datetime import datetime
import pytz

# Constants for IP and port
IP_ADDRESS = "20.206.240.145"
PORT_STH = 8666
DASH_HOST = "127.0.0.1"  # Set this to "0.0.0.0" to allow access from any IP

# Function to get potentiometer data from the API
def get_luminosity_data(lastN):
    url = f"http://{IP_ADDRESS}:{PORT_STH}/STH/v1/contextEntities/type/hosp/id/urn:ngsi-ld:hosp:200/attributes/luminosity?lastN={lastN}"
    headers = {
        'fiware-service': 'smart',
        'fiware-servicepath': '/'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        try:
            values = data['contextResponses'][0]['contextElement']['attributes'][0]['values']
            return values
        except KeyError as e:
            print(f"Erro de chave: {e}")
            return []
    else:
        print(f"Erro ao acessar {url}: {response.status_code}")
        return []

# Function to convert UTC timestamps to Lisbon time
def convert_to_lisbon_time(timestamps):
    utc = pytz.utc
    lisbon = pytz.timezone('Europe/Lisbon')
    converted_timestamps = []
    for timestamp in timestamps:
        try:
            timestamp = timestamp.replace('T', ' ').replace('Z', '')
            converted_time = utc.localize(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')).astimezone(lisbon)
        except ValueError:
            converted_time = utc.localize(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')).astimezone(lisbon)
        converted_timestamps.append(converted_time)
    return converted_timestamps

# Set lastN value
lastN = 10  # Get 10 most recent points at each interval

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Visualizador de Dados do Ldr'),
    dcc.Graph(id='luminosity-graph'),

    # Store to hold historical data
    dcc.Store(id='luminosity-data-store', data={'timestamps': [], 'luminosity_values': []}),

    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Atualiza a cada 5 segundos (5000 milissegundos)
        n_intervals=0
    )
])

@app.callback(
    Output('luminosity-data-store', 'data'),
    Input('interval-component', 'n_intervals'),
    State('luminosity-data-store', 'data')
)
def update_data_store(n, stored_data):
    # Get luminosity data
    data_luminosity = get_luminosity_data(lastN)

    if data_luminosity:
        # Extract values and timestamps
        luminosity_values = [float(entry['attrValue']) for entry in data_luminosity]  # Ensure values are floats
        timestamps = [entry['recvTime'] for entry in data_luminosity]

        # Convert timestamps to Lisbon time
        timestamps = convert_to_lisbon_time(timestamps)

        # Append new data to stored data only if the timestamp is unique
        for i in range(len(timestamps)):
            if timestamps[i] not in stored_data['timestamps']:
                stored_data['timestamps'].append(timestamps[i])
                stored_data['luminosity_values'].append(luminosity_values[i])

        return stored_data

    return stored_data

@app.callback(
    Output('luminosity-graph', 'figure'),
    Input('luminosity-data-store', 'data')
)
def update_graph(stored_data):
    if stored_data['timestamps'] and stored_data['luminosity_values']:
        
        # Calculate mean luminosity value
        mean_luminosity = sum(stored_data['luminosity_values']) / len(stored_data['luminosity_values'])

        # Create traces for the plot with improved styling
        trace_luminosity = go.Scatter(
            x=stored_data['timestamps'],
            y=stored_data['luminosity_values'],
            mode='lines+markers',
            name='Valor do Potenciômetro',
            line=dict(color='orange', width=2),
            marker=dict(size=6)
        )

        # Create a trace for the mean value (only two points)
        trace_mean = go.Scatter(
            x=[stored_data['timestamps'][0], stored_data['timestamps'][-1]],
            y=[mean_luminosity, mean_luminosity],
            mode='lines',
            name='Valor Médio do Potenciômetro',
            line=dict(color='blue', dash='dash', width=2)
        )

        # Create figure with enhanced layout settings
        fig_luminosity = go.Figure(data=[trace_luminosity, trace_mean])

        fig_luminosity.update_layout(
            title='Valores do Potenciômetro ao Longo do Tempo',
            xaxis_title='Timestamp',
            yaxis_title='Valor do Potenciômetro',
            hovermode='closest',
            template='plotly_white',  # Use a clean template for better aesthetics
            margin=dict(l=40, r=40, t=40, b=40),  # Add margins for better spacing
            font=dict(size=12)  # Increase font size for readability
        )

        return fig_luminosity

    return {}

if __name__ == '__main__':
    app.run_server(debug=True, host=DASH_HOST, port=8050)
