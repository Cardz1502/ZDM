import requests
import json
import time

# Configurações
SERVICE_URL = "http://localhost:5000/predict"
TEST_CASES = [
    {
        "start_time": "2025-06-04 13:19:47",
        "filename": "zdm4ms~4"  # L
    }
]

def test_service():
    """Envia requisições de teste ao prediction_service."""
    headers = {"Content-Type": "application/json"}

    for test_case in TEST_CASES:
        print(f"\nEnviando teste para: {test_case['filename']}")
        try:
            response = requests.post(SERVICE_URL, json=test_case, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print("Resposta:")
            print(json.dumps(response.json(), indent=2))
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar requisição: {e}")
        time.sleep(1)  # Pausa entre testes

if __name__ == "__main__":
    print("Iniciando testes do prediction_service...")
    test_service()
    print("\nTestes concluídos. Verifique o log em ./data/prediction_service.log")