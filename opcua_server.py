import logging
import sys
from opcua import Server, ua
from threading import Thread
import time
import os

# Configurar logging para stdout e arquivo
log_dir = "/app/data"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, "octoprint_monitor2.log"))
    ]
)
logger = logging.getLogger(__name__)

# Reduzir a verbosidade do logging da biblioteca opcua
logging.getLogger("opcua").setLevel(logging.ERROR)

logger.info("Iniciando opcua_server.py...")

# Inicializar o servidor OPC UA
try:
    server = Server()
    logger.info("Servidor OPC UA criado com sucesso")
    server.set_endpoint("opc.tcp://0.0.0.0:4840")
    logger.info("Endpoint configurado com sucesso: opc.tcp://0.0.0.0:4840")
except Exception as e:
    logger.error(f"Erro ao inicializar o servidor: {e}")
    sys.exit(1)

# Definir um namespace personalizado
try:
    uri = "http://examples.com/impressora"
    idx = server.register_namespace(uri)
    logger.info(f"Namespace registrado com índice: {idx}")
except Exception as e:
    logger.error(f"Erro ao registrar namespace: {e}")
    sys.exit(1)

# Definir a estrutura de nós
root = server.get_objects_node()
try:
    impressora_node = root.add_object(idx, "Impressora")
    logger.info("Nó 'Impressora' criado com sucesso")
except Exception as e:
    logger.error(f"Erro ao criar nó 'Impressora': {e}")
    impressora_node = root.add_object(idx, "Impressora")
    logger.info("Nó 'Impressora' criado sem configuração de eventos")

# Definir nós para cada variável da classe PrinterData
nodes = {}
variables = ["NozzleTemp", "NozzleTarget", "NozzleDelta", "BedTemp", "BedTarget", "BedDelta",
             "NozzlePWM", "BedPWM", "X", "Y", "Z", "ExtrusionLevel", "AccelPrint",
             "AccelRetract", "AccelTravel", "JerkX", "JerkY"]
for var in variables:
    try:
        nodes[var] = impressora_node.add_variable(idx, var, 0.0)
        nodes[var].set_writable()  # Tornar gravável
        logger.info(f"Nó '{var}' criado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar nó '{var}': {e}")

# Dicionário para armazenar os dados atualizados
data_store = {var: 0.0 for var in variables}

# Função para atualizar os nós com os dados do data_store
def update_nodes():
    try:
        for var in variables:
            if(nodes[var].set_value(data_store[var])):
                logger.info(f"Atualizado nó {var} com valor {data_store[var]}")  # Atualiza o valor
            else:
                logger.info(f"MERDA {data_store[var]}")  
            #logger.info(f"DATA STORE VAR: {data_store[var]}")
            #logger.info(f"Atualizado nó {var} com valor {data_store[var]}")
        logger.info(f"Atualizado nós com dados: NozzleTemp={data_store['NozzleTemp']}, X={data_store['X']}, AccelPrint={data_store['AccelPrint']}")
    except Exception as e:
        logger.error(f"Erro ao atualizar nós: {e}")

# Função para o octoprint-api.py atualizar os dados
def update_data(data):
    global data_store
    try:
        updated = False
        for key, value in data.items():
            if key in data_store and value is not None:
                data_store[key] = float(value)
                updated = True
        if updated:
            update_nodes()  # Atualizar os nós imediatamente
            logger.info(f"Dados recebidos para atualização: {data}")
    except Exception as e:
        logger.error(f"Erro ao atualizar data_store: {e}")

# Iniciar o servidor em uma thread separada
def start_server():
    try:
        logger.info("Iniciando servidor OPC UA na porta 4840...")
        server.start()
        logger.info("Servidor OPC UA iniciado com sucesso.")
        # Verificar se os nós foram criados corretamente
        logger.info(f"Nós criados sob Impressora: {[node.get_browse_name().Name for node in impressora_node.get_children()]}")
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Iniciar o servidor em uma thread
    server_thread = Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Manter o script rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Encerrando servidor OPC UA...")
        server.stop()