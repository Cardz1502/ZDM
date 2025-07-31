import requests

MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware
API_KEY = "-cqzgIHdAaLvW-9EbK6dXW5019dvLPgNyxP7tEwscFw"
AAS_URL = "192.168.250.104:5001"
MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware
CSV_URL = '192.168.250.104:5004'  # URL do CSV
MODELS_URL = '192.168.250.104:5002'

def csv_get_1(destination, msg):
    payload = {
        "destination": destination,
        "msg": msg,
    }
    print("INFO", "CSV_GET", f"Pedido de CSV enviado: {msg}")
    response = requests.post(f"{MIDDLEWARE_URL}:1880/csv/get", json=payload, timeout=10)
    response.raise_for_status()
    if response.status_code == 200:
        print("INFO", "CSV_GET", f"CSV recebido com sucesso de {destination}")
    return response


def send_csv_models_4(destination, msg):
    payload = {
        "destination": destination,
        "msg": msg
    }
    print("INFO", "MODEL", "Enviando dados para inferência do modelo")
    response = requests.post(f"{MIDDLEWARE_URL}:1880/model/predict4", json=payload, timeout=10)
    response.raise_for_status()
    if response.status_code == 200:
        print("INFO", "MODEL", f"Dados enviados com sucesso para {destination}")
    if response.status_code == 404:
        print("foi aqui")
    return response

def main():
    csv_response = csv_get_1(CSV_URL, {"start_time": "2025-07-29 20:44:03", "filename": "zdm4ms~4"})
    if csv_response is not None:
        try:
            csv_data = csv_response.json()
            model_response = send_csv_models_4(MODELS_URL, csv_data)
            if model_response is not None:
                model_data = model_response.json()
                predictions = model_data.get("predictions")
                print("INFO", "MODEL", f"Previsão do modelo recebida: {predictions}")
                if predictions is None:
                    print("ERRO", "MODEL", "Previsão do modelo não encontrada na resposta")
        except Exception as e:
            print("ERRO", "MODEL", f"Falha ao processar previsão do modelo: {e}")

if __name__ == "__main__":
    main()