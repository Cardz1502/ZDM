import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# Função para avaliar o modelo e mostrar métricas
def evaluate_model(y_true, y_pred, model_name):
    print(f"\nAvaliação do modelo {model_name}:")
    print(f"Acurácia: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Precisão: {precision_score(y_true, y_pred):.4f}")
    print(f"Recall: {recall_score(y_true, y_pred):.4f}")
    print(f"F1-Score: {f1_score(y_true, y_pred):.4f}")
    
    # Matriz de confusão
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['NOK', 'OK'], yticklabels=['NOK', 'OK'])
    plt.title(f'Matriz de Confusão - {model_name}')
    plt.xlabel('Predito')
    plt.ylabel('Real')
    plt.show()

# Carregar o dataset
input_file = 'processed_z_lower_1.csv'
print(f"Lendo {input_file}...")
try:
    df = pd.read_csv(input_file, encoding='utf-8')
    print("Arquivo lido com sucesso.")
except FileNotFoundError:
    print(f"Erro: Arquivo {input_file} não encontrado.")
    exit(1)

# Verificar se o dataset está vazio
if df.empty:
    print("Erro: O dataset está vazio.")
    exit(1)

# Pré-processamento
# Salvar 'Tipo de Peça' e 'id_peça' para uso posterior
piece_types = df['Tipo de Peça'].copy()
ids = df['id_peça'].copy()

# Codificar 'Tipo de Peça' com one-hot encoding
df = pd.get_dummies(df, columns=['Tipo de Peça'], prefix='Peça')

# Codificar 'Resultado' (OK=1, NOK=0)
le = LabelEncoder()
df['Resultado'] = le.fit_transform(df['Resultado'])  # OK=1, NOK=0

# Selecionar features e target
features = [col for col in df.columns if col not in ['id_peça', 'Data', 'Resultado']]
X = df[features]
y = df['Resultado']

# Dividir em treino e teste (80% treino, 20% teste)
X_train, X_test, y_train, y_test, ids_train, ids_test, piece_types_train, piece_types_test = train_test_split(
    X, y, ids, piece_types, test_size=0.2, random_state=42, stratify=y
)

# Treinar o modelo Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Previsões
y_pred_train = rf_model.predict(X_train)
y_pred_test = rf_model.predict(X_test)

# Avaliar o modelo
evaluate_model(y_train, y_pred_train, 'Random Forest - Treino')
evaluate_model(y_test, y_pred_test, 'Random Forest - Teste')

# Exibir previsões vs valores reais por tipo de peça
print("\nPrevisões vs Valores Reais (Conjunto de Teste):")
for piece_type in ['QUADRADO', 'RETANGULO', 'L']:
    print(f"\n--- {piece_type} ---")
    # Filtrar índices correspondentes ao tipo de peça
    indices = piece_types_test[piece_types_test == piece_type].index
    if len(indices) == 0:
        print("Nenhuma amostra deste tipo no conjunto de teste.")
        continue
    for idx in indices:
        i = piece_types_test.index.get_loc(idx)  # Posição relativa no conjunto de teste
        id_peça = ids_test.iloc[i]
        real_label = le.inverse_transform([y_test.iloc[i]])[0]
        pred_label = le.inverse_transform([y_pred_test[i]])[0]
        print(f"\nAmostra (id_peça: {id_peça}):")
        print(f"Previsto: {pred_label}")
        print(f"Real: {real_label}")

# Importância das features
feature_importance = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nImportância das Features:")
print(feature_importance)

# Plotar importância das features
plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=feature_importance)
plt.title('Importância das Features - Random Forest')
plt.show()

# Salvar o modelo
model_file = 'rf_model_ok_nok.joblib'
joblib.dump(rf_model, model_file)
print(f"\nModelo salvo em {model_file}")

# Salvar o LabelEncoder
le_file = 'label_encoder.joblib'
joblib.dump(le, le_file)
print(f"LabelEncoder salvo em {le_file}")