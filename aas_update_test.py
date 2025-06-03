import requests
import time

# Configurações do AASX Server
AAS_URL = "http://192.168.250.224:5001/submodels/aHR0cHM6Ly9leGFtcGxlLmNvbS9pZHMvc20vNjA1MF8zMTMwXzYwNTJfODY2MA/submodel-elements"
AAS_HEADERS = {"Content-Type": "application/json"}

# Dados base para o corpo da requisição ao AAS
AAS_BASE_DATA = {
    "category": "",
    "idShort": "value",
    "semanticId": {"type": "ModelReference", "keys": [{"type": "ConceptDescription", "value": "https://example.com/ids/cd/1162_4162_5052_4762"}]},
    "valueType": "xs:string",
    "modelType": "Property"
}

# Mapeamento de variáveis para variablesXX
AAS_VARIABLES = {
    "timestamp": {"variable_id": 1},  # TimeStamp
    "nozzle_temp": {"variable_id": 2},  # NozzleTemp
    "nozzle_target": {"variable_id": 3},  # NozzleTarget
    "bed_temp": {"variable_id": 4},  # BedTemp
    "bed_target": {"variable_id": 5},  # BedTarget
    "x": {"variable_id": 6},  # X
    "y": {"variable_id": 7},  # Y
    "z": {"variable_id": 8},  # Z
    "extrusion_level": {"variable_id": 9},  # ExtrusionLevel
    "filename": {"variable_id": 10},  # Filename
    "nozzle_delta": {"variable_id": 11},  # NozzleDelta
    "bed_delta": {"variable_id": 12},  # BedDelta
    "nozzle_pwm": {"variable_id": 13},  # NozzlePWM
    "bed_pwm": {"variable_id": 14},  # BedPWM
    "speed_factor": {"variable_id": 15} # SpeedFactor
}

# Função para atualizar uma variável no AAS
def update_aas_variable(variable_key, value):
    if value is None:
        return  # Não atualizar se o valor for None
    config = AAS_VARIABLES.get(variable_key)
    if not config:
        print(f"Variável {variable_key} não encontrada no mapeamento AAS_VARIABLES")
        return
    variable_id = config["variable_id"]
    url = f"{AAS_URL}variables{variable_id:02d}.value"
    data = AAS_BASE_DATA.copy()
    data["value"] = str(value)
    try:
        response = requests.put(url, headers=AAS_HEADERS, json=data, timeout=10)
        if response.status_code == 200 or response.status_code == 204 :
            print(f"Atualizado variables{variable_id:02d} ({variable_key}) para {value} às {time.strftime('%H:%M:%S')}")
        else:
            print(f"Erro ao atualizar variables{variable_id:02d} ({variable_key}): {response.status_code}")
    except Exception as e:
        print(f"Erro na requisição ao AAS para {variable_key}: {e}")

# Valores de teste
test_values = {
    "nozzle_temp": 212.5,
    "nozzle_target": 210.0,
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