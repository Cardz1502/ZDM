from flask import app, jsonify, request
from flask import Flask
from matplotlib.pyplot import box
import requests
import numpy as np

# Constantes da montagem
BOX_LENGTH = 99.5
BOX_WIDTH = 100
SLOT_SIZE = 50
MIN_GAP = 0.3
FIT_GAP = 0.2

# Initialize Flask application
app = Flask(__name__)

# Constants for URLs and API keys
API_KEY = "-cqzgIHdAaLvW-9EbK6dXW5019dvLPgNyxP7tEwscFw"
AAS_URL = "192.168.250.104:5001"

MIDDLEWARE_URL = 'http://192.168.2.90'  # URL do middleware
CSV_URL = '192.168.250.104:5004'  # URL do CSV
MODELS_URL = '192.168.250.104:5002'

def create_aas_product_complete(ids,product_id, piece_type, length, width, height, state, type):
    payload = {
        "ids": ids,
        "description": piece_type,
        "type": type,
        "id": product_id,
        "comprimento": length,
        "largura": width,
        "altura": height,
        "state": state
    }

    try:
        print("INFO", "CREATE_PRODUCT", f"Enviando produto {product_id} ao AAS com {payload}")
        response = requests.post(f"{MIDDLEWARE_URL}:1880/aas/create", json=payload, timeout=10)
        response.raise_for_status()
        if response.status_code == 200:
            print("INFO", "CREATE_PRODUCT", f"Produto {product_id} criado com sucesso no AAS")
        return True
    except requests.RequestException as e:
        print(f"Erro ao criar produto AAS: {e}")
        return False


def parse_dimensions(response_raw):
    parsed = []

    for entry in response_raw:
        for piece_id_str, info in entry.items():
            piece_id = int(piece_id_str)
            piece_type = info["type"]
            dims = []

            for dim in info["dimensions"]:
                for value in dim.values():
                    if value == "Undefined":
                        dims.append("Undefined")
                    else:
                        dims.append(float(value))

            parsed.append({
                "id_peça": piece_id,
                "tipo": piece_type,
                "dimensoes": dims
            })

    return parsed



def send_ids_to_middleware(ids):
    """
    Sends a list of IDs to the middleware for processing.
    """

    payload = {
        "msg": ids,
        "destination": AAS_URL
    }

    try:
        response = requests.post(f"{MIDDLEWARE_URL}:1880/aas/get/dimensions", json=payload, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.RequestException as e:
        print(f"Error sending data to middleware: {e}")
        return None

def check_assembly_from_middleware(data, box_length, box_width):
    """
    Verifica se a montagem pode ser feita com base nas dimensões e tipos retornados pelo middleware.
    Agora considera as dimensões reais da caixa.
    """
    VALID_COMBINATIONS = [
        ('QUADRADO', 4),
        ('RETANGULO', 2),
        ('RETANGULO', 1, 'QUADRADO', 2),
        ('L', 1, 'QUADRADO', 1)
    ]

    piece_counts = {}
    piece_types = {}
    dimensions = {}

    for piece in data:
        piece_id = piece['id_peça']
        piece_type = piece['tipo']
        dims = piece['dimensoes']

        piece_types[piece_id] = piece_type
        dimensions[piece_id] = dims
        piece_counts[piece_type] = piece_counts.get(piece_type, 0) + 1

    total_slots = 0
    for p_type, count in piece_counts.items():
        if p_type == 'QUADRADO':
            total_slots += count * 1
        elif p_type == 'RETANGULO':
            total_slots += count * 2
        elif p_type == 'L':
            total_slots += count * 3

    if piece_counts.get('L', 0) > 1 or ('L' in piece_counts and 'RETANGULO' in piece_counts):
        return False, "Combinação inválida com peça L."

    if total_slots != 4:
        return False, f"Total de slots ocupados ({total_slots}) diferente de 4."

    is_valid = False
    for combo in VALID_COMBINATIONS:
        if len(combo) == 2 and piece_counts.get(combo[0], 0) == combo[1]:
            is_valid = True
            break
        elif len(combo) == 4 and piece_counts.get(combo[0], 0) == combo[1] and piece_counts.get(combo[2], 0) == combo[3]:
            is_valid = True
            break

    if not is_valid:
        return False, f"Combinação de peças {piece_counts} não é válida."

    # Simulação da alocação em 2x2
    grid = np.zeros((2, 2), dtype=int)
    piece_positions = {}

    sorted_pieces = sorted(dimensions.items(), key=lambda x: -({'L': 3, 'RETANGULO': 2, 'QUADRADO': 1}[piece_types[x[0]]]))

    for piece_id, dims in sorted_pieces:
        p_type = piece_types[piece_id]
        fits = False

        if p_type == 'QUADRADO':
            for i in range(2):
                for j in range(2):
                    if grid[i, j] == 0 and dims[0] <= SLOT_SIZE - MIN_GAP and dims[1] <= SLOT_SIZE - MIN_GAP:
                        grid[i, j] = 1
                        piece_positions[piece_id] = [(i, j)]
                        fits = True
                        break
                if fits: break
            if not fits:
                return False, f"Sem espaço para Quadrado {piece_id}"

        elif p_type == 'RETANGULO':
            for i in range(2):
                if grid[i, 0] == 0 and grid[i, 1] == 0 and dims[0] <= box_length - MIN_GAP and dims[1] <= SLOT_SIZE - MIN_GAP:
                    grid[i, 0] = grid[i, 1] = 1
                    piece_positions[piece_id] = [(i, 0), (i, 1)]
                    fits = True
                    break
            if not fits:
                for j in range(2):
                    if grid[0, j] == 0 and grid[1, j] == 0 and dims[1] <= box_width - MIN_GAP and dims[0] <= SLOT_SIZE - MIN_GAP:
                        grid[0, j] = grid[1, j] = 1
                        piece_positions[piece_id] = [(0, j), (1, j)]
                        fits = True
                        break
            if not fits:
                return False, f"Sem espaço para Retângulo {piece_id}"

        elif p_type == 'L':
            if grid[0, 0] == grid[0, 1] == grid[1, 0] == 0:
                grid[0, 0] = grid[0, 1] = grid[1, 0] = 1
                piece_positions[piece_id] = [(0, 0), (0, 1), (1, 0)]
                fits = True
            elif grid[0, 0] == grid[0, 1] == grid[1, 1] == 0:
                grid[0, 0] = grid[0, 1] = grid[1, 1] = 1
                piece_positions[piece_id] = [(0, 0), (0, 1), (1, 1)]
                fits = True
            if not fits:
                return False, f"Sem espaço para peça L {piece_id}"

    # Calcular as dimensões ocupadas
    row_lengths = [[0.0, 0.0], [0.0, 0.0]]
    col_widths = [[0.0, 0.0], [0.0, 0.0]]

    for piece_id, positions in piece_positions.items():
        dims = dimensions[piece_id]
        p_type = piece_types[piece_id]

        if p_type == 'QUADRADO':
            i, j = positions[0]
            row_lengths[i][j] = dims[0]
            col_widths[i][j] = dims[1]

        elif p_type == 'RETANGULO':
            if positions[0][0] == positions[1][0]:  # horizontal
                i = positions[0][0]
                row_lengths[i][0] = dims[0] / 2
                row_lengths[i][1] = dims[0] / 2
                col_widths[i][0] = col_widths[i][1] = dims[1]
            else:  # vertical
                j = positions[0][1]
                row_lengths[0][j] = row_lengths[1][j] = dims[0]
                col_widths[0][j] = dims[1]

        elif p_type == 'L':
            row_lengths[0][0] = dims[0] / 2
            row_lengths[0][1] = dims[0] / 2
            col_widths[0][0] = col_widths[0][1] = dims[2]
            if (1, 0) in positions:
                row_lengths[1][0] = dims[2]
                col_widths[1][0] = dims[1] - dims[2]
            else:
                row_lengths[1][1] = dims[2]
                col_widths[1][1] = dims[1] - dims[2]

    top_side = row_lengths[0][0] + row_lengths[0][1]
    bottom_side = row_lengths[1][0] + row_lengths[1][1]
    left_side = col_widths[0][0] + col_widths[1][0]
    right_side = col_widths[0][1] + col_widths[1][1]

    if (top_side >= box_length - FIT_GAP or
        bottom_side >= box_length - FIT_GAP or
        left_side >= box_width - FIT_GAP or
        right_side >= box_width - FIT_GAP):
        return False, "Montagem não cabe na caixa com a folga exigida."

    return True, None



@app.route('/assembly', methods=['POST'])
def assembly():
    data = request.json
    print(f"Received assembly request with data: {data}")
    ids = data.get("ids", [])
    product_id = data.get("product_id", None)

    response = send_ids_to_middleware(ids)
    if response is None:
        return jsonify({"error": "Failed to process assembly request"}), 500

    print(f"Response from middleware: {response}")
    parsed_response = parse_dimensions(response)

    # Se alguma dimensão for Undefined → WAIT
    for piece in parsed_response:
        if any(d == "Undefined" for d in piece["dimensoes"]):
            print("INFO", "DIMENSOES", f"Dimensão indefinida detectada nas peças: {parsed_response}")
            return jsonify({"message": "WAIT", "product_id": product_id}), 200

    # Extrair dimensões da caixa
    box_dimensions = None
    filtered_pieces = []

    for piece in parsed_response:
        if piece["tipo"] == "CAIXA":
            box_dimensions = piece["dimensoes"]
        elif piece["tipo"] != "TAMPA":
            filtered_pieces.append(piece)

    if box_dimensions is None:
        return jsonify({"error": "Dimensões da caixa não fornecidas"}), 400

    box_length = box_dimensions[0]
    box_width = box_dimensions[1]
    box_height = box_dimensions[2]

    # Verifica se a montagem cabe
    assembly_check, reason = check_assembly_from_middleware(filtered_pieces, box_length, box_width)

    # Identifica tipo de montagem (ex: "4 QUADRADOS")
    piece_counts = {}
    for piece in filtered_pieces:
        t = piece["tipo"]
        piece_counts[t] = piece_counts.get(t, 0) + 1

    if piece_counts.get("QUADRADO") == 4:
        montagem_tipo = "4 QUADRADOS"
    elif piece_counts.get("RETANGULO") == 2:
        montagem_tipo = "2 RETANGULOS"
    elif piece_counts.get("RETANGULO") == 1 and piece_counts.get("QUADRADO") == 2:
        montagem_tipo = "1 RETANGULO + 2 QUADRADOS"
    elif piece_counts.get("L") == 1 and piece_counts.get("QUADRADO") == 1:
        montagem_tipo = "1L + 1 QUADRADO"
    else:
        montagem_tipo = "DESCONHECIDO"


    # Se a montagem for inválida
    if not assembly_check:
        create_aas_product_complete(ids, product_id, montagem_tipo, box_length, box_width, box_height, "NOK", "FINAL")
        print("Montagem NOK")
        return jsonify({"message": "NOK", "reason": reason, "product_id": product_id}), 200

    # Caso OK
    create_aas_product_complete(ids, product_id, montagem_tipo, box_length, box_width, box_height, "OK", "FINAL")
    print("Montagem OK")

    return jsonify({"message": "OK", "product_id": product_id}), 200




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)