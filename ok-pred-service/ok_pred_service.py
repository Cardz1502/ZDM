# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/data/prediction_service_ok_nok.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CSV_FILE = "/app/data/printer_dataZDM.csv"
FEATURE_COLUMNS = [
    'Speed Factor', 'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle',
    'Média Delta Mesa (°C)', 'Tempo Fora do Intervalo Extrusora (%)',
    'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)',
    'Variação Y', 'Variação Z', 'X_max', 'Y_max', 'Y_min',
    'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
    'Média PWM Bed', 'Desvio Padrão PWM Bed'
]

def calculate_t_out_of_range(df, threshold=2.0):
    """Calcula o percentual de tempo com temperatura fora do intervalo."""
    out_of_range = df['temp_delta_nozzle'].abs() > threshold
    if len(df) == 0:
        return 0.0
    return (out_of_range.sum() / len(df)) * 100

def calculate_e_active_time(df):
    """Calcula o percentual de tempo com extrusão ativa."""
    if len(df) <= 1:
        return 0.0
    e_changes = (df['E'].diff() != 0) & (df['E'].notna())
    active_intervals = e_changes.sum()
    total_intervals = len(df) - 1
    if total_intervals == 0:
        return 0.0
    return (active_intervals / total_intervals) * 100

def compute_features(samples, filename):
    """Calcula as features para o modelo a partir das amostras."""
    df = pd.DataFrame(samples)
    metrics = {}

    # Calcular métricas numéricas (alinhado com processed_z_lower_1.csv)
    metrics['Speed Factor'] = df['speed_factor'].mean() if df['speed_factor'].notna().any() else 0.0
    metrics['Média Delta temp_nozzle'] = df['temp_delta_nozzle'].mean() if df['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Máximo Delta temp_nozzle'] = df['temp_delta_nozzle'].max() if df['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Média Delta Mesa (°C)'] = df['temp_delta_bed'].mean() if df['temp_delta_bed'].notna().any() else 0.0
    metrics['Tempo Fora do Intervalo Extrusora (%)'] = calculate_t_out_of_range(df, threshold=2.0)
    
    if df['E'].notna().any() and len(df) > 1:
        e_initial = df['E'].iloc[0]
        e_final = df['E'].iloc[-1]
        time_initial = df['timestamp'].iloc[0] if pd.notna(df['timestamp'].iloc[0]) else None
        time_final = df['timestamp'].iloc[-1] if pd.notna(df['timestamp'].iloc[-1]) else None
        if time_initial is not None and time_final is not None:
            time_diff_minutes = (time_final - time_initial).total_seconds() / 60
            if time_diff_minutes > 0:
                metrics['Taxa de Extrusão (mm/min)'] = (e_final - e_initial) / time_diff_minutes
            else:
                metrics['Taxa de Extrusão (mm/min)'] = 0.0
        else:
            metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = calculate_e_active_time(df)
    else:
        metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = 0.0

    metrics['Variação Y'] = (df['Y'].max() - df['Y'].min()) if df['Y'].notna().any() else 0.0
    metrics['Variação Z'] = (df['Z'].max() - df['Z'].min()) if df['Z'].notna().any() else 0.0
    metrics['X_max'] = df['X'].max() if df['X'].notna().any() else 0.0
    metrics['Y_max'] = df['Y'].max() if df['Y'].notna().any() else 0.0
    metrics['Y_min'] = df['Y'].min() if df['Y'].notna().any() else 0.0
    metrics['Média PWM Extrusora'] = df['pwm_nozzle'].mean() if df['pwm_nozzle'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Extrusora'] = df['pwm_nozzle'].std() if df['pwm_nozzle'].notna().any() else 0.0
    metrics['Média PWM Bed'] = df['pwm_bed'].mean() if df['pwm_bed'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Bed'] = df['pwm_bed'].std() if df['pwm_bed'].notna().any() else 0.0

    # Criar DataFrame com as colunas na ordem exata
    features_df = pd.DataFrame([metrics])[FEATURE_COLUMNS]

    # Verificar se todas as colunas esperadas estão presentes
    if list(features_df.columns) != FEATURE_COLUMNS:
        logger.error(f"Colunas geradas não correspondem às esperadas: {list(features_df.columns)}")
        raise ValueError("Feature columns mismatch")

    return features_df

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint para previsão de OK/NOK."""
    try:
        data = request.get_json()
        start_time = data.get('start_time')
        filename = data.get('filename')
        
        if not start_time:
            logger.error("Start time não fornecido")
            return jsonify({"error": "Start time required"}), 400

        if not filename:
            logger.error("Filename não fornecido")
            return jsonify({"error": "Filename required"}), 400

        # Mapear filename para tipo de peça (para log)
        if filename == 'zdm4ms~4':
            piece_type = 'QUADRADO'
        elif filename == 'zd5b20~1':
            piece_type = 'L'
        elif filename == 'zd2c72~1':
            piece_type = 'RETANGULO'
        else:
            logger.error(f"Tipo de peça inválido: {filename}")
            return jsonify({"error": "Invalid piece type"}), 400

        # Carregar dados do CSV
        try:
            df = pd.read_csv(CSV_FILE, encoding='latin-1', sep=',', on_bad_lines='warn')
        except FileNotFoundError:
            logger.error(f"Arquivo CSV {CSV_FILE} não encontrado")
            return jsonify({"error": "CSV file not found"}), 500
        except UnicodeDecodeError:
            logger.error(f"Erro de codificação ao ler {CSV_FILE}")
            return jsonify({"error": "Encoding error reading CSV file"}), 500

        # Filtrar dados da impressão atual
        try:
            start_time = pd.to_datetime(start_time, format='%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Erro ao converter start_time: {str(e)}")
            return jsonify({"error": "Invalid start_time format"}), 400

        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
        df_filtered = df[
            (df['timestamp'] >= start_time) &
            (df['filename'] == filename)
        ]

        if df_filtered.empty:
            logger.error(f"Nenhum dado encontrado para {piece_type} a partir de {start_time} com filename {filename}")
            return jsonify({"error": "No data found for the given parameters"}), 400

        # Calcular features
        logger.info(f"Calculando features para {piece_type}...")
        features_df = compute_features(df_filtered, filename)
        logger.info(f"Features calculadas: {features_df.columns.tolist()}")

        # Carregar modelo, scaler e LabelEncoder
        try:
            model = joblib.load("app/models/random_forest_ok_nok.joblib")
            scaler = joblib.load("app/models/scaler.joblib")
            label_encoder = joblib.load("app/models/label_encoder.joblib")
        except FileNotFoundError:
            logger.error("Erro ao carregar modelo, scaler ou LabelEncoder")
            return jsonify({"error": "Failed to load model, scaler, or LabelEncoder"}), 500

        # Normalizar os dados
        features_df_scaled = scaler.transform(features_df)

        # Fazer previsão
        logger.info("Fazendo previsão...")
        prediction = model.predict(features_df_scaled)[0]
        prediction_label = label_encoder.inverse_transform([prediction])[0]

        # Log da previsão
        logger.info(f"Previsão para {piece_type}: Resultado={prediction_label}")

        # Formatar resposta
        response = {
            "piece_type": piece_type,
            "prediction": prediction_label
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Erro ao processar previsão: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)