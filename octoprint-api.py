import os
import requests
import time
from datetime import datetime
import csv
import websocket
import json
import threading
import re
import logging

# Configurações do OctoPrint
BASE_URL = "http://192.168.250.115"
API_KEY = "Yfvanr37vlCxeQCFi8_pdyrz-GrqYFIYh2RpYKYtQ0I"
USERNAME = "rics"
PASSWORD = "ricsricsjabjab"
UPDATE_INTERVAL_M114 = 5
TIMEOUT_LIMIT = 90
CSV_FILE = "/app/data/printer_data3.csv"
LOG_FILE = "/app/data/octoprint_monitor3.log"
CHECK_INTERVAL = 5

HEADERS = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

# Criar o diretório para logs e dados, se não existir
log_dir = "/app/data"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    logger.info("Diretório %s criado no contêiner", log_dir)

# Configurar logging para stdout e arquivo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        self.accel_print = None
        self.accel_retract = None
        self.accel_travel = None
        self.jerk_x = None
        self.jerk_y = None 

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
            "AccelPrint": self.accel_print,
            "AccelRetract": self.accel_retract,
            "AccelTravel": self.accel_travel,
            "JerkX": self.jerk_x,
            "JerkY": self.jerk_y
        }

class Control:
    def __init__(self):
        self.m114_waiting = False 
        self.m503_waiting = False
        self.m114_last_time = None
        self.m503_last_time = None
        self.session_key = None
        self.printerState = None 
        self.filename = None
        self.filename_obtained = False
        self.last_active_time = time.time()
        self.connection_failed_count = 0
        self.last_connection_check = time.time()
        self.websocket_active = False

data = PrinterData()
control = Control()
ws = None  # Variável global para a WebSocket

def login():
    global ws
    url = f"{BASE_URL}/api/login"
    payload = {"user": USERNAME, "pass": PASSWORD, "remember": True}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            control.session_key = response.json().get("session")
            logger.info("Login bem-sucedido! Chave de sessão: %s", control.session_key)
            control.connection_failed_count = 0
            return True
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro no login (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                logger.warning("Tentando novamente em %ds...", RETRY_WAIT)
                time.sleep(RETRY_WAIT)
            else:
                logger.error("Falha ao fazer login após %d tentativas.", MAX_RETRIES)
                control.connection_failed_count += 1
                if ws and control.connection_failed_count >= 10:  # Após 10 falhas consecutivas
                    logger.warning("OctoPrint offline por muito tempo. Fechando WebSocket.")
                    ws.close()
                    control.websocket_active = False
                return False

def check_printing_status():
    global ws
    url = f"{BASE_URL}/api/job"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            job_data = response.json()
            state = job_data["state"]
            control.printerState = state
            is_printing = state in ["Starting print from SD", "Printing from SD", "Printing"]
            if is_printing:
                control.last_active_time = time.time()
                if not control.websocket_active:
                    logger.info("Impressão detetada (%s). Reabrindo WebSocket...", state)
                    ws = start_websocket()
                    control.websocket_active = True
            logger.debug(f"Estado da impressora: {state}, is_printing: {is_printing}")
            control.connection_failed_count = 0
            return is_printing
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao verificar estado da impressora (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                control.connection_failed_count += 1
                control.printerState = "Unknown"
                if ws and control.connection_failed_count >= 10:  # Após 10 falhas consecutivas
                    logger.warning("OctoPrint offline por muito tempo. Fechando WebSocket.")
                    ws.close()
                    control.websocket_active = False
                return False

def get_current_filename_from_api():
    url = f"{BASE_URL}/api/job"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            job_data = response.json()
            file_info = job_data.get("job", {}).get("file", {})
            filename = file_info.get("name", "(no file)")
            if filename and filename.lower().endswith(".gco"):
                filename = filename[:-4]
            logger.info("Nome do arquivo obtido via API: %s", filename)
            return filename
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao obter nome do arquivo via API (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                return "(no file)"

def send_m114():
    global ws
    url = f"{BASE_URL}/api/printer/command"
    payload = {"command": "M114"}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            logger.info("Comando M114 enviado com sucesso!")
            control.m114_waiting = True
            control.m114_last_time = time.time()
            return
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao enviar M114 (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                control.m114_waiting = False
                control.m114_last_time = None
                if ws and control.connection_failed_count >= 3:
                    logger.warning("Reiniciando WebSocket devido a falha no M114.")
                    ws.close()
                    ws = start_websocket()

def send_m503():
    global ws
    url = f"{BASE_URL}/api/printer/command"
    payload = {"command": "M503"}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            logger.info("Comando M503 enviado com sucesso!")
            control.m503_waiting = True
            control.m503_last_time = time.time()
            return
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao enviar M503 (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                control.m503_waiting = False
                control.m503_last_time = None
                if ws and control.connection_failed_count >= 3:
                    logger.warning("Reiniciando WebSocket devido a falha no M503.")
                    ws.close()
                    ws = start_websocket()

def save_data(timestamp, is_m114=True):
    try:
        if not os.path.exists(CSV_FILE):
            logger.info("Criando novo arquivo CSV: %s", CSV_FILE)
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "temp_nozzle", "temp_target_nozzle", "temp_delta_nozzle",
                                 "pwm_nozzle", "temp_bed", "temp_target_bed", "temp_delta_bed", "pwm_bed",
                                 "X", "Y", "Z", "E", "accel_print",
                                 "accel_retract", "accel_travel",
                                 "jerk_x", "jerk_y", "filename"])
        else:
            logger.debug("Arquivo CSV já existe: %s", CSV_FILE)

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if is_m114:
            row = [timestamp_str, data.nozzle_temp, data.nozzle_target, data.nozzle_delta,
                   data.nozzle_pwm, data.bed_temp, data.bed_target, data.bed_delta, data.bed_pwm,
                   data.x, data.y, data.z, data.extrusion_level, None, None, None, None, None, control.filename]
            logger.info("Salvando M114: %s, Posição: X=%s, Y=%s, Z=%s, E=%s, Temperaturas: T:%s/%s, B:%s/%s",
                         timestamp_str, data.x, data.y, data.z, data.extrusion_level,
                         data.nozzle_temp, data.nozzle_target, data.bed_temp, data.bed_target)
        else:
            row = [timestamp_str, data.nozzle_temp, data.nozzle_target, data.nozzle_delta,
                   data.nozzle_pwm, data.bed_temp, data.bed_target, data.bed_delta, data.bed_pwm,
                   None, None, None, None, data.accel_print, data.accel_retract, data.accel_travel, data.jerk_x, data.jerk_y, control.filename]
            logger.info("Salvando M503: %s, Accel P=%s, R=%s, T=%s, Jerk X=%s, Y=%s, Temperaturas: T:%s/%s, B:%s/%s",
                         timestamp_str, data.accel_print, data.accel_retract, data.accel_travel,
                         data.jerk_x, data.jerk_y, data.nozzle_temp, data.nozzle_target, data.bed_temp, data.bed_target)

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row)
            logger.debug("Dados salvos no CSV: %s", row)
    except Exception as e:
        logger.error("Erro ao salvar dados no CSV: %s", e)

def on_message(ws, message):
    try:
        message_data = json.loads(message)
        if "connected" in message_data:
            logger.info("Conexão WebSocket estabelecida")
            return

        if "current" in message_data:
            current = message_data["current"]
            logs = current.get("logs", [])
            is_printing = check_printing_status()
            m204_received = False
            m205_received = False

            for log in logs:
                logger.debug("Mensagem recebida: %s", log)
                temp_match = re.search(r"T:([\d.]+)\s*/([\d.]+)\s*B:([\d.]+)\s*/([\d.]+)\s*@:(\d+)\s*B@:(\d+)", log)
                if temp_match:
                    data.nozzle_temp = float(temp_match.group(1))
                    data.nozzle_target = float(temp_match.group(2))
                    data.bed_temp = float(temp_match.group(3))
                    data.bed_target = float(temp_match.group(4))
                    data.nozzle_pwm = int(temp_match.group(5))
                    data.bed_pwm = int(temp_match.group(6))
                    data.nozzle_delta = data.nozzle_temp - data.nozzle_target if data.nozzle_temp is not None and data.nozzle_target is not None else None
                    data.bed_delta = data.bed_temp - data.bed_target if data.bed_temp is not None and data.bed_target is not None else None
                    logger.debug(f"Temperaturas atualizadas: Nozzle {data.nozzle_temp}/{data.nozzle_target}, Bed {data.bed_temp}/{data.bed_target}")

                pos_match = re.search(r"X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)\s+E:([-\d.]+)", log)
                if pos_match and control.m114_waiting:
                    data.x = float(pos_match.group(1))
                    data.y = float(pos_match.group(2))
                    data.z = float(pos_match.group(3))
                    data.extrusion_level = float(pos_match.group(4))
                    logger.info("M114 processado com sucesso: X=%s, Y=%s, Z=%s, E=%s", data.x, data.y, data.z, data.extrusion_level)
                    if is_printing:
                        timestamp = datetime.now()
                        save_data(timestamp, is_m114=True)
                    else:
                        logger.info("M114 recebido após fim da impressão, ignorado: %s", log)
                    control.m114_waiting = False

                accel_match = re.search(r"M204\s+(?:S([\d.]+)|P([\d.]+)\s+R([\d.]+)\s+T([\d.]+))", log)
                if accel_match and control.m503_waiting:
                    if accel_match.group(1):
                        data.accel_print = float(accel_match.group(1))
                        data.accel_retract = data.accel_print
                        data.accel_travel = data.accel_print
                    else:
                        data.accel_print = float(accel_match.group(2))
                        data.accel_retract = float(accel_match.group(3))
                        data.accel_travel = float(accel_match.group(4))
                    m204_received = True
                    logger.info("Aceleração: P=%s, R=%s, T=%s",
                                data.accel_print, data.accel_retract, data.accel_travel)

                jerk_match = re.search(r"M205.*X([\d.]+).*Y([\d.]+)", log)
                if jerk_match and control.m503_waiting:
                    data.jerk_x = float(jerk_match.group(1))
                    data.jerk_y = float(jerk_match.group(2))
                    m205_received = True
                    logger.info("Jerk: X=%s, Y=%s", data.jerk_x, data.jerk_y)

                if control.m503_waiting and m204_received and m205_received and is_printing:
                    timestamp = datetime.now()
                    save_data(timestamp, is_m114=False)
                    control.m503_waiting = False

    except json.JSONDecodeError as e:
        logger.error("Erro ao decodificar mensagem WebSocket: %s", e)
    except ValueError as e:
        logger.error("Erro ao processar mensagem: %s - Mensagem: %s", e, message)
    except Exception as e:
        logger.error("Erro inesperado: %s - Mensagem: %s", e, message)

def on_error(ws, error):
    logger.error("Erro no WebSocket: %s", error)

def on_close(ws, close_status_code, close_msg):
    logger.info("Conexão WebSocket fechada: %s", close_msg)
    control.websocket_active = False

def on_open(ws):
    logger.info("Conexão WebSocket aberta")
    ws.send(json.dumps({"auth": f"{USERNAME}:{control.session_key}"}))
    ws.send(json.dumps({"throttle": 0.5}))

def start_websocket():
    global ws
    ws_url = f"ws://{BASE_URL.split('http://')[1]}/sockjs/websocket"
    while True:
        try:
            ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message,
                                        on_error=on_error, on_close=on_close)
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            control.websocket_active = True
            time.sleep(2)  # Aguardar a conexão estabilizar
            return ws
        except Exception as e:
            logger.error("Erro ao iniciar WebSocket: %s", e)
            time.sleep(RETRY_WAIT)

def main():
    global ws
    while not login():
        logger.warning("Falha no login, esperando %ds antes de tentar novamente...", RETRY_WAIT)
        time.sleep(RETRY_WAIT)

    # Iniciar WebSocket inicialmente
    ws = start_websocket()

    last_check_time = 0
    last_m114_time = 0
    first_m114 = True
    first_m503 = True
    last_logged_state = None
    offline_check_timer = 0

    try:
        while True:
            current_time = time.time()
            check_interval = CHECK_INTERVAL

            # Se o OctoPrint estiver offline, reduzir a frequência de verificações
            if control.connection_failed_count >= 3:
                check_interval = OFFLINE_CHECK_INTERVAL
                offline_check_timer += 1
                if offline_check_timer * CHECK_INTERVAL >= OFFLINE_CHECK_INTERVAL:
                    logger.info("OctoPrint offline. Tentando reconectar...")
                    offline_check_timer = 0
                    login()  # Tentar reconectar

            if current_time - last_check_time >= check_interval:
                is_printing = check_printing_status()
                if is_printing and control.printerState != last_logged_state:
                    logger.info("Impressora está imprimindo! Estado: %s", control.printerState)
                    last_logged_state = control.printerState
                    if not control.m114_waiting and first_m114:
                        send_m114()
                        first_m114 = False
                        last_m114_time = current_time
                    if not control.m503_waiting and first_m503:
                        send_m503()
                        first_m503 = False
                elif not is_printing and control.printerState != last_logged_state:
                    logger.info("Impressora não está imprimindo. Estado: %s", control.printerState)
                    last_logged_state = control.printerState
                    control.m114_waiting = False
                    control.m503_waiting = False
                    first_m503 = True
                    first_m114 = True
                    control.filename_obtained = False

                    # Verificar inatividade e fechar WebSocket se necessário
                    if control.websocket_active and (current_time - control.last_active_time >= INACTIVITY_THRESHOLD):
                        logger.info("Impressora inativa por mais de 1 hora. Fechando WebSocket...")
                        ws.close()
                        control.websocket_active = False

                last_check_time = current_time

            if is_printing and control.websocket_active and not control.m114_waiting and (current_time - last_m114_time >= UPDATE_INTERVAL_M114):
                send_m114()
                last_m114_time = current_time

            if control.m114_waiting and control.m114_last_time and (current_time - control.m114_last_time > TIMEOUT_LIMIT) and is_printing:
                logger.warning("Timeout de %ds para M114. Reenviando... Mensagem anterior não processada.", TIMEOUT_LIMIT)
                send_m114()
                last_m114_time = current_time

            if control.m503_waiting and control.m503_last_time and first_m503 and (current_time - control.m503_last_time > TIMEOUT_LIMIT):
                logger.warning("Timeout de %ds para M503. Reenviando...", TIMEOUT_LIMIT)
                send_m503()

            if not control.filename_obtained:
                control.filename = get_current_filename_from_api()
                control.filename_obtained = True

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Programa encerrado pelo usuário.")
        if ws:
            ws.close()
    except Exception as e:
        logger.error("Erro no loop principal: %s", e)
        time.sleep(RETRY_WAIT)
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Programa encerrado pelo usuário.")

O que achas?
