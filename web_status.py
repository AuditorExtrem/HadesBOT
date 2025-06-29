
from flask import Flask
import threading
import time
from datetime import datetime
import pytz

app = Flask(__name__)

def get_hora_brasilia():
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(brasilia_tz)

@app.route('/')
def status():
    agora = get_hora_brasilia()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot HADES - Status</title>
        <meta charset="utf-8">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                background: #2f3136; 
                color: white; 
                text-align: center; 
                padding: 50px;
            }}
            .status {{ 
                background: #36393f; 
                padding: 30px; 
                border-radius: 10px; 
                max-width: 500px; 
                margin: 0 auto;
            }}
            .online {{ color: #43b581; }}
        </style>
    </head>
    <body>
        <div class="status">
            <h1>🤖 Bot HADES</h1>
            <h2 class="online">✅ Bot está ATIVO!</h2>
            <p><strong>Horário de Brasília:</strong> {agora.strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <p><strong>Status:</strong> Online 24/7</p>
            <p><strong>Avisos automáticos:</strong> Funcionando</p>
            <p><strong>Comandos:</strong> 8 slash commands ativos</p>
            <hr>
            <p>🎮 Gerenciando servidores Roblox</p>
            <p>📢 Enviando avisos diários automáticos</p>
        </div>
    </body>
    </html>
    """

def run_web():
    app.run(host='0.0.0.0', port=5000, debug=False)

def start_web_server():
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Servidor web iniciado na porta 5000")
