import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

print("Iniciando testes do prediction_service_ok_nok...")

# Dados de teste
test_data = {
    "start_time": "2025-06-24 12:57:02",  # Ajuste para um timestamp válido em z_lower_1.csv
    "filename": "zd2c72~1"
}

# Enviar requisição
logger.info(f"Enviando teste para: {test_data['filename']}")
try:
    response = requests.post(
        "http://localhost:5002/predict",
        headers={"Content-Type": "application/json"},
        data=json.dumps(test_data)
    )
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Resposta: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    logger.error(f"Erro ao enviar requisição: {str(e)}")

print("Testes concluídos. Verifique o log em ./data/prediction_service_ok_nok.log")