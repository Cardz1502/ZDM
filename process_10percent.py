import pandas as pd
import numpy as np
from datetime import datetime

# Função principal para processar o CSV
def process_printer_data(input_file, output_file):
    print("Lendo o printer_data2.csv...")
    try:
        df = pd.read_csv(input_file, encoding='latin-1', sep=',', index_col=False, on_bad_lines='warn')
        print("Arquivo lido com separador vírgula (,).")
    except (pd.errors.ParserError, ValueError) as e:
        print(f"Erro ao ler com separador vírgula: {e}")
        return

    if df.empty:
        print("Erro: O arquivo printer_data2.csv está vazio. Não há dados para processar.")
        return

    print("Colunas disponíveis no printer_data2.csv:")
    print(list(df.columns))

    # Verificar se as colunas esperadas estão presentes
    expected_columns = [
        'timestamp', 'temp_nozzle', 'temp_target_nozzle', 'temp_delta_nozzle', 
        'pwm_nozzle', 'temp_bed', 'temp_target_bed', 'temp_delta_bed', 'pwm_bed',
        'X', 'Y', 'Z', 'E', 'accel_print', 'accel_retract', 'accel_travel',
        'jerk_x', 'jerk_y', 'filename'
    ]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"Erro: As seguintes colunas esperadas não foram encontradas: {missing_columns}")
        print("Colunas encontradas:", list(df.columns))
        print("Verifique o formato do arquivo printer_data2.csv.")
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

    # Ler o processed_data2.csv para determinar as impressões já processadas
    processed_prints = set()
    try:
        processed_df = pd.read_csv(output_file, encoding='utf-8')
        if not processed_df.empty:
            existing_ids = processed_df['id_peça'].tolist()
            last_id = max(existing_ids) if existing_ids else 0
        else:
            last_id = 0
    except FileNotFoundError:
        last_id = 0
        processed_df = pd.DataFrame()

    # Agrupar os dados por print_group (cada grupo é uma impressão distinta)
    grouped = df.groupby('print_group')
    all_prints = sorted(grouped.groups.keys())  # Lista de impressões ordenadas

    # Determinar as impressões que ainda não foram processadas
    prints_to_process = []
    piece_id = last_id + 1
    processed_count = last_id  # Número de impressões já processadas

    for i, print_group in enumerate(all_prints):
        if i + 1 > processed_count:
            prints_to_process.append(print_group)

    if not prints_to_process:
        print("Não há novas impressões para processar.")
        return

    print(f"Processando {len(prints_to_process)} novas impressões...")
    processed_data = []

    for print_group in prints_to_process:
        group = grouped.get_group(print_group)
        metrics = {}
        metrics['id_peça'] = piece_id

        # Adicionar a data da impressão (data do primeiro registro do grupo)
        start_time = group['timestamp'].iloc[0]
        end_time = group['timestamp'].iloc[-1]
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_time.strftime('%H:%M:%S')
        metrics['Data'] = f"{start_str}/{end_str}"

        # Métricas da impressão
        metrics['Média Delta temp_nozzle'] = group['temp_delta_nozzle'].mean() if group['temp_delta_nozzle'].notna().any() else 0.0
        metrics['Máximo Delta temp_nozzle'] = group['temp_delta_nozzle'].max() if group['temp_delta_nozzle'].notna().any() else 0.0
        metrics['Média Delta Mesa (°C)'] = group['temp_delta_bed'].mean() if group['temp_delta_bed'].notna().any() else 0.0
        metrics['Variação Z'] = group['Z'].std() if group['Z'].notna().any() else 0.0
        metrics['Variação X'] = group['X'].std() if group['X'].notna().any() else 0.0
        metrics['Variação Y'] = group['Y'].std() if group['Y'].notna().any() else 0.0

        # Adicionar métricas de máximo e mínimo para X e Y
        metrics['X_max'] = group['X'].max() if group['X'].notna().any() else 0.0
        metrics['X_min'] = group['X'].min() if group['X'].notna().any() else 0.0
        metrics['Y_max'] = group['Y'].max() if group['Y'].notna().any() else 0.0
        metrics['Y_min'] = group['Y'].min() if group['Y'].notna().any() else 0.0

        metrics['Média PWM Extrusora'] = group['pwm_nozzle'].mean() if group['pwm_nozzle'].notna().any() else 0.0
        metrics['Desvio Padrão PWM Extrusora'] = group['pwm_nozzle'].std() if group['pwm_nozzle'].notna().any() else 0.0

        # Calcular média e desvio padrão do PWM da cama
        metrics['Média PWM Bed'] = group['pwm_bed'].mean() if group['pwm_bed'].notna().any() else 0.0
        metrics['Desvio Padrão PWM Bed'] = group['pwm_bed'].std() if group['pwm_bed'].notna().any() else 0.0

        # # Extrair o valor único de filename do grupo
        # if group['filename'].notna().any():
        #     filename = group['filename'].dropna().iloc[0]  # Pega o primeiro valor não nulo
        #     print(f"Filename encontrado: {filename}")
        #     # Mapear o filename para o tipo de peça
        #     if filename == 'zdm4ms~4':
        #         metrics['Tipo de Peça'] = 'QUADRADO'
        #     elif filename == 'zd5b20~1':
        #         metrics['Tipo de Peça'] = 'L'
        #     elif filename == 'zd2c72~1':
        #         metrics['Tipo de Peça'] = 'RETANGULO'
        #     else:
        #         print(f"Erro: Tipo de peça desconhecido para filename '{filename}'.")
        #         return
        # else:
        #     print("Erro: Coluna 'filename' contém apenas valores nulos.")
        #     return

        slb = str("slb")
        metrics['Tipo de Peça'] = str(slb)
        
        # Solicitar o Resultado da impressão (OK ou NOK)
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

    # Reordenar colunas, garantindo correspondência com as chaves de metrics
    columns = [
        'Tipo de Peça', 'id_peça', 'Data',
        'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 'Média Delta Mesa (°C)',
        'Variação X', 'Variação Y', 'Variação Z',
        'X_max', 'X_min', 'Y_max', 'Y_min',
        'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
        'Média PWM Bed', 'Desvio Padrão PWM Bed', 'Resultado'
    ]
    new_processed_df = new_processed_df[columns]

    # Salvar os novos dados no processed_data2.csv
    print(f"\nAdicionando os dados processados em {output_file}...")
    if last_id == 0:
        # Se é a primeira vez, criar o arquivo
        new_processed_df.to_csv(output_file, index=False, encoding='utf-8')
    else:
        # Se o arquivo já existe, adicionar os novos dados
        new_processed_df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8')
    print("Processamento concluído!")

# Executar o script
if __name__ == "__main__":
    input_file = "10percent.csv"
    output_file = "processed_10percent.csv"
    process_printer_data(input_file, output_file)