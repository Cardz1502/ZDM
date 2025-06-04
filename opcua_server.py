from opcua import Server
import time
import requests
import threading
import logging

# # Configuração de logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Reduzir o ruído dos logs da biblioteca opcua
# logging.getLogger("opcua.server.subscription_service").setLevel(logging.WARNING)
# logging.getLogger("opcua.server.internal_subscription").setLevel(logging.WARNING)
# logging.getLogger("opcua.server.uaprocessor").setLevel(logging.WARNING)
# logging.getLogger("opcua.server.address_space").setLevel(logging.WARNING)

# Configurações do AASX Server
AAS_URL = "http://192.168.250.224:5001/submodels/aHR0cHM6Ly9leGFtcGxlLmNvbS9pZHMvc20vNjA1MF8zMTMwXzYwNTJfODY2MA==/submodel-elements/"
AAS_HEADERS = {"Content-Type": "application/json"}
HTTP_TIMEOUT = 30

# Configuração do servidor OPC UA
server = Server()
url = "opc.tcp://0.0.0.0:4840"  # Porta padrão OPC UA
server.set_endpoint(url)
server.set_server_name("Impressora3D_AAS_OPCUA_Server")

# Registrar namespace
namespace = "Impressora3D"
idx = server.register_namespace(namespace)

# Criar objeto principal no espaço de endereçamento
objects = server.get_objects_node()
printer_obj = objects.add_object(idx, "Printer3D")

# Criar submodelo OperationalData como objeto
operational_data = printer_obj.add_object(idx, "OperationalData")

# Dicionário para armazenar as variáveis OPC UA
opcua_vars = {}

# Lista de métricas do OperationalData
metrics = [
    "nozzle_temp", "nozzle_target", "nozzle_delta", "nozzle_pwm",
    "bed_temp", "bed_target", "bed_delta", "bed_pwm",
    "x", "y", "z", "extrusion_level", "speed_factor", "filename", "timestamp"
]

# Inicializar variáveis no OPC UA
for metric in metrics:
    opcua_vars[metric] = operational_data.add_variable(idx, metric, 0.0 if metric != "filename" and metric != "timestamp" else "")
    opcua_vars[metric].set_writable(False)  # Somente leitura para clientes

# Função para atualizar os valores do OPC UA a partir do AAS
def update_opcua_from_aas():
    while True:
        try:
            for metric in metrics:
                url = f"{AAS_URL}{metric}.value"
                response = requests.get(url, headers=AAS_HEADERS, timeout=HTTP_TIMEOUT)
                if response.status_code == 200:
                    value = response.json().get("value", "")
                    if metric in ["filename", "timestamp"]:
                        opcua_vars[metric].set_value(value)
                        print(f"Atualizado {metric} no OPC UA: {value}")
                    else:
                        try:
                            opcua_vars[metric].set_value(float(value))
                        except ValueError:
                            print(f"Valor inválido para {metric}: {value}")
                            opcua_vars[metric].set_value(0.0)
                else:
                    print(f"Erro ao ler {metric} do AAS: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Erro ao atualizar OPC UA: {e}")
        time.sleep(5)  # Atualiza a cada 5 segundos, alinhado com M114

# Iniciar o servidor OPC UA
try:
    server.start()
    print(f"Servidor OPC UA iniciado em {url}")

    # Iniciar thread para atualizar os valores
    update_thread = threading.Thread(target=update_opcua_from_aas, daemon=True)
    update_thread.start()

    # Manter o servidor rodando
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Servidor OPC UA encerrado pelo usuário")
    server.stop()
except Exception as e:
    print(f"Erro ao iniciar o servidor OPC UA: {e}")
    server.stop()