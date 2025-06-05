import pandas as pd

# Nomes dos arquivos de entrada e saída
file1 = 'printer_data2a.csv'  # Substitua pelo nome do primeiro arquivo
file2 = 'printer_data3.csv'  # Substitua pelo nome do segundo arquivo
output_file = 'printer_data5.csv'  # Nome do arquivo combinado

# Lê os dois datasets
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Combina os datasets
combined_df = pd.concat([df1, df2], ignore_index=True)

# Salva o dataset combinado
combined_df.to_csv(output_file, index=False)

print(f"Datasets combinados e salvos como {output_file}")