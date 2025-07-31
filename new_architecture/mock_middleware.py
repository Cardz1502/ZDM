from flask import Flask, request, jsonify

app = Flask(__name__)

# Dicionário de peças fictícias com as suas dimensões
FAKE_DATABASE = {
    7: {
        "id": 7,
        "comprimento": 98.9,
        "largura": 99.3,
        "comprimentoext1": 49.4,
        "comprimentoext2": 49.4,
        "larguraext1": 49.6,
        "larguraext2": 49.6,
        "altura": 12.2
    },
    3: {
        "id": 3,
        "comprimento": 49.4,
        "largura": 49.6,
        "altura": 12.2
    },
    1: {
        "id": 1,
        "comprimento": 100.0,
        "largura": 50.0,
        "altura": 12.0
    },
    2: {
        "id": 2,
        "comprimento": 50.0,
        "largura": 50.0,
        "altura": 12.0
    }
}

@app.route('/aas/assembly', methods=['POST'])
def simulate_middleware():
    ids = request.json
    if not isinstance(ids, list):
        return jsonify({"error": "Expected a list of IDs"}), 400

    response = []
    for piece_id in ids:
        piece = FAKE_DATABASE.get(piece_id)
        if piece:
            response.append(piece)
        else:
            return jsonify({"error": f"ID {piece_id} not found in fake DB"}), 404

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1880)
