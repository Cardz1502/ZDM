import pandas as pd
import numpy as np
from datetime import datetime

# Função para calcular o percentual de tempo com temperatura fora do intervalo
def calculate_t_out_of_range(group, threshold=2.0):
    out_of_range = group['temp_delta_nozzle'].abs() > threshold
    if len(group) == 0:
        return 0.0
    return (out_of_range.sum() / len(group)) * 100  # Percentual

# Função para calcular o percentual de tempo com extrusão ativa
def calculate_e_active_time(group):
    if len(group) <= 1:
        return 0.0
    e_changes = (group['E'].diff() != 0) & (group['E'].notna())
    active_intervals = e_changes.sum()
    total_intervals = len(group) - 1
    if total_intervals == 0:
        return 0.0
    return (active_intervals / total_intervals) * 100  # Percentual

# Função para calcular métricas de uma peça
def compute_features(group):
    metrics = {}
    
    # Métricas mantidas
    metrics['Speed Factor'] = group['speed_factor'].mean() if group['speed_factor'].notna().any() else 0.0
    metrics['Média Delta temp_nozzle'] = group['temp_delta_nozzle'].mean() if group['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Máximo Delta temp_nozzle'] = group['temp_delta_nozzle'].max() if group['temp_delta_nozzle'].notna().any() else 0.0
    metrics['Média Delta Mesa (°C)'] = group['temp_delta_bed'].mean() if group['temp_delta_bed'].notna().any() else 0.0
    metrics['Tempo Fora do Intervalo Extrusora (%)'] = calculate_t_out_of_range(group, threshold=2.0)
    
    if group['E'].notna().any() and len(group) > 1:
        e_initial = group['E'].iloc[0]
        e_final = group['E'].iloc[-1]
        time_initial = group['timestamp'].iloc[0] if pd.notna(group['timestamp'].iloc[0]) else None
        time_final = group['timestamp'].iloc[-1] if pd.notna(group['timestamp'].iloc[-1]) else None
        if time_initial is not None and time_final is not None:
            time_diff_minutes = (time_final - time_initial).total_seconds() / 60
            if time_diff_minutes > 0:
                metrics['Taxa de Extrusão (mm/min)'] = (e_final - e_initial) / time_diff_minutes
            else:
                metrics['Taxa de Extrusão (mm/min)'] = 0.0
        else:
            metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = calculate_e_active_time(group)
    else:
        metrics['Taxa de Extrusão (mm/min)'] = 0.0
        metrics['Tempo Ativo de Extrusão (%)'] = 0.0

    metrics['Variação X'] = (group['X'].max() - group['X'].min()) if group['X'].notna().any() else 0.0
    metrics['Variação Z'] = (group['Z'].max() - group['Z'].min()) if group['Z'].notna().any() else 0.0
    metrics['X_min'] = group['X'].min() if group['X'].notna().any() else 0.0
    metrics['Média PWM Extrusora'] = group['pwm_nozzle'].mean() if group['pwm_nozzle'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Extrusora'] = group['pwm_nozzle'].std() if group['pwm_nozzle'].notna().any() else 0.0
    metrics['Média PWM Bed'] = group['pwm_bed'].mean() if group['pwm_bed'].notna().any() else 0.0
    metrics['Desvio Padrão PWM Bed'] = group['pwm_bed'].std() if group['pwm_bed'].notna().any() else 0.0

    # Nova métrica
    metrics['Taxa Variação temp_nozzle'] = group['temp_delta_nozzle'].diff().abs().mean() if group['temp_delta_nozzle'].notna().any() else 0.0

    return metrics

# Função principal para processar o CSV
def process_printer_data(input_file, output_file):
    print(f"Lendo o {input_file}...")
    try:
        df = pd.read_csv(input_file, encoding='latin-1', sep=',', index_col=False, on_bad_lines='warn')
        print("Arquivo lido com separador vírgula (,).")
    except (pd.errors.ParserError, ValueError) as e:
        print(f"Erro ao ler com separador vírgula: {e}")
        return

    if df.empty:
        print(f"Erro: O arquivo {input_file} está vazio. Não há dados para processar.")
        return

    print(f"Colunas disponíveis no {input_file}:")
    print(list(df.columns))

    # Verificar se as colunas esperadas estão presentes
    expected_columns = [
        'timestamp', 'temp_nozzle', 'temp_target_nozzle', 'temp_delta_nozzle', 
        'pwm_nozzle', 'temp_bed', 'temp_target_bed', 'temp_delta_bed', 'pwm_bed',
        'X', 'Y', 'Z', 'E', 'speed_factor', 'filename'
    ]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"Erro: As seguintes colunas esperadas não foram encontradas: {missing_columns}")
        print("Colunas encontradas:", list(df.columns))
        print(f"Verifique o formato do arquivo {input_file}.")
        return

    date_column = 'timestamp'
    print(f"Coluna de data encontrada: {date_column}")

    # Verificar os primeiros valores da coluna timestamp
    print("Primeiros 5 valores da coluna 'timestamp':")
    print(df[date_column].head())

    # Converter a coluna de data para datetime
    try:
        df['timestamp'] = pd.to_datetime(df[date_column], format='%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter a coluna 'timestamp' para datetime: {e}")
        print("Valores da coluna 'timestamp':")
        print(df[date_column].head())
        return

    # Identificar impressões com base em gaps de 5 minutos ou mais
    df = df.sort_values('timestamp')  # Garantir que os dados estão ordenados por timestamp
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 60  # Diferença em minutos
    df['print_group'] = (df['time_diff'] >= 5).cumsum()  # Novo grupo para gaps >= 5 minutos

    # Ler o processed_z_lower_1.csv para obter impressões já processadas
    processed_timestamps = set()
    try:
        processed_df = pd.read_csv(output_file, encoding='utf-8')
        if not processed_df.empty:
            processed_timestamps = set(processed_df['Data'].str.split('/').str[0])
            last_id = max(processed_df['id_peça']) if not processed_df['id_peça'].empty else 0
        else:
            last_id = 0
    except FileNotFoundError:
        last_id = 0

    # Agrupar os dados por print_group
    grouped = df.groupby('print_group')
    all_prints = sorted(grouped.groups.keys())

    # Filtrar apenas as impressões não processadas
    prints_to_process = []
    for print_group in all_prints:
        group = grouped.get_group(print_group)
        start_time = group['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
        if start_time not in processed_timestamps:
            prints_to_process.append(print_group)

    if not prints_to_process:
        print(f"Não há novas impressões para processar no {input_file}.")
        return

    print(f"Processando {len(prints_to_process)} novas impressões do {input_file}...")
    processed_data = []
    piece_id = last_id + 1

    for print_group in prints_to_process:
        group = grouped.get_group(print_group)
        metrics = compute_features(group)
        metrics['id_peça'] = piece_id

        # Adicionar a data da impressão
        start_time = group['timestamp'].iloc[0]
        end_time = group['timestamp'].iloc[-1]
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_time.strftime('%H:%M:%S')
        metrics['Data'] = f"{start_str}/{end_str}"

        # Extrair o valor único de filename do grupo
        if group['filename'].notna().any():
            filename = group['filename'].dropna().iloc[0]
            print(f"Filename encontrado: {filename}")
            if filename == 'zdm4ms~4':
                metrics['Tipo de Peça'] = 'QUADRADO'
            elif filename == 'zd5b20~1':
                metrics['Tipo de Peça'] = 'L'
            elif filename == 'zd2c72~1':
                metrics['Tipo de Peça'] = 'RETANGULO'
            else:
                print(f"Erro: Tipo de peça desconhecido para filename '{filename}'.")
                return
        else:
            print("Erro: Coluna 'filename' contém apenas valores nulos.")
            return

        # Solicitar o Resultado da impressão
        print(f"\nPeça {piece_id} (Timestamp Inicial: {start_str}, Timestamp Final: {end_str}, Tipo: {metrics['Tipo de Peça']})")
        while True:
            result = input(f"Peça {piece_id} - Resultado da impressão (OK/NOK): ").strip().upper()
            if result in ['OK', 'NOK']:
                metrics['Resultado'] = result
                break
            print("Por favor, insira 'OK' ou 'NOK'.")

        processed_data.append(metrics)
        piece_id += 1

    if not processed_data:
        print("Nenhum dado novo para adicionar.")
        return

    # Criar o DataFrame com os novos dados processados
    new_processed_df = pd.DataFrame(processed_data)

    # Reordenar colunas
    columns = [
        'Tipo de Peça', 'id_peça', 'Data', 'Speed Factor',
        'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 'Média Delta Mesa (°C)', 
        'Tempo Fora do Intervalo Extrusora (%)', 'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)',
        'Variação X', 'Variação Z', 'X_min',
        'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora', 'Média PWM Bed', 'Desvio Padrão PWM Bed',
        'Taxa Variação temp_nozzle', 'Resultado'
    ]
    new_processed_df = new_processed_df[columns]

    # Salvar os novos dados
    print(f"\nAdicionando os dados processados em {output_file}...")
    if last_id == 0:
        new_processed_df.to_csv(output_file, index=False, encoding='utf-8')
    else:
        new_processed_df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8')
    print("Processamento concluído!")

# Executar o script
if __name__ == "__main__":
    input_file = "z_lower_1.csv"
    output_file = "processed_z_lower_2.csv"
    process_printer_data(input_file, output_file)