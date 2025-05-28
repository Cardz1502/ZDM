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
BASE_URL = "http://192.168.250.100"
API_KEY = "Yfvanr37vlCxeQCFi8_pdyrz-GrqYFIYh2RpYKYtQ0I"
USERNAME = "rics"
PASSWORD = "ricsricsjabjab"
UPDATE_INTERVAL_M114 = 5
UPDATE_INTERVAL_M220 = 30
TIMEOUT_LIMIT = 90
CSV_FILE = "/app/data/printer_data2.csv"
LOG_FILE = "/app/data/octoprint_monitor2.log"
CHECK_INTERVAL = 5
CHECK_STATE_INTERVAL = 30
CHECK_WAIT_IMPRESSION_INTERVAL = 60
HTTP_TIMEOUT = 30

# Configurações de Retry
MAX_RETRIES = 5
RETRY_WAIT = 10

HEADERS = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

# Criar o diretório para logs e dados, se não existir
log_dir = "/app/data"
try:
    os.makedirs(log_dir, exist_ok=True)
except Exception as e:
    print(f"Erro ao criar diretório {log_dir}: {e}")
    exit(1)

# Configurar logging
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

class Control:
    def __init__(self):
        self.m114_waiting = False 
        self.m220_waiting = False
        self.m114_last_time = None
        self.m220_last_time = None
        self.session_key = None
        self.printer_state = None
        self.filename = None
        self.filename_obtained = False
        self.ws = None

data = PrinterData()
control = Control()

def login():
    url = f"{BASE_URL}/api/login"
    payload = {"user": USERNAME, "pass": PASSWORD, "remember": True}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            control.session_key = response.json().get("session")
            logger.info("Login bem-sucedido")
            return True
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro no login (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                logger.error("Falha ao fazer login após %d tentativas", MAX_RETRIES)
                return False

def check_printing_status():
    url = f"{BASE_URL}/api/job"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            job_data = response.json()
            state = job_data["state"]
            control.printer_state = state
            return state
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao verificar estado da impressora (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                control.printer_state = "Unknown"
                return "Unknown"

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
            logger.info("Nome do arquivo obtido: %s", filename)
            return filename
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao obter nome do arquivo (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                return "(no file)"

def send_m114():
    url = f"{BASE_URL}/api/printer/command"
    payload = {"command": "M114"}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            logger.info("Comando M114 enviado")
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

def send_m220():
    url = f"{BASE_URL}/api/printer/command"
    payload = {"command": "M220"}
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, json=payload, headers=HEADERS, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            logger.info("Comando M220 enviado")
            control.m220_waiting = True
            control.m220_last_time = time.time()
            return
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error("Erro ao enviar M220 (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                control.m220_waiting = False
                control.m220_last_time = None

def save_data(timestamp, is_m114=True):
    allowed_filenames = {"zdm4ms~4", "zd5b20~1", "zd2c72~1"}
    
    if control.filename not in allowed_filenames:
        logger.info("Nome de ficheiro %s não está na lista permitida. Dados não salvos", control.filename)
        return

    try:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "temp_nozzle", "temp_target_nozzle", "temp_delta_nozzle",
                                 "pwm_nozzle", "temp_bed", "temp_target_bed", "temp_delta_bed", "pwm_bed",
                                 "X", "Y", "Z", "E", "speed_factor", "filename"])

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if is_m114:
            row = [timestamp_str, data.nozzle_temp, data.nozzle_target, data.nozzle_delta,
                   data.nozzle_pwm, data.bed_temp, data.bed_target, data.bed_delta, data.bed_pwm,
                   data.x, data.y, data.z, data.extrusion_level, data.speed_factor, control.filename]
            # Usar valores padrão se algum dado for None
            nozzle_temp = data.nozzle_temp if data.nozzle_temp is not None else 0.0
            nozzle_target = data.nozzle_target if data.nozzle_target is not None else 0.0
            bed_temp = data.bed_temp if data.bed_temp is not None else 0.0
            bed_target = data.bed_target if data.bed_target is not None else 0.0
            nozzle_pwm = data.nozzle_pwm if data.nozzle_pwm is not None else 0
            bed_pwm = data.bed_pwm if data.bed_pwm is not None else 0
            x = data.x if data.x is not None else 0.0
            y = data.y if data.y is not None else 0.0
            z = data.z if data.z is not None else 0.0
            extrusion_level = data.extrusion_level if data.extrusion_level is not None else 0.0
            speed_factor = data.speed_factor if data.speed_factor is not None else 0.0
            logger.info("Dados M114 salvos: %s, X=%.2f, Y=%.2f, Z=%.2f, E=%.2f, SpeedFactor=%.0f%%, Nozzle=%.2f/%.2f, Bed=%.2f/%.2f, PWM(Nozzle:Bed)=(%d:%d), Filename=%s",
                        timestamp_str, x, y, z, extrusion_level, speed_factor,
                        nozzle_temp, nozzle_target, bed_temp, bed_target, nozzle_pwm, bed_pwm, control.filename)
        else:
            row = [timestamp_str, data.nozzle_temp, data.nozzle_target, data.nozzle_delta,
                   data.nozzle_pwm, data.bed_temp, data.bed_target, data.bed_delta, data.bed_pwm,
                   None, None, None, None, data.speed_factor, control.filename]
            # Usar valores padrão se algum dado for None
            nozzle_temp = data.nozzle_temp if data.nozzle_temp is not None else 0.0
            nozzle_target = data.nozzle_target if data.nozzle_target is not None else 0.0
            bed_temp = data.bed_temp if data.bed_temp is not None else 0.0
            bed_target = data.bed_target if data.bed_target is not None else 0.0
            nozzle_pwm = data.nozzle_pwm if data.nozzle_pwm is not None else 0
            bed_pwm = data.bed_pwm if data.bed_pwm is not None else 0
            speed_factor = data.speed_factor if data.speed_factor is not None else 0.0
            logger.info("Dados M220 salvos: %s, SpeedFactor=%.0f%%, Nozzle=%.2f/%.2f, Bed=%.2f/%.2f, PWM(Nozzle:Bed)=(%d:%d), Filename=%s",
                        timestamp_str, speed_factor, nozzle_temp, nozzle_target, bed_temp, bed_target, nozzle_pwm, bed_pwm, control.filename)

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row)
    except Exception as e:
        logger.error("Erro ao salvar dados no CSV %s: %s", CSV_FILE, e)

def on_message(ws, message):
    try:
        logger.debug("Mensagem WebSocket recebida: %s", message)
        message_data = json.loads(message)
        if "connected" in message_data:
            logger.info("Conexão WebSocket confirmada")
            return

        if "current" in message_data:
            current = message_data["current"]
            logs = current.get("logs", [])
            logger.debug("Logs recebidos: %s", logs)

            for log in logs:
                logger.debug("Processando log: %s", log)

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

                pos_match = re.search(r"X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)\s+E:([-\d.]+)", log)
                if pos_match and control.m114_waiting:
                    data.x = float(pos_match.group(1))
                    data.y = float(pos_match.group(2))
                    data.z = float(pos_match.group(3))
                    data.extrusion_level = float(pos_match.group(4))
                    # Verificar se os valores de temperatura estão disponíveis e não são 0
                    nozzle_target = data.nozzle_target if data.nozzle_target is not None else 0.0
                    bed_target = data.bed_target if data.bed_target is not None else 0.0
                    if nozzle_target != 0 and bed_target != 0:
                        timestamp = datetime.now()
                        save_data(timestamp, is_m114=True)
                    else:
                        logger.info("M114 ignorado após fim da impressão: X=%.2f, Y=%.2f, Z=%.2f, E=%.2f", data.x, data.y, data.z, data.extrusion_level)
                    control.m114_waiting = False

                speed_match = re.search(r"FR:([\d.]+)%", log)
                if speed_match and control.m220_waiting:
                    data.speed_factor = float(speed_match.group(1))
                    # Verificar se os valores de temperatura estão disponíveis e não são 0
                    nozzle_target = data.nozzle_target if data.nozzle_target is not None else 0.0
                    bed_target = data.bed_target if data.bed_target is not None else 0.0
                    if nozzle_target != 0 and bed_target != 0:
                        timestamp = datetime.now()
                        save_data(timestamp, is_m114=False)
                    else:
                        logger.info("M220 ignorado após fim da impressão: SpeedFactor=%.0f%%", data.speed_factor)
                    control.m220_waiting = False

    except json.JSONDecodeError as e:
        logger.error("Erro ao decodificar mensagem WebSocket: %s", e)
    except ValueError as e:
        logger.error("Erro ao processar mensagem: %s", e)
    except Exception as e:
        logger.error("Erro inesperado: %s", e)

def on_error(ws, error):
    logger.error("Erro no WebSocket: %s", error)

def on_close(ws, close_status_code, close_msg):
    logger.info("Conexão WebSocket fechada. Tentando reconectar...")
    control.ws = None
    time.sleep(RETRY_WAIT)
    control.ws = start_websocket()

def on_open(ws):
    logger.info("Conexão WebSocket aberta")
    ws.send(json.dumps({"auth": f"{USERNAME}:{control.session_key}"}))

def start_websocket():
    ws_url = f"ws://{BASE_URL.split('http://')[1]}/sockjs/websocket"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message,
                                        on_error=on_error, on_close=on_close)
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            logger.info("Conexão WebSocket iniciada")
            return ws
        except Exception as e:
            retries += 1
            logger.error("Erro ao iniciar WebSocket (tentativa %d/%d): %s", retries, MAX_RETRIES, e)
            if retries < MAX_RETRIES:
                time.sleep(RETRY_WAIT)
            else:
                logger.error("Falha ao iniciar WebSocket após %d tentativas", MAX_RETRIES)
                return None

def main():
    while not login():
        logger.warning("Falha no login, esperando %ds antes de tentar novamente", RETRY_WAIT)
        time.sleep(RETRY_WAIT)

    # Abrir a conexão WebSocket logo no início e mantê-la aberta
    control.ws = start_websocket()
    time.sleep(2)  # Aguardar a conexão WebSocket ser estabelecida

    last_check_time = 0
    last_check_time_state = 0
    last_m114_time = 0
    last_m220_time = 0
    first_m114 = True
    first_m220 = True
    was_printing = False
    last_wait_impression = 0

    try:
        while True:
            current_time = time.time()
            logger.debug("Loop principal rodando, current_time: %s", datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S"))

            if current_time - last_check_time >= CHECK_INTERVAL:
                try:
                    state = check_printing_status()
                    if current_time - last_check_time_state >= CHECK_STATE_INTERVAL:
                        logger.info("Estado da impressora verificado: %s", state)
                        last_check_time_state = current_time
                    is_printing = state in ["Printing from SD", "Starting print from SD"]
                    is_operational = state == "Operational"

                    if is_operational and not was_printing:
                        if current_time - last_wait_impression >= CHECK_WAIT_IMPRESSION_INTERVAL:
                            logger.info("Impressora em estado Operational, aguardando impressão")
                            last_wait_impression = current_time

                    if is_printing and not was_printing:
                        logger.info("Impressora iniciando impressão: %s", state)
                        control.filename = get_current_filename_from_api()
                        control.filename_obtained = True
                        first_m114 = True
                        first_m220 = True

                    if not is_printing and was_printing and is_operational:
                        logger.info("Impressora voltou ao estado Operational após impressão")
                        control.m114_waiting = False
                        control.m220_waiting = False
                        first_m220 = True
                        first_m114 = True
                        control.filename_obtained = False

                    allowed_filenames = {"zdm4ms~4", "zd5b20~1", "zd2c72~1"}
                    filename_allowed = control.filename in allowed_filenames

                    if is_printing and filename_allowed:
                        if not control.m114_waiting and first_m114:
                            send_m114()
                            first_m114 = False
                            last_m114_time = current_time
                        if not control.m220_waiting and first_m220:
                            send_m220()
                            first_m220 = False
                            last_m220_time = current_time

                    was_printing = is_printing
                    last_check_time = current_time
                except Exception as e:
                    logger.error("Erro ao verificar estado da impressora: %s", e)
                    time.sleep(RETRY_WAIT)
                    continue

            allowed_filenames = {"zdm4ms~4", "zd5b20~1", "zd2c72~1"}
            filename_allowed = control.filename in allowed_filenames

            if was_printing and filename_allowed and not control.m114_waiting and (current_time - last_m114_time >= UPDATE_INTERVAL_M114):
                send_m114()
                last_m114_time = current_time

            if was_printing and filename_allowed and not control.m220_waiting and (current_time - last_m220_time >= UPDATE_INTERVAL_M220):
                send_m220()
                last_m220_time = current_time

            if control.m114_waiting and control.m114_last_time and (current_time - control.m114_last_time > TIMEOUT_LIMIT) and was_printing:
                logger.warning("Timeout de %ds para M114. Reenviando", TIMEOUT_LIMIT)
                send_m114()
                last_m114_time = current_time

            if control.m220_waiting and control.m220_last_time and (current_time - control.m220_last_time > TIMEOUT_LIMIT) and was_printing:
                logger.warning("Timeout de %ds para M220. Reenviando", TIMEOUT_LIMIT)
                send_m220()
                last_m220_time = current_time

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Programa encerrado pelo usuário")
        if control.ws is not None:
            control.ws.close()
    except Exception as e:
        logger.error("Erro no loop principal: %s", e)
        time.sleep(RETRY_WAIT)
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Programa encerrado pelo usuário")