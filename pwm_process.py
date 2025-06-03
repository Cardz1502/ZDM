import pandas as pd
import numpy as np
from datetime import datetime

def process_pwm_bed_metrics(input_file):
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
    expected_columns = ['timestamp', 'pwm_bed']
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

    # Agrupar os dados por print_group
    grouped = df.groupby('print_group')

    print("\nMétricas de PWM Bed por impressão:")
    for print_group in sorted(grouped.groups.keys()):
        group = grouped.get_group(print_group)
        start_time = group['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
        mean_pwm_bed = group['pwm_bed'].mean() if group['pwm_bed'].notna().any() else 0.0
        std_pwm_bed = group['pwm_bed'].std() if group['pwm_bed'].notna().any() else 0.0
        print(f"Impressão iniciada em {start_time}:")
        print(f"  Média PWM Bed: {mean_pwm_bed:.2f}")
        print(f"  Desvio Padrão PWM Bed: {std_pwm_bed:.2f}")

# Executar o script
if __name__ == "__main__":
    input_file = "printer_data2.csv"
    process_pwm_bed_metrics(input_file)