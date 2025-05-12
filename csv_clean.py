import pandas as pd

# Função para limpar o printer_data.csv por dias
def clean_printer_data(file_path, days_to_exclude):
    # Ler o CSV
    print("Lendo o printer_data.csv...")
    try:
        # Tentar ler com utf-8-sig primeiro (para lidar com BOM)
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except UnicodeDecodeError:
        print("Erro ao ler com utf-8-sig, tentando latin-1...")
        df = pd.read_csv(file_path, encoding='latin-1')
    except pd.errors.ParserError:
        print("Erro ao ler com separador vírgula, tentando ponto e vírgula...")
        df = pd.read_csv(file_path, encoding='utf-8-sig', sep=';')

    # Verificar se o arquivo está vazio
    if df.empty:
        print("Erro: O arquivo printer_data.csv está vazio. Não há dados para processar.")
        return

    # Mostrar as colunas disponíveis
    print("Colunas disponíveis no printer_data.csv:")
    print(list(df.columns))

    # Procurar a coluna de data/hora (considerando variações)
    date_column = None
    for col in df.columns:
        if 'Data/Hora' in col or 'DataHora' in col or 'Timestamp' in col:
            date_column = col
            break

    if date_column is None:
        print("Erro: Nenhuma coluna correspondente a 'Data/Hora' foi encontrada.")
        print("Colunas disponíveis:", list(df.columns))
        return
    else:
        print(f"Coluna de data encontrada: {date_column}")

    # Converter a coluna de data para datetime
    try:
        df['Timestamp'] = pd.to_datetime(df[date_column])
    except ValueError as e:
        print(f"Erro ao converter a coluna '{date_column}' para datetime: {e}")
        return

    # Extrair o dia de cada timestamp
    df['Dia'] = df['Timestamp'].dt.date.astype(str)  # Converter para string no formato YYYY-MM-DD

    # Mostrar o número de linhas antes da filtragem
    total_rows_before = len(df)
    print(f"Total de linhas antes da filtragem: {total_rows_before}")

    # Filtrar: manter apenas linhas cujos dias NÃO estão na lista de exclusão
    filtered_df = df[~df['Dia'].isin(days_to_exclude)]

    # Mostrar quantas linhas foram removidas
    total_rows_after = len(filtered_df)
    removed_rows = total_rows_before - total_rows_after
    print(f"Linhas removidas: {removed_rows}")
    print(f"Linhas mantidas: {total_rows_after}")

    # Remover as colunas temporárias 'Dia' e 'Timestamp' antes de salvar
    filtered_df = filtered_df.drop(columns=['Dia', 'Timestamp'])

    # Sobrescrever o arquivo original
    print(f"\nSobrescrevendo o printer_data.csv com os dados filtrados...")
    filtered_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print("Limpeza concluída!")

# Executar o script
if __name__ == "__main__":
    file_path = "printer_data.csv"  # Arquivo a ser manipulado

    # Lista de dias a excluir (substitua pelos dias que queres remover)
    days_to_exclude = ["2025-04-09"]  # Exemplo: ajustar conforme necessário

    print(f"Dias a excluir: {days_to_exclude}")
    clean_printer_data(file_path, days_to_exclude)