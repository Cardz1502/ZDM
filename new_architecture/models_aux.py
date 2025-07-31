# -*- coding: utf-8 -*-
# models_aux.py
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime
import requests

API_KEY = "-cqzgIHdAaLvW-9EbK6dXW5019dvLPgNyxP7tEwscFw"
MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware

app = Flask(__name__)

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

FEATURE_COLUMNS_Z4 = [
    'Speed Factor', 'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle',
    'Média Delta Mesa (°C)', 'Tempo Fora do Intervalo Extrusora (%)',
    'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)',
    'Variação X', 'Variação Y', 'Variação Z', 'X_max', 'X_min',
    'Y_max', 'Y_min', 'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
    'Média PWM Bed', 'Desvio Padrão PWM Bed'
]

def compute_features(samples, mode):
    df = pd.DataFrame(samples)
    metrics = {}

    #metricas de z=1
    metrics['Desvio Padrão temp_nozzle'] = df['temp_delta_nozzle'].std() if df['temp_delta_nozzle'].notna().any() else 0.0  ## z=1
    metrics['Máximo Delta temp_nozzle'] = df['temp_delta_nozzle'].max() if df['temp_delta_nozzle'].notna().any() else 0.0 ## z=1
    metrics['Tempo Fora do Intervalo Extrusora (%)'] = calculate_t_out_of_range(df, threshold=2.0) ## z=1
    metrics['Média PWM Extrusora'] = df['pwm_nozzle'].mean() if df['pwm_nozzle'].notna().any() else 0.0 ## z=1
    metrics['Média PWM Bed'] = df['pwm_bed'].mean() if df['pwm_bed'].notna().any() else 0.0 ## z=1

    #metricas para z=4
    metrics['Speed Factor'] = df['speed_factor'].mean() if df['speed_factor'].notna().any() else 0.0
    metrics['Média Delta temp_nozzle'] = df['temp_delta_nozzle'].mean() if df['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Média Delta Mesa (°C)'] = df['temp_delta_bed'].mean() if df['temp_delta_bed'].notna().any() else 0.0

    if df['E'].notna().any() and len(df) > 1:
        e_initial = df['E'].iloc[0]
        e_final = df['E'].iloc[-1]
        time_initial = df['timestamp'].iloc[0] if pd.notna(df['timestamp'].iloc[0]) else None
        time_final = df['timestamp'].iloc[-1] if pd.notna(df['timestamp'].iloc[-1]) else None
        if time_initial and time_final:
            time_diff_minutes = (time_final - time_initial).total_seconds() / 60
            metrics['Taxa de Extrusão (mm/min)'] = (e_final - e_initial) / time_diff_minutes if time_diff_minutes > 0 else 0.0
        else:
            metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = calculate_e_active_time(df)
    else:
        metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = 0.0

    # ADD missing features from old service
    metrics['Variação X'] = df['X'].std() if df['X'].notna().any() else 0.0
    metrics['Variação Y'] = df['Y'].std() if df['Y'].notna().any() else 0.0
    metrics['Variação Z'] = df['Z'].std() if df['Z'].notna().any() else 0.0
    metrics['X_max'] = df['X'].max() if df['X'].notna().any() else 0.0
    metrics['X_min'] = df['X'].min() if df['X'].notna().any() else 0.0
    metrics['Y_max'] = df['Y'].max() if df['Y'].notna().any() else 0.0
    metrics['Y_min'] = df['Y'].min() if df['Y'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Extrusora'] = df['pwm_nozzle'].std() if df['pwm_nozzle'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Bed'] = df['pwm_bed'].std() if df['pwm_bed'].notna().any() else 0.0

    # Seleciona colunas
    if mode == 'z1':
        selected_columns = [
            'Máximo Delta temp_nozzle',
            'Desvio Padrão temp_nozzle',
            'Média PWM Extrusora',
            'Média PWM Bed',
            'Tempo Fora do Intervalo Extrusora (%)'
        ]
    else:  # z4
        selected_columns = FEATURE_COLUMNS_Z4

    return pd.DataFrame([metrics], columns=selected_columns)


@app.route('/predict1', methods=['POST'])
def start1():
    try:
        data = request.get_json()
        print("[INFO] Dados recebidos com sucesso.")

        # Verificar se é uma lista de amostras
        if not isinstance(data, list):
            return jsonify({"error": "Esperado uma lista de amostras JSON"}), 400

        # Converter para DataFrame
        df = pd.DataFrame(data)

        # Garantir que timestamp está no formato datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        filename = df['filename'].iloc[0] if 'filename' in df.columns else "unknown"

        # Mapear filename para tipo de peça (para log)
        if filename.lower() == 'zdm4ms~4':
            piece_type = 'QUADRADO'
        elif filename.lower() == 'zd5b20~1':
            piece_type = 'L'
        elif filename.lower() == 'zd2c72~1':
            piece_type = 'RETANGULO'
        else:
            print(f"Tipo de peça inválido: {filename}")
            return jsonify({"error": "Invalid piece type"}), 400

        # Calcular features
        features_df = compute_features(df, mode='z1')
        print("[INFO] Features calculadas com sucesso.")    
        print("[INFO] Features:\n", features_df.to_string(index=False))


        # Carregar modelo, scaler e label encoder
        try:
            model = joblib.load("models/svm_ok_nokv2.joblib")
            scaler = joblib.load("models/scalerv2.joblib")
            label_encoder = joblib.load("models/label_encoderv2.joblib")
        except FileNotFoundError:
            print("Erro ao carregar modelo, scaler ou LabelEncoder")
            return jsonify({"error": "Failed to load model, scaler, or LabelEncoder"}), 500

        # Normalizar os dados
        features_scaled = scaler.transform(features_df)

        # Fazer predição
        prediction = model.predict(features_scaled)[0]
        prediction_label = label_encoder.inverse_transform([prediction])[0]

        print(f"[PREVISÃO] Peça: {piece_type} => Resultado: {prediction_label}")

        return jsonify({
            "piece_type": piece_type,
            "prediction": prediction_label
        }), 200



    except Exception as e:
        print(f"[ERRO] {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/predict4', methods=['POST'])
def start4():
    try:
        data = request.get_json()
        print("[INFO] Dados recebidos com sucesso.")

        # Verificar se é uma lista de amostras
        if not isinstance(data, list):
            return jsonify({"error": "Esperado uma lista de amostras JSON"}), 400

        # Converter para DataFrame
        df = pd.DataFrame(data)

        # Garantir que timestamp está no formato datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        filename = df['filename'].iloc[0] if 'filename' in df.columns else "unknown"

        # Mapear filename para tipo de peça (para log)
        if filename.lower() == 'zdm4ms~4':
            piece_type = 'QUADRADO'
        elif filename.lower() == 'zd5b20~1':
            piece_type = 'L'
        elif filename.lower() == 'zd2c72~1':
            piece_type = 'RETANGULO'
        else:
            print(f"Tipo de peça inválido: {filename}")
            return jsonify({"error": "Invalid piece type"}), 400

        # Calcular features
        features_df = compute_features(df, mode='z4')
        print("[INFO] Features calculadas com sucesso.")    
        print("[INFO] Features:\n", features_df.to_string(index=False))


        # Carregar modelo e scaler
        try:
            model = joblib.load(f"models/model_{piece_type.lower()}.joblib")
            scaler = joblib.load(f"models/scaler_{piece_type.lower()}.joblib")
        except FileNotFoundError:
            return jsonify({"error": f"Failed to load model or scaler for {piece_type}"}), 400

        # Fazer previsão
        X_scaled = scaler.transform(features_df)
        predictions = model.predict(X_scaled)[0]

        # Formatar mensagem de log com dimensões previstas
        if piece_type in ['QUADRADO', 'RETANGULO']:
            log_message = (
                f"Previsão para {piece_type}: "
                f"Comprimento={predictions[0]:.1f}mm, "
                f"Largura={predictions[1]:.1f}mm, "
                f"Altura={predictions[2]:.1f}mm"
            )
        elif piece_type == 'L':
            log_message = (
                f"Previsão para {piece_type}: "
                f"Comprimento Externo={predictions[0]:.1f}mm, "
                f"Largura Externa={predictions[1]:1f}mm, "
                f"Comprimento Interno 1={predictions[2]:.1f}mm, "
                f"Comprimento Interno 2={predictions[3]:.1f}mm, "
                f"Largura Interna 1={predictions[4]:.1f}mm, "
                f"Largura Interna 2={predictions[5]:.1f}mm, "
                f"Altura={predictions[6]:.1f}mm"
            )

        print(log_message)

        return jsonify({
                "piece_type": piece_type,
                "predictions": predictions.tolist(),
            }), 200

    except Exception as e:
        print(f"[ERRO] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
