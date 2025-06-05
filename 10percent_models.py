import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Carrega o dataset
input_file = 'processed_10percent.csv'
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print(f"Arquivo {input_file} não encontrado.")
    exit(1)

# Filtra apenas impressões com Resultado = OK
df = df[df['Resultado'] == 'OK'].copy()

# Verifica se há dados após o filtro
if df.empty:
    print("Nenhum dado com Resultado = OK encontrado.")
    exit(1)

# Define as dimensões por tipo de peça
dimensions_by_type = {
    'QUADRADO': ['d1', 'd2', 'd3'],
    'RETANGULO': ['d1', 'd2', 'd3'],
    'L': ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']
}

# Define as features (exclui identificadores, Data, dimensões, Resultado e Tipo de Peça)
feature_columns = ['Speed Factor', 'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 
                   'Média Delta Mesa (°C)', 'Tempo Fora do Intervalo Extrusora (%)', 
                   'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)', 
                   'Variação X', 'Variação Y', 'Variação Z', 'X_max', 'X_min', 
                   'Y_max', 'Y_min', 'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora', 
                   'Média PWM Bed', 'Desvio Padrão PWM Bed']

# Itera sobre cada tipo de peça
for piece_type in ['QUADRADO', 'RETANGULO', 'L']:
    print(f"\n=== Treinando modelos para {piece_type} ===")
    
    # Filtra dados para o tipo de peça
    df_piece = df[df['Tipo de Peça'] == piece_type].copy()
    if df_piece.empty:
        print(f"Nenhum dado encontrado para {piece_type} com Resultado = OK.")
        continue
    
    # Prepara X (features)
    X = df_piece[feature_columns]
    
    # Itera sobre as dimensões relevantes para o tipo de peça
    for dim in dimensions_by_type[piece_type]:
        print(f"\nTreinando modelo para {dim}...")
        
        # Prepara y (dimensão alvo)
        y = df_piece[dim]
        
        # Verifica se há dados válidos
        if y.isna().all():
            print(f"Nenhum dado válido para {dim} em {piece_type}. Ignorando.")
            continue
        
        # Divide em treino e teste (80/20)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Treina o modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Faz previsões
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calcula métricas
        rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        
        # Exibe resultados
        print(f"RMSE Treino: {rmse_train:.4f}, R² Treino: {r2_train:.4f}")
        print(f"RMSE Teste: {rmse_test:.4f}, R² Teste: {r2_test:.4f}")
        
        # Exibe importância das features
        feature_importance = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        print(f"Top 5 features mais importantes para {dim}:")
        print(feature_importance.head(5))