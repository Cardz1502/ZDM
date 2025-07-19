import requests
import datetime

from monitor_aux import AAS_URL

MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware

def send_to_aas(destination, msg):
    payload = {
        "destination": destination,
        "msg": msg,
    }

    print(f"[INFO] Enviando DADOS da aas para middleware: {msg}")

    try:
        response = requests.post(f"{MIDDLEWARE_URL}:1880/aas/append", json=payload, timeout=10)
        response.raise_for_status()
        print(f"[SUCESSO] Resposta: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar dados: {e}")

if __name__ == '__main__':
    data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temp_nozzle": 2020.5,
        "temp_target_nozzle": 210.0,
        "temp_delta_nozzle": -9.5,
        "pwm_nozzle": 255,
        "temp_bed": 60.0,
        "temp_target_bed": 60.0,
        "temp_delta_bed": 0.0,
        "pwm_bed": 128,
        "x": 2020.0,
        "y": 120.0,
        "z": 0.2,
        "e": 12.3,
        "speed_factor": 100,
        "filename": "example.gcode",
    }

    send_to_aas(AAS_URL, data)
