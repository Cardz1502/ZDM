import pandas as pd
from datetime import datetime

# Função para converter timestamp em objeto datetime
def parse_timestamp(ts):
    try:
        return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter timestamp: {ts}, erro: {e}")
        return None

# Carrega o dataset
input_file = 'printer_data2.csv'  # Substitua pelo nome do seu arquivo de entrada
output_file = 'printer_data2a.csv'  # Nome do arquivo de saída

# Lê o arquivo CSV
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print(f"Arquivo {input_file} não encontrado.")
    exit(1)

# Verifica se a coluna timestamp existe
if 'timestamp' not in df.columns:
    print("Coluna 'timestamp' não encontrada no dataset.")
    exit(1)

# Converte a coluna timestamp para datetime
df['timestamp'] = df['timestamp'].apply(parse_timestamp)

# Verifica se há timestamps inválidos
if df['timestamp'].isnull().any():
    print("Alguns timestamps são inválidos e serão ignorados.")
    df = df.dropna(subset=['timestamp'])

# Identifica grupos de impressão com base em intervalos > 10 minutos (600 segundos)
df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
df['group'] = (df['time_diff'] > 600).cumsum()

# Exibe informações sobre os grupos
print("\nGrupos de impressão encontrados:")
for group_id in df['group'].unique():
    group_df = df[df['group'] == group_id]
    start_time = group_df['timestamp'].iloc[0]
    end_time = group_df['timestamp'].iloc[-1]
    filename = group_df['filename'].iloc[0]
    print(f"Grupo {group_id + 1}: {start_time} a {end_time}, Filename: {filename}, Linhas: {len(group_df)}")

# Solicita ao usuário o valor de speed_factor para cada grupo
for group_id in df['group'].unique():
    while True:
        try:
            new_speed_factor = float(input(f"\nDigite o valor de speed_factor para o grupo {group_id + 1} (ex: 100.0): "))
            break
        except ValueError:
            print("Por favor, insira um valor numérico válido (ex: 100.0).")
    
    # Atualiza o speed_factor para o grupo
    df.loc[df['group'] == group_id, 'speed_factor'] = new_speed_factor
    print(f"Grupo {group_id + 1} atualizado com speed_factor = {new_speed_factor}")

# Remove as colunas auxiliares
df = df.drop(columns=['time_diff', 'group'])

# Salva o dataset modificado
df.to_csv(output_file, index=False)
print(f"\nDataset atualizado e salvo como {output_file}")