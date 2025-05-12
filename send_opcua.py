from opcua import Client
import pandas as pd
import time
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/data/send_opcua.log"),
        logging.StreamHandler()
    ]
)

# Configurações do servidor OPC UA (ajustar com os valores reais da tua empresa)
OPCUA_URL = ""  # Substituir pelo endereço real do servidor
NODE_IDS = {
    "id_peça": "ns=2;s=Impressora.IdPeca",
    "media_temp_nozzle": "ns=2;s=Impressora.MediaTempNozzle",
    "max_temp_nozzle": "ns=2;s=Impressora.MaxTempNozzle",
    "resultado": "ns=2;s=Impressora.Resultado"
}

def send_to_opcua(data):
    try:
        # Conectar ao servidor OPC UA
        client = Client(OPCUA_URL)
        client.connect()
        logging.info("Conectado ao servidor OPC UA: %s", OPCUA_URL)

        # Enviar cada métrica para o nó correspondente
        for key, node_id in NODE_IDS.items():
            if key in data:
                node = client.get_node(node_id)
                value = float(data[key]) if key in ["media_temp_nozzle", "max_temp_nozzle"] else data[key]
                node.set_value(value)
                logging.info("Enviado %s=%s para %s", key, value, node_id)

        # Desconectar
        client.disconnect()
        logging.info("Desconectado do servidor OPC UA")

    except Exception as e:
        logging.error("Erro ao enviar dados para OPC UA: %s", e)

def main():
    csv_file = "/app/data/processed_data2.csv"
    if not os.path.exists(csv_file):
        logging.warning("Arquivo %s não encontrado. Aguardando dados...", csv_file)
        return

    # Ler o CSV mais recente
    df = pd.read_csv(csv_file)
    if df.empty:
        logging.warning("Nenhum dado no CSV.")
        return

    # Pegar a última linha (última impressão processada)
    latest_data = df.iloc[-1].to_dict()
    logging.info("Dados a enviar: %s", latest_data)

    # Enviar os dados
    send_to_opcua(latest_data)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # Enviar dados a cada 60 segundos