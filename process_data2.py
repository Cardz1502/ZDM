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

# Função principal para processar o CSV
def process_printer_data(input_file, output_file):
    print("Lendo o printer_data3.csv...")
    try:
        df = pd.read_csv(input_file, encoding='latin-1', sep=',', index_col=False, on_bad_lines='warn')
        print("Arquivo lido com separador vírgula (,).")
    except (pd.errors.ParserError, ValueError) as e:
        print(f"Erro ao ler com separador vírgula: {e}")
        return

    if df.empty:
        print("Erro: O arquivo printer_data3.csv está vazio. Não há dados para processar.")
        return

    print("Colunas disponíveis no printer_data3.csv:")
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
        print("Verifique o formato do arquivo printer_data3.csv.")
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

    # Ler o processed_data2.csv para obter impressões já processadas
    processed_timestamps = set()
    try:
        processed_df = pd.read_csv(output_file, encoding='utf-8')
        if not processed_df.empty:
            # Extrair os timestamps iniciais das impressões já processadas
            processed_timestamps = set(processed_df['Data'].str.split('/').str[0])
            last_id = max(processed_df['id_peça']) if not processed_df['id_peça'].empty else 0
        else:
            last_id = 0
    except FileNotFoundError:
        last_id = 0

    # Agrupar os dados por print_group (cada grupo é uma impressão distinta)
    grouped = df.groupby('print_group')
    all_prints = sorted(grouped.groups.keys())  # Lista de impressões ordenadas

    # Filtrar apenas as impressões não processadas
    prints_to_process = []
    for print_group in all_prints:
        group = grouped.get_group(print_group)
        start_time = group['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
        if start_time not in processed_timestamps:
            prints_to_process.append(print_group)

    if not prints_to_process:
        print("Não há novas impressões para processar no printer_data3.csv.")
        return

    print(f"Processando {len(prints_to_process)} novas impressões do printer_data3.csv...")
    processed_data = []
    piece_id = last_id + 1

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

        # Calcular Speed Factor (média dos valores não nulos)
        metrics['Speed Factor'] = group['speed_factor'].mean() if group['speed_factor'].notna().any() else 0.0

        # Métricas da impressão
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

        metrics['Variação Z'] = group['Z'].std() if group['Z'].notna().any() else 0.0
        metrics['Variação X'] = group['X'].std() if group['X'].notna().any() else 0.0
        metrics['Variação Y'] = group['Y'].std() if group['Y'].notna().any() else 0.0

        # Adicionar métricas de máximo e mínimo para X e Y
        metrics['X_max'] = group['X'].max() if group['X'].notna().any() else 0.0
        metrics['X_min'] = group['X'].min() if group['X'].notna().any() else 0.0
        metrics['Y_max'] = group['Y'].max() if group['Y'].notna().any() else 0.0
        metrics['Y_min'] = group['Y'].min() if group['Y'].notna().any() else 0.0

        # Calcular média e desvio padrão do PWM da extrusora e da cama
        metrics['Média PWM Extrusora'] = group['pwm_nozzle'].mean() if group['pwm_nozzle'].notna().any() else 0.0
        metrics['Desvio Padrão PWM Extrusora'] = group['pwm_nozzle'].std() if group['pwm_nozzle'].notna().any() else 0.0
        metrics['Média PWM Bed'] = group['pwm_bed'].mean() if group['pwm_bed'].notna().any() else 0.0
        metrics['Desvio Padrão PWM Bed'] = group['pwm_bed'].std() if group['pwm_bed'].notna().any() else 0.0

        # Extrair o valor único de filename do grupo
        if group['filename'].notna().any():
            filename = group['filename'].dropna().iloc[0]  # Pega o primeiro valor não nulo
            print(f"Filename encontrado: {filename}")
            # Mapear o filename para o tipo de peça
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

        # Inicializar as 7 dimensões como vazias
        metrics['d1'] = None
        metrics['d2'] = None
        metrics['d3'] = None
        metrics['d4'] = None
        metrics['d5'] = None
        metrics['d6'] = None
        metrics['d7'] = None

        # Solicitar dimensões com base no tipo de peça
        print(f"\nPeça {piece_id} (Data: {metrics['Data']}, Tipo: {metrics['Tipo de Peça']})")
        while True:
            try:
                if metrics['Tipo de Peça'] == 'QUADRADO':
                    metrics['d1'] = float(input(f"Peça {piece_id} - Comprimento do Quadrado (mm): "))
                    metrics['d2'] = float(input(f"Peça {piece_id} - Largura do Quadrado (mm): "))
                    metrics['d3'] = float(input(f"Peça {piece_id} - Altura do Quadrado (mm): "))
                elif metrics['Tipo de Peça'] == 'RETANGULO':
                    metrics['d1'] = float(input(f"Peça {piece_id} - Comprimento do Retângulo (mm): "))
                    metrics['d2'] = float(input(f"Peça {piece_id} - Largura do Retângulo (mm): "))
                    metrics['d3'] = float(input(f"Peça {piece_id} - Altura do Retângulo (mm): "))
                elif metrics['Tipo de Peça'] == 'L':
                    metrics['d1'] = float(input(f"Peça {piece_id} - Comprimento Externo do L (mm): "))
                    metrics['d2'] = float(input(f"Peça {piece_id} - Largura Externa do L (mm): "))
                    metrics['d3'] = float(input(f"Peça {piece_id} - Comprimento Interno 1 do L (mm): "))
                    metrics['d4'] = float(input(f"Peça {piece_id} - Comprimento Interno 2 do L (mm): "))
                    metrics['d5'] = float(input(f"Peça {piece_id} - Largura Interna 1 do L (mm): "))
                    metrics['d6'] = float(input(f"Peça {piece_id} - Largura Interna 2 do L (mm): "))
                    metrics['d7'] = float(input(f"Peça {piece_id} - Altura do L (mm): "))
                break
            except ValueError:
                print("Por favor, insira um número válido.")

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

    # Reordenar colunas para corresponder ao formato desejado
    columns = [
        'Tipo de Peça', 'id_peça', 'Data', 'Speed Factor',
        'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 'Média Delta Mesa (°C)', 
        'Tempo Fora do Intervalo Extrusora (%)', 'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)',
        'Variação X', 'Variação Y', 'Variação Z',
        'X_max', 'X_min', 'Y_max', 'Y_min',
        'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
        'Média PWM Bed', 'Desvio Padrão PWM Bed',  # Adicionando as novas colunas
        'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'
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
    input_file = "printer_data3.csv"
    output_file = "processed_data2.csv"
    process_printer_data(input_file, output_file)