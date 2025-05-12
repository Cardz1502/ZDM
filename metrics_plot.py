import pandas as pd
import numpy as np

# Função para comparar métricas no processed_data2.csv
def compare_metrics(input_file):
    print("Lendo o processed_data2.csv...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except FileNotFoundError:
        print(f"Erro: O arquivo {input_file} não foi encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo {input_file}: {e}")
        return

    if df.empty:
        print("Erro: O arquivo processed_data2.csv está vazio. Não há dados para comparar.")
        return

    # Verificar se as colunas esperadas estão presentes
    expected_columns = [
        'Tipo de Peça', 'id_peça', 'Data',
        'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 'Média Delta Mesa (°C)', 
        'Tempo Fora do Intervalo Extrusora (%)', 'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)',
        'Variação X', 'Variação Y', 'Variação Z',
        'X_max', 'X_min', 'Y_max', 'Y_min',
        'Accel_print', 'Accel_retract', 'Accel_travel', 'Média jerk_x', 'Média jerk_y',
        'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
        'Resultado'
    ]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"Erro: As seguintes colunas esperadas não foram encontradas: {missing_columns}")
        print("Colunas encontradas:", list(df.columns))
        return

    # Renomear as colunas para facilitar a comparação (usar nomes mais curtos e consistentes)
    df = df.rename(columns={
        'Média Delta temp_nozzle': 'T_delta_mean',
        'Máximo Delta temp_nozzle': 'T_delta_max',
        'Média Delta Mesa (°C)': 'B_delta_mean',
        'Tempo Fora do Intervalo Extrusora (%)': 'T_out_of_range',
        'Taxa de Extrusão (mm/min)': 'E_rate',
        'Tempo Ativo de Extrusão (%)': 'E_active_time',
        'Variação X': 'X_variation',
        'Variação Y': 'Y_variation',
        'Variação Z': 'Z_variation',
        'X_max': 'X_max',
        'X_min': 'X_min',
        'Y_max': 'Y_max',
        'Y_min': 'Y_min',
        'Accel_print': 'Accel_print',
        'Accel_retract': 'Accel_retract',
        'Accel_travel': 'Accel_travel',
        'Média jerk_x': 'Jerk_X_mean',
        'Média jerk_y': 'Jerk_Y_mean',
        'Média PWM Extrusora': 'PWM_mean',
        'Desvio Padrão PWM Extrusora': 'PWM_std',
        'id_peça': 'Impressão',
        'Tipo de Peça': 'Tipo_Peça'
    })

    # Mapear os tipos de peça para corresponder aos valores esperados
    valid_piece_types = ['L', 'RETANGULO', 'QUADRADO', 'CAIXA', 'TAMPA']
    df['Tipo_Peça'] = df['Tipo_Peça'].str.upper()
    while True:
        piece_type = input("Qual tipo de peça deseja analisar (L, RETANGULO, QUADRADO, CAIXA, TAMPA)? ").strip().upper()
        if piece_type in valid_piece_types:
            break
        print("Tipo de peça inválido. Escolha entre: L, RETANGULO, QUADRADO, CAIXA, TAMPA.")

    filtered_df = df[df['Tipo_Peça'] == piece_type]
    if filtered_df.empty:
        print(f"Erro: Não há impressões do tipo {piece_type} para comparar.")
        return

    print(f"\nImpressões disponíveis do tipo {piece_type}:")
    print(filtered_df[['Impressão', 'Tipo_Peça', 'Data', 'Resultado']].to_string(index=False))

    ok_impressions = filtered_df[filtered_df['Resultado'] == 'OK']
    nok_impressions = filtered_df[filtered_df['Resultado'] == 'NOK']

    if ok_impressions.empty:
        print(f"Erro: Não há impressões OK do tipo {piece_type} para comparar.")
        return
    if nok_impressions.empty:
        print(f"Erro: Não há impressões NOK do tipo {piece_type} para comparar.")
        return

    # Lista de métricas a comparar, agora incluindo X_max, X_min, Y_max, Y_min
    metrics = [
        'T_delta_mean', 'T_delta_max', 'B_delta_mean', 'T_out_of_range',
        'E_rate', 'E_active_time', 'Z_variation', 'X_variation', 'Y_variation',
        'X_max', 'X_min', 'Y_max', 'Y_min',
        'Accel_print', 'Accel_retract', 'Accel_travel', 'Jerk_X_mean', 'Jerk_Y_mean',
        'PWM_mean', 'PWM_std'
    ]

    print(f"\n=== Tabela de Métricas por Impressão (Tipo: {piece_type}) ===")
    print(filtered_df[['Impressão', 'Tipo_Peça', 'Data'] + metrics + ['Resultado']].to_string(index=False))

    print(f"\n=== Comparação entre Impressões do Tipo {piece_type} ===")
    comparison = {}
    for idx, row in filtered_df.iterrows():
        impression_label = f"Impressão {row['Impressão']} ({row['Resultado']})"
        comparison[impression_label] = row[metrics]
    comparison_df = pd.DataFrame(comparison)
    print(comparison_df.to_string())

    print("\n=== Observações ===")
    print(f"Tipos de peça nas impressões OK (Tipo: {piece_type}):")
    for _, row in ok_impressions.iterrows():
        print(f"- Impressão {row['Impressão']} (Data: {row['Data']}): {row['Tipo_Peça']}")
    print(f"Tipos de peça nas impressões NOK (Tipo: {piece_type}):")
    for _, row in nok_impressions.iterrows():
        print(f"- Impressão {row['Impressão']} (Data: {row['Data']}): {row['Tipo_Peça']}")

    for _, nok_row in nok_impressions.iterrows():
        nok_label = f"Impressão {nok_row['Impressão']} (NOK)"
        for _, ok_row in ok_impressions.iterrows():
            ok_label = f"Impressão {ok_row['Impressão']} (OK)"
            print(f"\nComparando {nok_label} com {ok_label}:")
            for metric in metrics:
                nok_value = nok_row[metric]
                ok_value = ok_row[metric]
                # Tratar valores NaN ou não numéricos
                if pd.isna(nok_value) or pd.isna(ok_value):
                    continue
                try:
                    nok_value = float(nok_value)
                    ok_value = float(ok_value)
                except (ValueError, TypeError):
                    continue
                diff = nok_value - ok_value
                threshold = 0.1 * abs(ok_value) if ok_value != 0 else 0.1
                if abs(diff) > threshold:
                    print(f"- {metric}:")
                    print(f"  {ok_label}: {ok_value:.2f}")
                    print(f"  {nok_label}: {nok_value:.2f}")
                    print(f"  Diferença: {diff:.2f}")
                    if diff > 0:
                        print(f"  Observação: O valor de {metric} é significativamente maior na NOK.")
                    else:
                        print(f"  Observação: O valor de {metric} é significativamente menor na NOK.")

# Executar o script
if __name__ == "__main__":
    input_file = "processed_data2.csv"
    compare_metrics(input_file)