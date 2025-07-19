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

def compute_features(samples, filename):
    """Calcula as features para o modelo a partir das amostras."""
    df = pd.DataFrame(samples)
    metrics = {}

    # Calcular métricas numéricas (alinhado com processed_z_lower_1.csv)
    metrics['Speed Factor'] = df['speed_factor'].mean() if df['speed_factor'].notna().any() else 0.0
    metrics['Média Delta temp_nozzle'] = df['temp_delta_nozzle'].mean() if df['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Desvio Padrão temp_nozzle'] = df['temp_delta_nozzle'].std() if df['temp_delta_nozzle'].notna().any() else 0.0
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

    # # Criar DataFrame com as colunas na ordem exata
    # features_df = pd.DataFrame([metrics])[FEATURE_COLUMNS]

    # Criar DataFrame com as colunas na ordem exata do treinamento
    features_df = pd.DataFrame([metrics], columns=[
        'Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle', 
        'Média PWM Extrusora', 'Média PWM Bed', 
        'Tempo Fora do Intervalo Extrusora (%)'
    ])

    # Verificar se as colunas correspondem
    if list(features_df.columns) != [
        'Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle', 
        'Média PWM Extrusora', 'Média PWM Bed', 
        'Tempo Fora do Intervalo Extrusora (%)'
    ]:
        raise ValueError("Feature columns mismatch")

    return features_df

@app.route('/predict', methods=['POST'])
def start():
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
        features_df = compute_features(df, filename)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
