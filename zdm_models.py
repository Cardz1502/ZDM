import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report

# Carregar o dataset (assumindo que foi salvo como CSV)
data = pd.read_csv('processed_data2.csv')

# Remover colunas irrelevantes ou constantes
data = data.drop(columns=['Data', 'id_peça', 'Accel_print', 'Accel_retract', 'Accel_travel', 'Média jerk_x', 'Média jerk_y'])

# Codificar variáveis categóricas
label_encoder = LabelEncoder()
data['Tipo de Peça'] = label_encoder.fit_transform(data['Tipo de Peça'])

# Separar o dataset por tipo de peça
quadrados = data[data['Tipo de Peça'] == label_encoder.transform(['QUADRADO'])[0]]
ls = data[data['Tipo de Peça'] == label_encoder.transform(['L'])[0]]
retangulos = data[data['Tipo de Peça'] == label_encoder.transform(['RETANGULO'])[0]]

# Definir as colunas de medidas relevantes para cada tipo de peça
quadrados_measures = quadrados[['d1', 'd2', 'd3']]
ls_measures = ls[['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']]
retangulos_measures = retangulos[['d1', 'd2', 'd3']]

# Características (X) para cada tipo de peça
quadrados_X = quadrados.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
ls_X = ls.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
retangulos_X = retangulos.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])

# Para o resultado (OK/NOK), usamos todo o dataset
X_result = data.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
y_result = data['Resultado']

# Dividir os dados em treino e teste para cada tipo de peça
quadrados_X_train, quadrados_X_test, quadrados_y_train, quadrados_y_test = train_test_split(
    quadrados_X, quadrados_measures, test_size=0.2, random_state=42)
ls_X_train, ls_X_test, ls_y_train, ls_y_test = train_test_split(
    ls_X, ls_measures, test_size=0.2, random_state=42)
retangulos_X_train, retangulos_X_test, retangulos_y_train, retangulos_y_test = train_test_split(
    retangulos_X, retangulos_measures, test_size=0.2, random_state=42)

# Dividir os dados para o resultado
X_result_train, X_result_test, y_result_train, y_result_test = train_test_split(
    X_result, y_result, test_size=0.2, random_state=42)

# Normalizar as características
scaler = StandardScaler()
quadrados_X_train = scaler.fit_transform(quadrados_X_train)
quadrados_X_test = scaler.transform(quadrados_X_test)
ls_X_train = scaler.fit_transform(ls_X_train)
ls_X_test = scaler.transform(ls_X_test)
retangulos_X_train = scaler.fit_transform(retangulos_X_train)
retangulos_X_test = scaler.transform(retangulos_X_test)
X_result_train = scaler.fit_transform(X_result_train)
X_result_test = scaler.transform(X_result_test)

# Codificar o resultado (OK/NOK)
result_encoder = LabelEncoder()
y_result_train = result_encoder.fit_transform(y_result_train)
y_result_test = result_encoder.transform(y_result_test)

# Treinar os modelos de regressão
quadrados_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
quadrados_regressor.fit(quadrados_X_train, quadrados_y_train)

ls_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
ls_regressor.fit(ls_X_train, ls_y_train)

retangulos_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
retangulos_regressor.fit(retangulos_X_train, retangulos_y_train)

# Treinar o modelo de classificação
classifier = RandomForestClassifier(n_estimators=100, random_state=42)
classifier.fit(X_result_train, y_result_train)

# Fazer previsões
quadrados_pred = quadrados_regressor.predict(quadrados_X_test)
ls_pred = ls_regressor.predict(ls_X_test)
retangulos_pred = retangulos_regressor.predict(retangulos_X_test)
y_result_pred = classifier.predict(X_result_test)

# Avaliar os modelos de regressão
print("Erro Quadrático Médio (MSE) para Quadrados:", mean_squared_error(quadrados_y_test, quadrados_pred))
print("Erro Quadrático Médio (MSE) para L:", mean_squared_error(ls_y_test, ls_pred))
print("Erro Quadrático Médio (MSE) para Retângulos:", mean_squared_error(retangulos_y_test, retangulos_pred))

# Mostrar algumas previsões de regressão
print("\nPrevisões para Quadrados (d1, d2, d3):")
for i in range(len(quadrados_y_test)):
    print(f"Real: {quadrados_y_test.iloc[i].values}, Previsto: {quadrados_pred[i]}")

print("\nPrevisões para L (d1 a d7):")
for i in range(len(ls_y_test)):
    print(f"Real: {ls_y_test.iloc[i].values}, Previsto: {ls_pred[i]}")

print("\nPrevisões para Retângulos (d1, d2, d3):")
for i in range(len(retangulos_y_test)):
    print(f"Real: {retangulos_y_test.iloc[i].values}, Previsto: {retangulos_pred[i]}")

# Avaliar o modelo de classificação
accuracy = accuracy_score(y_result_test, y_result_pred)
print(f"\nAcurácia para o resultado (OK/NOK): {accuracy}")

# Verificar as classes presentes no conjunto de teste
unique_classes = np.unique(y_result_test)
print(f"Classes presentes no conjunto de teste: {unique_classes}")
if len(unique_classes) == 1:
    print("Aviso: Apenas uma classe presente no conjunto de teste. O relatório de classificação pode não ser significativo.")
else:
    # Usar 'labels' para especificar as classes esperadas
    print("\nRelatório de Classificação:")
    print(classification_report(y_result_test, y_result_pred, labels=unique_classes, target_names=[result_encoder.inverse_transform([c])[0] for c in unique_classes]))