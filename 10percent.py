import pandas as pd
from datetime import datetime

# Função para converter timestamp em objeto datetime
def parse_timestamp(ts):
    try:
        return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter timestamp: {ts}, erro: {e}")
        return None

# Carrega o dataset bruto
input_file = 'printer_data5.csv'  # Substitua pelo nome do seu arquivo de entrada
output_file = 'z_lower_1.csv'  # Nome do arquivo de saída

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
df['group'] = (df['time_diff'] > 300).cumsum()

# Lista para armazenar as linhas até Z <= 1.0 mm de cada grupo
result_dfs = []

# Itera sobre os grupos únicos
for group_id in df['group'].unique():
    group_df = df[df['group'] == group_id].copy()
    
    # Seleciona linhas onde Z <= 1.0 mm
    z_4_df = group_df[group_df['Z'] < 1.0].copy()
    
    if z_4_df.empty:
        print(f"Grupo {group_id + 1}: Nenhum dado com Z <= 1.0 mm. Ignorando.")
        continue
    
    # Adiciona ao resultado
    result_dfs.append(z_4_df)
    
    print(f"Grupo {group_id + 1}: {len(group_df)} linhas, selecionadas {len(z_4_df)} linhas (Z <= 1.0 mm)")

# Combina os dados selecionados em um único dataframe
if result_dfs:
    result_df = pd.concat(result_dfs, ignore_index=True)
    
    # Remove as colunas auxiliares
    result_df = result_df.drop(columns=['time_diff', 'group'])
    
    # Salva o dataset resultante
    result_df.to_csv(output_file, index=False)
    print(f"\nDataset com linhas até Z <= 1.0 mm salvo como {output_file}")
else:
    print("\nNenhum dado com Z <= 1.0 mm encontrado em qualquer grupo.")