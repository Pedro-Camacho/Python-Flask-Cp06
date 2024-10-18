from flask import Flask, render_template_string
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json

# Constantes para MQTT
MQTT_BROKER = "20.206.240.145"  # Substitua pelo endereço do seu broker
MQTT_TOPIC = "/TEF/hosp200/attrs/l"  # Substitua pelo seu tópico
MQTT_TOPIC_2 = "/TEF/hosp200/attrs/t"  # Substitua pelo seu tópico
MQTT_TOPIC_3 = "/TEF/hosp200/attrs/h"  # Substitua pelo seu tópico


# Inicializa o aplicativo Flask e o SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Variável global para armazenar o último valor do potenciômetro
ultimo_valor_luminosidade = None
ultimo_valor_temperatura = None
ultimo_valor_umidade = None


# Funções de callback do MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado com código de resultado " + str(rc))
    client.subscribe(MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC_2)
    client.subscribe(MQTT_TOPIC_3)

def on_message(client, userdata, msg):
    global ultimo_valor
    try:
        #pegando informações luminosidade
        payload = json.loads(msg.payload)
        ultimo_valor_luminosidade = payload  # Supondo que o payload seja um objeto JSON
        socketio.emit('novo_dado_luminosidade', {'valor': ultimo_valor_luminosidade})  # Emite dados para o cliente
        print(f"Mensagem recebida: {ultimo_valor_luminosidade}")  # Saída de depuração
        
        #pegando informações temperatura
        payload = json.loads(msg.payload)
        ultimo_valor_temperatura = payload  # Supondo que o payload seja um objeto JSON
        socketio.emit('novo_dado_temperatura', {'valor': ultimo_valor_temperatura})  # Emite dados para o cliente
        print(f"Mensagem recebida: {ultimo_valor_temperatura}")  # Saída de depuração
        
        #pegando informações luminosidade
        payload = json.loads(msg.payload)
        ultimo_valor_umidade = payload  # Supondo que o payload seja um objeto JSON
        socketio.emit('novo_dado_umidade', {'valor': ultimo_valor_umidade})  # Emite dados para o cliente
        print(f"Mensagem recebida: {ultimo_valor_umidade}")  # Saída de depuração
        
    except json.JSONDecodeError:
        print("Falha ao decodificar JSON")

# Configura o cliente MQTT e conecta
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()  # Inicia o loop MQTT em uma thread separada

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Visualizador de Dados do Potenciômetro</title>
            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
            <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
            <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                canvas {
                    max-width: 400px;
                    margin: auto;
                }
                #valor {
                    font-size: 48px; /* Tamanho da fonte aumentado */
                    font-weight: bold; /* Texto em negrito */
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mt-5">Luminosidade</h1>
                <canvas id="gauge" width="400" height="400"></canvas>
                <div id="valor" class="mt-3">
                    Aguardando dados...
                </div>
            </div>

            <script>
                var ctx = document.getElementById('gauge').getContext('2d');
                var gaugeChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Valor', 'Restante'],
                        datasets: [{
                            label: 'Valor',
                            data: [0, 100], // Valores iniciais (a serem atualizados)
                            backgroundColor: ['#36A2EB', '#E0E0E0'],
                            borderWidth: 1,
                        }]
                    },
                    options: {
                        responsive: true,
                        cutoutPercentage: 70,
                        animation: {
                            animateRotate: true,
                        }
                    }
                });

                $(document).ready(function() {
                    var socket = io.connect('http://' + document.domain + ':' + location.port);
                    socket.on('novo_dado_luminosidade', function(data) {
                        $('#valor').text('Medição: ' + data.valor);
                        // Atualiza o gráfico gauge com o novo valor
                        gaugeChart.data.datasets[0].data[0] = data.valor; // Atualiza a parte do valor do gráfico de rosca
                        gaugeChart.data.datasets[0].data[1] = 100 - data.valor; // Parte restante (supondo que o valor máximo seja 100)
                        gaugeChart.update(); // Atualiza o gráfico
                    });
                });
            </script>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    socketio.run(app, debug=True)
