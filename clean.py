import csv

# Arquivos de entrada e saída
input_file = "printer_data2.csv"
output_file = "printer_data2_corrected.csv"

# Ler o arquivo e corrigir as linhas
with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    # Ler o cabeçalho
    header = next(reader)
    expected_cols = len(header)  # Deve ser 19
    writer.writerow(header)
    
    # Índices das colunas X, Y, Z, E (para identificar linhas do M114)
    x_index = header.index('X')
    y_index = header.index('Y')
    z_index = header.index('Z')
    e_index = header.index('E')
    
    # Processar cada linha
    for row in reader:
        # Verificar se a linha é do M114 (campos X, Y, Z, E não são vazios)
        is_m114 = (row[x_index] != '' and row[y_index] != '' and 
                   row[z_index] != '' and row[e_index] != '')
        
        if len(row) == expected_cols + 1 and is_m114:
            # Linha do M114 com 20 colunas (tem um None extra antes do filename)
            # Verificar se o penúltimo campo está vazio (deve ser o None extra)
            if row[-2] == '':
                # Remover o penúltimo campo (None) e juntar
                corrected_row = row[:-2] + [row[-1]]
                writer.writerow(corrected_row)
            else:
                print(f"Linha com problema inesperado (20 colunas): {row}")
                writer.writerow(row)
        else:
            # Linha já está correta ou não é do M114
            writer.writerow(row)

print(f"Arquivo corrigido salvo como {output_file}")