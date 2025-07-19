import requests
import json

# URL onde o teu modelo está a correr
URL = "http://localhost:5000/predict"  # ou outro IP/porta se estiver noutro sítio

# Carregar o JSON com os dados de teste
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Enviar POST para o endpoint de previsão
response = requests.post(URL, json=data)

# Mostrar a resposta
if response.status_code == 200:
    print("[✔] Previsão recebida:")
    print(response.text)
else:
    print(f"[✖] Erro {response.status_code}: {response.text}")
