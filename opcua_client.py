from opcua import Client, ua
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubHandler(object):
    def __init__(self, node_names):
        self.node_names = node_names  # Mapa de node_id para nome

    def datachange_notification(self, node, val, data):
        # Obter o nome do nó a partir do mapa pré-armazenado
        node_id = str(node.nodeid)
        node_name = self.node_names.get(node_id, "Unknown")
        logger.info(f"Atualização recebida - {node_name}: {val}")

def main():
    # Configurar o cliente com um tempo limite maior
    client = Client("opc.tcp://192.168.23.1:4840")  # Ajusta o IP conforme necessário
    client.set_timeout(5000)  # Aumentar o tempo limite para 5 segundos
    try:
        client.connect()
        logger.info("Conectado ao servidor OPC UA")

        # Obter o nó raiz e o nó Impressora
        root = client.get_root_node()
        impressora = root.get_child(["0:Objects", "2:Impressora"])  # Ajusta o índice do namespace (2) se necessário
        variables = ["NozzleTemp", "X", "AccelPrint"]
        nodes = {var: impressora.get_child(f"2:{var}") for var in variables}

        # Criar um mapa de node_id para nome
        node_names = {}
        for var, node in nodes.items():
            node_id = str(node.nodeid)
            node_names[node_id] = var  # Usar o nome da variável como identificador

        # Criar uma subscrição
        handler = SubHandler(node_names)
        sub = client.create_subscription(500, handler)  # 500ms é o intervalo de publicação
        handle = sub.subscribe_data_change([nodes[var] for var in variables])
        logger.info("Subscrição criada para os nós: %s", variables)

        # Manter o script rodando para receber notificações
        try:
            while True:
                # Opcional: Ler valores manualmente para comparação
                for var, node in nodes.items():
                    value = node.get_value()
                    logger.info(f"Valor lido manualmente - {var}: {value}")
                time.sleep(2)
        except KeyboardInterrupt:
            logger.info("Parando o monitoramento...")
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        sub.delete()  # Remove a subscrição
        client.disconnect()
        logger.info("Desconectado do servidor")

if __name__ == "__main__":
    main()