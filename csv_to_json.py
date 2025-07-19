import pandas as pd
import json
import numpy as np

# Lê o CSV
df = pd.read_csv("csv_to_json.csv", sep=",")

# Converter timestamp para string
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

# Substitui qualquer NaN ou np.nan por None (json serializável)
df = df.replace({np.nan: None})

# Converte para lista de dicionários
data = df.to_dict(orient="records")

# Escreve o JSON
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
