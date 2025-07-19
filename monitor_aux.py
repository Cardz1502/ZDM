from flask import Flask, request, jsonify
import requests
import time
import threading
import json
import re
import datetime

API_KEY = "-cqzgIHdAaLvW-9EbK6dXW5019dvLPgNyxP7tEwscFw"
AAS_URL = "192.168.250.110:5001"
MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware
CSV_URL = '192.168.250.108:5000'  # URL do CSV

stop_m114 = threading.Event()
stop_m220 = threading.Event()
stop_info_loop = threading.Event()
m114_response_received = threading.Event()
m220_response_received = threading.Event()

# Inicialmente setados para permitir o envio do primeiro comando
m114_response_received.set()
m220_response_received.set()



# CLASSE PrinterData
# Esta classe é usada para armazenar os dados do monitoramento da impressora
class PrinterData:
    def __init__(self):
        self.nozzle_temp = None
        self.nozzle_target = None
        self.nozzle_delta = None
        self.bed_temp = None
        self.bed_target = None
        self.bed_delta = None
        self.nozzle_pwm = None
        self.bed_pwm = None
        self.x = None
        self.y = None
        self.z = None
        self.extrusion_level = None
        self.speed_factor = None

    def to_dict(self):
        return {
            "NozzleTemp": self.nozzle_temp,
            "NozzleTarget": self.nozzle_target,
            "NozzleDelta": self.nozzle_delta,
            "BedTemp": self.bed_temp,
            "BedTarget": self.bed_target,
            "BedDelta": self.bed_delta,
            "NozzlePWM": self.nozzle_pwm,
            "BedPWM": self.bed_pwm,
            "X": self.x,
            "Y": self.y,
            "Z": self.z,
            "ExtrusionLevel": self.extrusion_level,
            "SpeedFactor": self.speed_factor
        }
    
data = PrinterData()
# Iniciar Flask
app = Flask(__name__)



def send_command(destination, msg):
    
    # Criar a mensagem para o middleware
        payload = {
            "destination": destination,
            "msg": msg,
            "key": API_KEY
        }

        print(f"[INFO] Enviando para middleware: {msg}")

        # Enviar comando para o middleware
        response = requests.post(f"{MIDDLEWARE_URL}:1880/printer/command", json=payload, timeout=10)
        response.raise_for_status()  # levanta erro se status code for 4xx ou 5xx
        #print(f"[INFO] Middleware respondeu: {response.status_code} - {response.text}")

def get_status(destination):
    
    # Criar a mensagem para o middleware
        payload = {
            "destination": destination,
            "key": API_KEY
        }

        #print(f"[INFO] Enviando para middleware: {payload}")

        # Enviar comando para o middleware
        response = requests.post(f"{MIDDLEWARE_URL}:1880/printer/status", json=payload, timeout=10)
        response.raise_for_status()  # levanta erro se status code for 4xx ou 5xx
        #print(f"[INFO] Middleware respondeu: {response.status_code} - {response.text}")
        job_data = response.json()
        state = job_data["state"]
        return state

def start_m114_loop(ip_printer):
    def loop_m114():
        while not stop_m114.is_set():
            if m114_response_received.wait(timeout=5):  # Espera a resposta anterior (máximo 5s)
                try:
                    m114_response_received.clear()  # Vai esperar a próxima resposta
                    send_command(ip_printer, "M114")
                except Exception as e:
                    print(f"[ERRO] Falha ao enviar M114: {e}")
                    m114_response_received.set()  # Evita deadlock
            else:
                print("[WARN] Timeout à espera de M114. Reenviando comando.")
                # Tenta novamente pois pode ter perdido resposta
                m114_response_received.set()  # Libera para novo envio no próximo loop

            time.sleep(0.5)

    threading.Thread(target=loop_m114, daemon=True).start()




def start_m220_loop(ip_printer):
    def loop_m220():
        while not stop_m220.is_set():
            if m220_response_received.wait(timeout=5):  # Espera até 5s pela resposta
                try:
                    m220_response_received.clear()
                    send_command(ip_printer, "M220")
                except Exception as e:
                    print(f"[ERRO] Falha ao enviar M220: {e}")
                    m220_response_received.set()
            else:
                print("[WARN] Timeout à espera de M220. Reenviando comando.")
                m220_response_received.set()

            time.sleep(0.5)

    threading.Thread(target=loop_m220, daemon=True).start()




def printer_sub(destination):
    
    # Criar a mensagem para o middleware
        payload = {
            "destination": destination,
            "username": "rics",
            "key": API_KEY
        }

        #print(f"[INFO] Enviando para middleware: {payload}")

        # Enviar comando para o middleware
        response = requests.post(f"{MIDDLEWARE_URL}:1880/printer/sub", json=payload, timeout=10)
        response.raise_for_status()  # levanta erro se status code for 4xx ou 5xx
        print(f"[INFO] Subscrito ao Middleware: {response.status_code} - {response.text}")

def send_to_aas(destination, msg):
    
    # Criar a mensagem para o middleware
        payload = {
            "destination": destination,
            "msg": msg,
        }

        
        print(f"[INFO] Enviando DADOS da aas para middleware: {msg}")

        # Enviar comando para o middleware
        response = requests.post(f"{MIDDLEWARE_URL}:1880/aas/append", json=payload, timeout=10)
        response.raise_for_status()  # levanta erro se status code for 4xx ou 5xx

def send_to_csv(destination, msg):
    
    # Criar a mensagem para o middleware
        payload = {
            "destination": destination,
            "msg": msg,
        }

        
        print(f"[INFO] Enviando DADOS do csv para middleware: {msg}")

        # Enviar comando para o middleware
        response = requests.post(f"{MIDDLEWARE_URL}:1880/csv/append", json=payload, timeout=10)
        response.raise_for_status()  # levanta erro se status code for 4xx ou 5xx


def get_printer_info(destination, filename):
    payload = {
        "destination": destination
    }

    try:
        response = requests.post(f"{MIDDLEWARE_URL}:1880/printer/info", json=payload, timeout=10)
        response.raise_for_status()
        message_data = response.json()
    except Exception as e:
        print(f"[ERRO] Ao contactar middleware: {e}")
        return

    last_temp = None

    for item in message_data:
        current = item.get("current", {})
        logs = current.get("logs", [])

        for log in logs:
            log = log.strip()

            # Temperatura
            temp_match = re.search(r"(?:Recv:\s*)?T:([\d.]+)\s*/([\d.]+)\s*B:([\d.]+)\s*/([\d.]+)\s*@:(\d+)\s*B@:(\d+)", log)
            if temp_match:
                
                last_temp = {
                    "nozzle_temp": float(temp_match.group(1)),
                    "nozzle_target": float(temp_match.group(2)),
                    "bed_temp": float(temp_match.group(3)),
                    "bed_target": float(temp_match.group(4)),
                    "nozzle_pwm": int(temp_match.group(5)),
                    "bed_pwm": int(temp_match.group(6)),
                }
                continue

            # Posição
            pos_match = re.search(r"X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)\s+E:([-\d.]+)", log)
            if pos_match and last_temp:
                # print informações de posição encontradas
                print(f"[INFO] Posição encontrada: {pos_match.group(0)}")
                # Montar dados para enviar
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pos_data = {
                    "X": float(pos_match.group(1)),
                    "Y": float(pos_match.group(2)),
                    "Z": float(pos_match.group(3)),
                    "E": float(pos_match.group(4)),
                }
                

                data = {
                    "timestamp": timestamp,
                    "temp_nozzle": last_temp["nozzle_temp"],
                    "temp_target_nozzle": last_temp["nozzle_target"],
                    "temp_delta_nozzle": last_temp["nozzle_temp"] - last_temp["nozzle_target"],
                    "pwm_nozzle": last_temp["nozzle_pwm"],
                    "temp_bed": last_temp["bed_temp"],
                    "temp_target_bed": last_temp["bed_target"],
                    "temp_delta_bed": last_temp["bed_temp"] - last_temp["bed_target"],
                    "pwm_bed": last_temp["bed_pwm"],
                    "X": pos_data["X"],
                    "Y": pos_data["Y"],
                    "Z": pos_data["Z"],
                    "E": pos_data["E"],
                    "speed_factor": None,
                    "filename": filename
                }

                m114_response_received.set()
                send_to_aas(AAS_URL, data)
                send_to_csv(CSV_URL, data)
                continue

            # Speed Factor
            speed_match = re.search(r"FR:([\d.]+)%", log)
            if speed_match and last_temp:
                # print informações de velocidade encontradas
                print(f"[INFO] Velocidade encontrada: {speed_match.group(0)}")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                speed_factor = float(speed_match.group(1))

                data = {
                    "timestamp": timestamp,
                    "temp_nozzle": last_temp["nozzle_temp"],
                    "temp_target_nozzle": last_temp["nozzle_target"],
                    "temp_delta_nozzle": last_temp["nozzle_temp"] - last_temp["nozzle_target"],
                    "pwm_nozzle": last_temp["nozzle_pwm"],
                    "temp_bed": last_temp["bed_temp"],
                    "temp_target_bed": last_temp["bed_target"],
                    "temp_delta_bed": last_temp["bed_temp"] - last_temp["bed_target"],
                    "pwm_bed": last_temp["bed_pwm"],
                    "X": None,
                    "Y": None,
                    "Z": None,
                    "E": None,
                    "speed_factor": speed_factor,
                    "filename": filename
                }
                m220_response_received.set()

                send_to_aas(AAS_URL, data)
                send_to_csv(CSV_URL, data)
                continue


def start_printer_info_loop(ip_printer, filename):                            #to_do: VER ATRASOS DE M114, VER SE AS MENSAGENS TÃO A SER GUARDADAS PARA SEREM ENVIADAS MAIS TARDE(TEMOS QUE LIMPAR O BUFFER)
    def loop():
        while True:
            try:
                get_printer_info(ip_printer, filename)
            except Exception as e:
                print(f"[ERRO] Falha ao obter info da impressora: {e}")
            time.sleep(5)

            try:
                state = get_status(ip_printer)
                if state.lower() == "operational":
                    print("[LOOP] Parando monitoramento de info: impressora voltou a 'operational'")
                    stop_info_loop.set()
            except:
                pass

    threading.Thread(target=loop, daemon=True).start()

def wait_for_printing_and_start_monitoring(ip_printer, filename):
    try:
        while True:
            state = get_status(ip_printer).lower()
            print(f"[INFO] Estado atual da impressora: {state}")

            if state == "printing from sd":
                print("[INFO] Impressora iniciou impressão. Iniciando monitorização...")
                printer_sub(ip_printer)
                start_printer_info_loop(ip_printer, filename)
                start_m114_loop(ip_printer)
                start_m220_loop(ip_printer)
                break

            elif state == "operational":
                print("[INFO] Impressora ainda está a aquecer...")

            else:
                print(f"[INFO] Estado inesperado: {state}")

            time.sleep(2)

    except Exception as e:
        print(f"[ERRO - Thread de monitorização] {e}")


        

@app.route('/start', methods=['POST'])
def start():
    try:
        data = request.get_json()
        print("[INFO] Dados recebidos:", data)

        filename = data["filename"]
        speed_factor = data["speed_factor"]
        ip_printer = data["ip_printer"]
        id = data["id"]

        print("[INFO] filename:", filename)
        print("[INFO] speed_factor:", speed_factor)
        print("[INFO] ip_printer:", ip_printer)
        print("[INFO] id:", id)

        # Envia comandos iniciais
        send_command(ip_printer, "M27 S0")
        send_command(ip_printer, f"M23 {filename}")
        send_command(ip_printer, "M24")
        send_command(ip_printer, f"M220 S{speed_factor}")

        # Limpa as flags
        stop_info_loop.clear()
        stop_m114.clear()
        stop_m220.clear()

        # Inicia a verificação em background
        threading.Thread(
            target=wait_for_printing_and_start_monitoring,
            args=(ip_printer, filename),
            daemon=True
        ).start()

        return jsonify({"status": "mensagem encaminhada com sucesso"}), 200

    except Exception as e:
        print(f"[ERRO] {e}")
        return jsonify({"error": "erro interno"}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # acessível na rede local
    #quero chama
