from flask import Flask, request, jsonify
import requests
import time
import threading
import json
import re

API_KEY = "-cqzgIHdAaLvW-9EbK6dXW5019dvLPgNyxP7tEwscFw"

stop_m114 = threading.Event()
stop_m220 = threading.Event()
stop_info_loop = threading.Event()


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

MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware

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
    def monitor():
        while not stop_m114.is_set():
            try:
                send_command(ip_printer, "M114")
                time.sleep(5)
            except Exception as e:
                print(f"[LOOP ERRO] Falha ao enviar M114: {e}")
                time.sleep(2)

            try:
                state = get_status(ip_printer)
                if state.lower() == "operational":
                    print("[LOOP] Parando M114: impressora voltou a 'operational'")
                    stop_m114.set()
            except:
                pass
    threading.Thread(target=monitor, daemon=True).start()


def start_m220_loop(ip_printer):
    def loop_m220():
        while True:
            try:
                send_command(ip_printer, "M220")
                time.sleep(20)
            except Exception as e:
                print(f"[LOOP ERRO] Falha ao enviar M220: {e}")
            time.sleep(20)

            try:
                state = get_status(ip_printer)
                if state.lower() == "operational":
                    print("[LOOP] Parando M220: impressora voltou a 'operational'")
                    stop_m220.set()
            except:
                pass

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
        #print(f"[INFO] Middleware  SUB respondeu: {response.status_code} - {response.text}")

def get_printer_info(destination):
    payload = {
        "destination": destination
    }

    #print(f"[INFO] Enviando pedido de dados para middleware: {payload}")
    response = requests.post(f"{MIDDLEWARE_URL}:1880/printer/info", json=payload, timeout=10)
    response.raise_for_status()
    #print(f"[INFO] Middleware respondeu: {response.status_code} - {response.text}")
    
    message_data = response.json()

    last_temp = None
    pending_messages = []

    for item in message_data:
        current = item.get("current", {})
        logs = current.get("logs", [])

        for log in logs:
            log = log.strip()
            #print(f"[DEBUG] Analisando log: {log}")

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
                print(f"[INFO] Temp atualizada: {last_temp}")
                continue  # passar para o próximo log

            # Posição
            pos_match = re.search(r"X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)\s+E:([-\d.]+)", log)
            if pos_match:
                pos_data = {
                    "x": float(pos_match.group(1)),
                    "y": float(pos_match.group(2)),
                    "z": float(pos_match.group(3)),
                    "extrusion_level": float(pos_match.group(4)),
                }
                if last_temp:
                    pending_messages.append({
                        "type": "position",
                        "position": pos_data,
                        "temperature": last_temp.copy()
                    })
                    print(f"[INFO] Posição capturada com temperatura: {pos_data} @ {last_temp}")
                continue

            # Speed Factor
            speed_match = re.search(r"FR:([\d.]+)%", log)
            if speed_match:
                speed_factor = float(speed_match.group(1))
                if last_temp:
                    pending_messages.append({
                        "type": "speed",
                        "speed_factor": speed_factor,
                        "temperature": last_temp.copy()
                    })
                    print(f"[INFO] SpeedFactor capturado com temperatura: {speed_factor}% @ {last_temp}")
                continue

    return pending_messages  # ou processa como precisares

def start_printer_info_loop(ip_printer):                            #to_do: VER ATRASOS DE M114, ADICIONAR TIMESTAMPS, VER SE AS MENSAGENS TÃO A SER GUARDADAS PARA SEREM ENVIADAS MAIS TARDE(TEMOS QUE LIMPAR O BUFFER)
    def loop():
        while True:
            try:
                printer_info = get_printer_info(ip_printer)
                if printer_info:
                    for msg in printer_info:
                        print("[INFO] Mensagem capturada:")
                        print(json.dumps(msg, indent=4))
                        # Aqui podes gravar ou enviar os dados
                else:
                    print("[INFO] Nenhuma informação útil encontrada nos logs.")
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

        # Loop de espera até a impressora estar a imprimir
        while True:
            try:
                state = get_status(ip_printer).lower()
                print(f"[INFO] Estado atual da impressora: {state}")

                if state == "printing from sd":
                    print("[INFO] Impressora iniciou impressão. Iniciando monitorização...")
                    printer_sub(ip_printer)
                    start_printer_info_loop(ip_printer)
                    start_m114_loop(ip_printer)
                    start_m220_loop(ip_printer)
                    break  # sai do loop

                elif state == "operational":
                    print("[INFO] Impressora ainda está a aquecer...")

                else:
                    print(f"[INFO] Estado inesperado: {state}")

                time.sleep(2)

            except Exception as e:
                print(f"[ERRO] A verificar estado da impressora: {e}")
                time.sleep(2)

        return jsonify({"status": "mensagem encaminhada com sucesso"}), 200

    except Exception as e:
        print(f"[ERRO] {e}")
        return jsonify({"error": "erro interno"}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # acessível na rede local
    #quero chama
