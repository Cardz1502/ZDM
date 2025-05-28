import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report

# Carregar o dataset atualizado
data = pd.read_csv('processed_data2.csv')  # Ajusta o nome do arquivo conforme necessário

# Remover colunas irrelevantes ou constantes
data = data.drop(columns=['Data', 'id_peça'])

# Codificar variáveis categóricas
label_encoder = LabelEncoder()
data['Tipo de Peça'] = label_encoder.fit_transform(data['Tipo de Peça'])

# Separar o dataset por tipo de peça
quadrados = data[data['Tipo de Peça'] == label_encoder.transform(['QUADRADO'])[0]]
ls = data[data['Tipo de Peça'] == label_encoder.transform(['L'])[0]]
retangulos = data[data['Tipo de Peça'] == label_encoder.transform(['RETANGULO'])[0]]

# Verificar se há dados suficientes para cada tipo de peça
min_samples = 5  # Mínimo de amostras para treinamento e teste
if len(quadrados) < min_samples:
    print(f"Aviso: Apenas {len(quadrados)} amostras para QUADRADO. São necessárias pelo menos {min_samples}.")
if len(ls) < min_samples:
    print(f"Aviso: Apenas {len(ls)} amostras para L. São necessárias pelo menos {min_samples}.")
if len(retangulos) < min_samples:
    print(f"Aviso: Apenas {len(retangulos)} amostras para RETANGULO. São necessárias pelo menos {min_samples}.")

# Definir as colunas de medidas relevantes para cada tipo de peça
# Para QUADRADO e RETANGULO, usamos apenas d1, d2, d3 (d4 a d7 estão vazios)
quadrados_measures = quadrados[['d1', 'd2', 'd3']]
ls_measures = ls[['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']]
retangulos_measures = retangulos[['d1', 'd2', 'd3']]

# Características (X) para cada tipo de peça
# Excluímos d1 a d7 e Resultado
quadrados_X = quadrados.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
ls_X = ls.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
retangulos_X = retangulos.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])

# Para o resultado (OK/NOK), usamos todo o dataset
X_result = data.drop(columns=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'Resultado'])
y_result = data['Resultado']

# Dividir os dados em treino e teste para cada tipo de peça
# Ajustamos o test_size para garantir que haja dados suficientes
test_size = 0.3  # Aumentamos para 30% para ter mais dados de teste
if len(quadrados) >= min_samples:
    quadrados_X_train, quadrados_X_test, quadrados_y_train, quadrados_y_test = train_test_split(
        quadrados_X, quadrados_measures, test_size=test_size, random_state=42)
else:
    quadrados_X_train, quadrados_X_test, quadrados_y_train, quadrados_y_test = quadrados_X, None, quadrados_measures, None

if len(ls) >= min_samples:
    ls_X_train, ls_X_test, ls_y_train, ls_y_test = train_test_split(
        ls_X, ls_measures, test_size=test_size, random_state=42)
else:
    ls_X_train, ls_X_test, ls_y_train, ls_y_test = ls_X, None, ls_measures, None

if len(retangulos) >= min_samples:
    retangulos_X_train, retangulos_X_test, retangulos_y_train, retangulos_y_test = train_test_split(
        retangulos_X, retangulos_measures, test_size=test_size, random_state=42)
else:
    retangulos_X_train, retangulos_X_test, retangulos_y_train, retangulos_y_test = retangulos_X, None, retangulos_measures, None

# Dividir os dados para o resultado
if len(data) >= min_samples:
    X_result_train, X_result_test, y_result_train, y_result_test = train_test_split(
        X_result, y_result, test_size=test_size, random_state=42)
else:
    X_result_train, X_result_test, y_result_train, y_result_test = X_result, None, y_result, None

# Normalizar as características
scaler = StandardScaler()
if len(quadrados) >= min_samples:
    quadrados_X_train = scaler.fit_transform(quadrados_X_train)
    if quadrados_X_test is not None:
        quadrados_X_test = scaler.transform(quadrados_X_test)
else:
    quadrados_X_train = scaler.fit_transform(quadrados_X_train)

if len(ls) >= min_samples:
    ls_X_train = scaler.fit_transform(ls_X_train)
    if ls_X_test is not None:
        ls_X_test = scaler.transform(ls_X_test)
else:
    ls_X_train = scaler.fit_transform(ls_X_train)

if len(retangulos) >= min_samples:
    retangulos_X_train = scaler.fit_transform(retangulos_X_train)
    if retangulos_X_test is not None:
        retangulos_X_test = scaler.transform(retangulos_X_test)
else:
    retangulos_X_train = scaler.fit_transform(retangulos_X_train)

if len(data) >= min_samples:
    X_result_train = scaler.fit_transform(X_result_train)
    if X_result_test is not None:
        X_result_test = scaler.transform(X_result_test)
else:
    X_result_train = scaler.fit_transform(X_result_train)

# Codificar o resultado (OK/NOK)
result_encoder = LabelEncoder()
y_result_train = result_encoder.fit_transform(y_result_train)
if y_result_test is not None:
    y_result_test = result_encoder.transform(y_result_test)

# Treinar os modelos de regressão
if len(quadrados) >= min_samples:
    quadrados_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    quadrados_regressor.fit(quadrados_X_train, quadrados_y_train)

if len(ls) >= min_samples:
    ls_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    ls_regressor.fit(ls_X_train, ls_y_train)

if len(retangulos) >= min_samples:
    retangulos_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    retangulos_regressor.fit(retangulos_X_train, retangulos_y_train)

# Treinar o modelo de classificação
if len(data) >= min_samples:
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    classifier.fit(X_result_train, y_result_train)

# Fazer previsões e avaliar os modelos
# Para QUADRADO
if len(quadrados) >= min_samples and quadrados_X_test is not None:
    quadrados_pred = quadrados_regressor.predict(quadrados_X_test)
    print("Erro Quadrático Médio (MSE) para Quadrados:", mean_squared_error(quadrados_y_test, quadrados_pred))
    print("\nPrevisões para Quadrados (d1, d2, d3):")
    for i in range(len(quadrados_y_test)):
        print(f"Real: {quadrados_y_test.iloc[i].values}, Previsto: {quadrados_pred[i]}")
else:
    print("Não há dados suficientes para avaliar o modelo de regressão para Quadrados.")

# Para L
if len(ls) >= min_samples and ls_X_test is not None:
    ls_pred = ls_regressor.predict(ls_X_test)
    print("Erro Quadrático Médio (MSE) para L:", mean_squared_error(ls_y_test, ls_pred))
    print("\nPrevisões para L (d1 a d7):")
    for i in range(len(ls_y_test)):
        print(f"Real: {ls_y_test.iloc[i].values}, Previsto: {ls_pred[i]}")
else:
    print("Não há dados suficientes para avaliar o modelo de regressão para L.")

# Para RETANGULO
if len(retangulos) >= min_samples and retangulos_X_test is not None:
    retangulos_pred = retangulos_regressor.predict(retangulos_X_test)
    print("Erro Quadrático Médio (MSE) para Retângulos:", mean_squared_error(retangulos_y_test, retangulos_pred))
    print("\nPrevisões para Retângulos (d1, d2, d3):")
    for i in range(len(retangulos_y_test)):
        print(f"Real: {retangulos_y_test.iloc[i].values}, Previsto: {retangulos_pred[i]}")
else:
    print("Não há dados suficientes para avaliar o modelo de regressão para Retângulos.")

# Avaliar o modelo de classificação
if len(data) >= min_samples and X_result_test is not None:
    y_result_pred = classifier.predict(X_result_test)
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
else:
    print("Não há dados suficientes para avaliar o modelo de classificação.")