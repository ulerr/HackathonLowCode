from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CONFIG_FILE = "form_config.json"
DATA_FILE = "form_data.json"

# Função para carregar e salvar JSON
def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(file, "w") as f:
            json.dump(default, f)
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Rota para obter a configuração das colunas
@app.route("/api/config", methods=["GET", "POST"])
def handle_config():
    if request.method == "GET":
        config = load_json(CONFIG_FILE, {"fields": []})
        return jsonify(config)
    
    elif request.method == "POST":
        config = request.json
        save_json(CONFIG_FILE, config)
        return jsonify({"message": "Configuração salva com sucesso!"})

# Rota para listar os dados salvos
@app.route("/api/data", methods=["GET"])
def list_form_data():
    data = load_json(DATA_FILE, [])
    return jsonify(data)

# Rota para salvar dados do formulário com validação
@app.route("/api/data", methods=["POST"])
def save_form_data():
    data = request.json
    config = load_json(CONFIG_FILE, {"fields": []})
    fields = config.get("fields", [])

    errors = []
    # Validar os dados recebidos com base na configuração
    for field in fields:
        name = field["name"]
        value = data.get(name)
        required = field.get("required", False)
        max_length = field.get("maxLength")
        min_value = field.get("min")
        max_value = field.get("max")

        if required and (value is None or value == ""):
            errors.append(f"O campo '{name}' é obrigatório.")
            continue

        if max_length and isinstance(value, str) and len(value) > max_length:
            errors.append(f"O campo '{name}' excede o tamanho máximo de {max_length} caracteres.")
            continue

        if isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                errors.append(f"O campo '{name}' deve ser maior ou igual a {min_value}.")
            if max_value is not None and value > max_value:
                errors.append(f"O campo '{name}' deve ser menor ou igual a {max_value}.")

    if errors:
        return jsonify({"errors": errors}), 400

    existing_data = load_json(DATA_FILE, [])
    existing_data.append(data)
    save_json(DATA_FILE, existing_data)
    return jsonify({"message": "Dados salvos com sucesso!"})

# Rota para upload de arquivos CSV
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Apenas arquivos .csv são suportados"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        data = pd.read_csv(file_path)
        data_records = data.to_dict(orient="records")
        return jsonify({"message": "Arquivo carregado com sucesso!", "data": data_records})
    except Exception as e:
        return jsonify({"error": f"Erro ao processar o arquivo: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
