import requests
import time

# Configurações do AASX Server
AAS_URL = "http://192.168.250.224:5001/submodels/aHR0cHM6Ly9leGFtcGxlLmNvbS9pZHMvc20vNjA1MF8zMTMwXzYwNTJfODY2MA==/submodel-elements/"
AAS_HEADERS = {"Content-Type": "application/json"}

# Dados base para o corpo da requisição ao AAS
AAS_BASE_DATA = {
    "category": "",
    "idShort": "value",
    "semanticId": {"type": "ModelReference", "keys": [{"type": "ConceptDescription", "value": "https://example.com/ids/cd/1162_4162_5052_4762"}]},
    "valueType": "xs:string",
    "modelType": "Property"
}

# Mapeamento de variáveis para idShort
AAS_VARIABLES = {
    "timestamp": {"id_short": "timestamp"},       # Timestamp
    "nozzle_temp": {"id_short": "nozzle_temp"},   # NozzleTemp
    "nozzle_target": {"id_short": "nozzle_target"}, # NozzleTarget
    "bed_temp": {"id_short": "bed_temp"},         # BedTemp
    "bed_target": {"id_short": "bed_target"},     # BedTarget
    "x": {"id_short": "x"},                       # X
    "y": {"id_short": "y"},                       # Y
    "z": {"id_short": "z"},                       # Z
    "extrusion_level": {"id_short": "extrusion_level"}, # ExtrusionLevel
    "filename": {"id_short": "filename"},         # Filename
    "nozzle_delta": {"id_short": "nozzle_delta"}, # NozzleDelta
    "bed_delta": {"id_short": "bed_delta"},       # BedDelta
    "nozzle_pwm": {"id_short": "nozzle_pwm"},     # NozzlePWM
    "bed_pwm": {"id_short": "bed_pwm"},           # BedPWM
    "speed_factor": {"id_short": "speed_factor"}  # SpeedFactor
}

# Constantes de configuração
MAX_RETRIES = 5
HTTP_TIMEOUT = 30
RETRY_WAIT = 10

def update_aas_variable(variable_key, value):
    if value is None:
        return  # Não atualizar se o valor for None
    config = AAS_VARIABLES.get(variable_key)
    if not config:
        print(f"Variável {variable_key} não encontrada no mapeamento AAS_VARIABLES")
        return
    id_short = config["id_short"]
    url = f"{AAS_URL}{id_short}.value"
    data = AAS_BASE_DATA.copy()
    data["value"] = str(value)
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.put(url, headers=AAS_HEADERS, json=data, timeout=HTTP_TIMEOUT)
            if response.status_code in [200, 204]:  # Aceitar 200 e 204 como sucesso
                print(f"Atualizado {id_short}.value ({variable_key}) para {value} às {time.strftime('%H:%M:%S')}")
                return
            else:
                print(f"Erro ao atualizar {id_short}.value ({variable_key}): {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Erro na requisição ao AAS para {variable_key} (tentativa {retries+1}/{MAX_RETRIES}): {e}")

# Valores de teste
test_values = {
    "timestamp": "2025-06-03 14:32:00",  # Timestamp ajustado para 02:32 PM WEST
    "nozzle_temp": 21213.5,
    "nozzle_target": 213210.0,
    "bed_temp": 60.0,
    "bed_target": 60.0,
    "nozzle_delta": 0.5,
    "bed_delta": 0.0,
    "nozzle_pwm": 725,
    "bed_pwm": 50,
    "x": 10.2,
    "y": 15.3,
    "z": 5.0,
    "extrusion_level": 1.5,
    "filename": "test_print",
    "speed_factor": 102.0
}

# Loop de teste
print("Iniciando teste de atualização no AASX Server...")
for i in range(3):  # Executa 3 vezes para testar
    for variable_key, value in test_values.items():
        update_aas_variable(variable_key, value)
    print(f"Ciclo {i+1} concluído. Aguardando 5 segundos...")
    time.sleep(5)
print("Teste concluído!")