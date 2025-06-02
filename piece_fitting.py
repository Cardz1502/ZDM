import pandas as pd
import numpy as np

BOX_LENGTH = 100
BOX_WIDTH = 99.5  
SLOT_SIZE = 50  
MIN_GAP = 0.3  # Diferença mínima para caber nas dimensões do slot
FIT_GAP = 0.5  # Folga mínima necessária para caber na caixa (0.5 mm)

def load_database(file_path='processed_data2.csv'):
    try:
        data = pd.read_csv(file_path)
        # Garantir que as colunas d1 a d7 sejam numéricas
        data[['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']] = data[['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']].apply(pd.to_numeric, errors='coerce')
        return data
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado. Certifique-se de que o arquivo existe.")
        exit(1)
    except Exception as e:
        print(f"Erro ao carregar o arquivo {file_path}: {e}")
        exit(1)

def get_piece_dimensions(data, selected_piece_ids):
    # Filtrar peças com Resultado 'OK' e IDs correspondentes
    valid_pieces = data[(data['Resultado'] == 'OK') & (data['id_peça'].isin(selected_piece_ids))]
    
    # Verificar se todos os IDs estão disponíveis
    if len(valid_pieces) != len(selected_piece_ids):
        missing_ids = set(selected_piece_ids) - set(valid_pieces['id_peça'])
        print(f"Aviso: As seguintes peças não estão disponíveis ou não têm Resultado 'OK': {missing_ids}")
        return None, missing_ids

    # Criar dicionário com dimensões
    dimensions_dict = {}
    for idx, piece in valid_pieces.iterrows():
        piece_type = piece['Tipo de Peça']
        if piece_type in ['QUADRADO', 'RETANGULO']:
            dimensions = [piece['d1'], piece['d2'], piece['d3']]
        else:
            dimensions = [piece['d1'], piece['d2'], piece['d3'], piece['d4'], piece['d5'], piece['d6'], piece['d7']]
        dimensions_dict[piece['id_peça']] = dimensions
    
    return dimensions_dict, None

def check_assembly(data, piece_dimensions):
    # Definir regras de montagem (combinações válidas que somam exatamente 4 slots)
    VALID_COMBINATIONS = [
        ('QUADRADO', 4),              # 4 QUADRADO (4 × 1 = 4 slots)
        ('RETANGULO', 2),             # 2 RETANGULO (2 × 2 = 4 slots)
        ('RETANGULO', 1, 'QUADRADO', 2),  # 1 RETANGULO + 2 QUADRADO (2 + 2 = 4 slots)
        ('L', 1, 'QUADRADO', 1)      # 1 L + 1 QUADRADO (3 + 1 = 4 slots)
    ]

    # Contar tipos de peças
    piece_counts = {}
    piece_types = {}
    for piece_id in piece_dimensions.keys():
        piece = data[data['id_peça'] == piece_id].iloc[0]
        piece_type = piece['Tipo de Peça']
        piece_types[piece_id] = piece_type
        piece_counts[piece_type] = piece_counts.get(piece_type, 0) + 1

    # Calcular slots ocupados
    total_slots = 0
    for p_type, count in piece_counts.items():
        if p_type == 'QUADRADO':
            total_slots += count * 1
        elif p_type == 'RETANGULO':
            total_slots += count * 2
        elif p_type == 'L':
            total_slots += count * 3

    # Verificar restrições específicas
    if piece_counts.get('L', 0) > 1:
        print("Erro: Não é permitido montar mais de uma peça L.")
        return False, None
    if 'L' in piece_counts and 'RETANGULO' in piece_counts:
        print("Erro: Não é permitido montar uma peça L com um RETANGULO.")
        return False, None

    # Verificar se a soma dos slots é exatamente 4
    if total_slots != 4:
        print(f"Erro: A combinação de peças ocupa {total_slots} slots, mas deve ocupar exatamente 4 slots.")
        return False, None

    # Verificar se a combinação é válida
    is_valid = False
    for combo in VALID_COMBINATIONS:
        if len(combo) == 2 and piece_counts.get(combo[0], 0) == combo[1]:
            is_valid = True
            break
        elif len(combo) == 4 and piece_counts.get(combo[0], 0) == combo[1] and piece_counts.get(combo[2], 0) == combo[3]:
            is_valid = True
            break

    if not is_valid:
        print(f"Erro: A combinação {piece_counts} não é válida. Combinações permitidas: {VALID_COMBINATIONS}")
        return False, None

    # Simulação de alocação (matriz 2x2)
    grid = np.zeros((2, 2), dtype=int)
    placed_pieces = []
    piece_positions = {}

    # Priorizar peças maiores (L, RETANGULO) antes de QUADRADO
    sorted_pieces = sorted(piece_dimensions.items(), key=lambda x: -({'L': 3, 'RETANGULO': 2, 'QUADRADO': 1}[piece_types[x[0]]]))

    for piece_id, dims in sorted_pieces:
        p_type = piece_types[piece_id]
        fits = False

        if p_type == 'QUADRADO':
            for i in range(2):
                for j in range(2):
                    if grid[i, j] == 0 and dims[0] <= SLOT_SIZE - MIN_GAP and dims[1] <= SLOT_SIZE - MIN_GAP:
                        grid[i, j] = 1
                        fits = True
                        piece_positions[piece_id] = [(i, j)]
                        placed_pieces.append((piece_id, i, j))
                        print(f"Quadrado {piece_id} colocado no slot ({i},{j}).")
                        break
                if fits:
                    break
            if not fits:
                print(f"Erro: Não há espaço para o Quadrado {piece_id}.")
                return False, None

        elif p_type == 'RETANGULO':
            for i in range(2):
                if grid[i, 0] == 0 and grid[i, 1] == 0 and dims[0] <= BOX_LENGTH - MIN_GAP and dims[1] <= SLOT_SIZE - MIN_GAP:
                    grid[i, 0] = 1
                    grid[i, 1] = 1
                    fits = True
                    piece_positions[piece_id] = [(i, 0), (i, 1)]
                    placed_pieces.append((piece_id, i, 0))
                    print(f"Retângulo {piece_id} colocado horizontalmente na linha {i}.")
                    break
            if not fits:
                for j in range(2):
                    if grid[0, j] == 0 and grid[1, j] == 0 and dims[1] <= BOX_WIDTH - MIN_GAP and dims[0] <= SLOT_SIZE - MIN_GAP:
                        grid[0, j] = 1
                        grid[1, j] = 1
                        fits = True
                        piece_positions[piece_id] = [(0, j), (1, j)]
                        placed_pieces.append((piece_id, 0, j))
                        print(f"Retângulo {piece_id} colocado verticalmente na coluna {j}.")
                        break
            if not fits:
                print(f"Erro: Não há espaço para o Retângulo {piece_id}.")
                return False, None

        elif p_type == 'L':
            if grid[0, 0] == 0 and grid[0, 1] == 0 and grid[1, 0] == 0 and dims[0] <= BOX_LENGTH - MIN_GAP and dims[2] <= SLOT_SIZE - MIN_GAP:
                grid[0, 0] = 1
                grid[0, 1] = 1
                grid[1, 0] = 1
                fits = True
                piece_positions[piece_id] = [(0, 0), (0, 1), (1, 0)]
                placed_pieces.append((piece_id, 0, 0))
                print(f"Peça L {piece_id} colocada ocupando linha 0 e slot (1,0).")
            elif grid[0, 0] == 0 and grid[0, 1] == 0 and grid[1, 1] == 0 and dims[0] <= BOX_LENGTH - MIN_GAP and dims[2] <= SLOT_SIZE - MIN_GAP:
                grid[0, 0] = 1
                grid[0, 1] = 1
                grid[1, 1] = 1
                fits = True
                piece_positions[piece_id] = [(0, 0), (0, 1), (1, 1)]
                placed_pieces.append((piece_id, 0, 0))
                print(f"Peça L {piece_id} colocada ocupando linha 0 e slot (1,1).")
            if not fits:
                print(f"Erro: Não há espaço para a peça L {piece_id}.")
                return False, None

    print("Montagem bem-sucedida! Todas as peças foram alocadas.")

    # Calcular dimensões dos 4 lados da montagem com base nas peças
    row_lengths = [[0.0, 0.0], [0.0, 0.0]]  # Comprimento por linha e coluna
    col_widths = [[0.0, 0.0], [0.0, 0.0]]   # Largura por linha e coluna

    for piece_id, positions in piece_positions.items():
        dims = piece_dimensions[piece_id]
        p_type = piece_types[piece_id]

        if p_type == 'QUADRADO':
            i, j = positions[0]
            row_lengths[i][j] = dims[0]  # d1
            col_widths[i][j] = dims[1]   # d2

        elif p_type == 'RETANGULO':
            if positions[0][0] == positions[1][0]:  # Horizontal
                i = positions[0][0]
                row_lengths[i][0] = dims[0]  # d1 (~100)
                col_widths[i][0] = dims[1]   # d2 (~50)
                col_widths[i][1] = dims[1]   # Mesmo d2 no segundo slot
            else:  # Vertical
                j = positions[0][1]
                row_lengths[0][j] = dims[0]  # d1 (~50)
                row_lengths[1][j] = dims[0]  # Mesmo d1 no segundo slot
                col_widths[0][j] = dims[1]   # d2 (~100)

        elif p_type == 'L':
            # L ocupa 3 slots (ex.: linha 0 e slot (1,0))
            # d1 é o comprimento total (~100), d3 é a largura da parte menor (~50)
            row_lengths[0][0] = dims[0] / 2  # Divide d1 para cada slot na linha 0
            row_lengths[0][1] = dims[0] / 2
            col_widths[0][0] = dims[2]       # d3 (~50)
            col_widths[0][1] = dims[2]       # Mesmo d3 no segundo slot
            if (1, 0) in positions:
                row_lengths[1][0] = dims[2]  # d3 (~50)
                col_widths[1][0] = dims[1] - dims[2]  # d2 - d3 para a parte vertical
            else:  # (1,1) está ocupado
                row_lengths[1][1] = dims[2]  # d3 (~50)
                col_widths[1][1] = dims[1] - dims[2]  # d2 - d3 para a parte vertical

    # Calcular os 4 lados da montagem
    top_side = row_lengths[0][0] + row_lengths[0][1]  # Lado superior (linha 0)
    bottom_side = row_lengths[1][0] + row_lengths[1][1]  # Lado inferior (linha 1)
    left_side = col_widths[0][0] + col_widths[1][0]  # Lado esquerdo (coluna 0)
    right_side = col_widths[0][1] + col_widths[1][1]  # Lado direito (coluna 1)

    print("\nDimensões dos 4 lados da montagem:")
    print(f"Lado superior: {top_side:.1f}")
    print(f"Lado inferior: {bottom_side:.1f}")
    print(f"Lado esquerdo: {left_side:.1f}")
    print(f"Lado direito: {right_side:.1f}")

    # Verificar se a montagem cabe na caixa com folga mínima de 0.5 mm
    max_length_allowed = BOX_LENGTH - FIT_GAP  # 100 - 0.5 = 99.5
    max_width_allowed = BOX_WIDTH - FIT_GAP   # 99.5 - 0.5 = 99.0

    if (top_side >= max_length_allowed or
        bottom_side >= max_length_allowed or
        left_side >= max_width_allowed or
        right_side >= max_width_allowed):
        print(f"\nErro: A montagem não cabe na caixa de {BOX_LENGTH}x{BOX_WIDTH}.")
        print(f"As dimensões da montagem devem ser pelo menos {FIT_GAP} mm menores que as da caixa em cada lado.")
        print(f"Limites: Comprimento < {max_length_allowed}, Largura < {max_width_allowed}")
        return False, None

    print(f"\nA montagem cabe na caixa de {BOX_LENGTH}x{BOX_WIDTH} com folga mínima de {FIT_GAP} mm.")

    # Mostrar a matriz 2x2
    print("\nMatriz 2x2 da montagem (IDs das peças):")
    matrix_display = np.full((2, 2), ".", dtype=object)
    for piece_id, positions in piece_positions.items():
        for i, j in positions:
            matrix_display[i, j] = str(piece_id)
    for i in range(2):
        print(" ".join(matrix_display[i, :]))

    return True, piece_positions

def main():
    # Carregar a base de dados
    data = load_database()

    # Mostrar tipos de peças disponíveis
    print("Tipos de peças disponíveis:", data['Tipo de Peça'].unique())

    # Mostrar todas as peças disponíveis
    available_pieces = data[data['Resultado'] == 'OK']
    if available_pieces.empty:
        print("Não há peças disponíveis com Resultado 'OK'.")
        return
    print("Peças disponíveis com Resultado 'OK':")
    for piece_type in data['Tipo de Peça'].unique():
        type_pieces = available_pieces[available_pieces['Tipo de Peça'] == piece_type]
        if not type_pieces.empty:
            print(f"Tipo: {piece_type}")
            for idx, piece in type_pieces.iterrows():
                print(f"  ID: {piece['id_peça']}, Dimensões principais: d1={piece['d1']:.1f}, d2={piece['d2']:.1f}")

    while True:
        ids_input = input(f"Digite os IDs das peças que deseja montar (separados por vírgula, ex.: 1,5,6,7): ").strip()
        try:
            selected_piece_ids = [int(id.strip()) for id in ids_input.split(',')]
        except ValueError:
            print("Erro: Insira IDs válidos (números inteiros separados por vírgula).")
            continue

        print(f"Peças selecionadas (IDs): {selected_piece_ids}")

        # Obter dimensões das peças selecionadas
        piece_dimensions, error_ids = get_piece_dimensions(data, selected_piece_ids)
        if error_ids:
            print(f"Erro: Os seguintes IDs não estão disponíveis: {error_ids}")
            print("Por favor, escolha apenas IDs da lista acima.")
            continue

        print("Dimensões das peças selecionadas:")
        for piece_id, dims in piece_dimensions.items():
            print(f"ID: {piece_id}, Dimensões: {dims}")

        # Verificar se a montagem é possível
        success, piece_positions = check_assembly(data, piece_dimensions)
        if not success:
            print("Montagem não é possível com as peças selecionadas.")
            continue
        break

if __name__ == "__main__":
    main()