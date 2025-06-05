import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# === 1. Carregar os dados processados ===
df = pd.read_csv("processed_10percent.csv")

# === 2. Mapear rótulos para binário ===
df['Resultado'] = df['Resultado'].map({'OK': 1, 'NOK': 0})

# === 3. Selecionar features numéricas ===
feature_cols = [
    'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 'Média Delta Mesa (°C)',
    'Variação X', 'Variação Y', 'Variação Z',
    'X_max', 'X_min', 'Y_max', 'Y_min',
    'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora',
    'Média PWM Bed', 'Desvio Padrão PWM Bed'
]
X = df[feature_cols]
y = df['Resultado']

# === 4. Dividir os dados ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# === 5. Treinar modelo ===
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# === 6. Previsões e probabilidades ===
y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)

# === 7. Avaliação ===
print("\n=== Relatório de Classificação ===")
print(classification_report(y_test, y_pred))

# Matriz de confusão
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["NOK", "OK"], yticklabels=["NOK", "OK"])
plt.xlabel("Previsto")
plt.ylabel("Real")
plt.title("Matriz de Confusão - Random Forest")
plt.tight_layout()
plt.show()

# === 8. Mostrar previsões com confiança ===
results_df = X_test.copy()
results_df['Real'] = y_test.values
results_df['Previsto'] = y_pred
results_df['Confiança_OK'] = y_proba[:, 1]  # Probabilidade de ser OK (classe 1)
results_df['Confiança_NOK'] = y_proba[:, 0]  # Probabilidade de ser NOK (classe 0)

# Mostrar resultados ordenados pela confiança na predição feita
results_df['Confiança'] = results_df.apply(
    lambda row: row['Confiança_OK'] if row['Previsto'] == 1 else row['Confiança_NOK'], axis=1
)
results_df['Previsto_Label'] = results_df['Previsto'].map({1: 'OK', 0: 'NOK'})
results_df['Real_Label'] = results_df['Real'].map({1: 'OK', 0: 'NOK'})

# Mostrar resumo
print("\n=== Previsões Individuais ===")
print(results_df[['Previsto_Label', 'Real_Label', 'Confiança']].sort_values(by='Confiança', ascending=False).to_string(index=False))

# Opcional: salvar para Excel ou CSV
# results_df.to_csv("resultados_com_previsao.csv", index=False)
