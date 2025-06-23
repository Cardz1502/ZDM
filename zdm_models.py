import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
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

# Define as features
feature_columns = ['Speed Factor', 'Média Delta temp_nozzle', 'Máximo Delta temp_nozzle', 
                   'Média Delta Mesa (°C)', 'Tempo Fora do Intervalo Extrusora (%)', 
                   'Taxa de Extrusão (mm/min)', 'Tempo Ativo de Extrusão (%)', 
                   'Variação X', 'Variação Y', 'Variação Z', 'X_max', 'X_min', 
                   'Y_max', 'Y_min', 'Média PWM Extrusora', 'Desvio Padrão PWM Extrusora', 
                   'Média PWM Bed', 'Desvio Padrão PWM Bed']

# Itera sobre cada tipo de peça
for piece_type in ['QUADRADO', 'RETANGULO', 'L']:
    print(f"\n=== Resultados para {piece_type} ===")
    
    # Filtra dados para o tipo de peça
    df_piece = df[df['Tipo de Peça'] == piece_type].copy()
    if df_piece.empty:
        print(f"Nenhum dado encontrado para {piece_type} com Resultado = OK.")
        continue
    
    # Prepara X (features) e y (dimensões)
    X = df_piece[feature_columns]
    dimensions = dimensions_by_type[piece_type]
    y = df_piece[dimensions]
    
    # Verifica se há dados válidos
    if y.isna().any().any():
        print(f"Dados inválidos encontrados para {piece_type}. Ignorando.")
        continue
    
    # Verifica variância das dimensões
    for dim in dimensions:
        variance = y[dim].var()
        if variance < 0.01:
            print(f"Aviso: Dimensão {dim} em {piece_type} tem variância muito baixa ({variance:.6f}). R² pode ser instável.")
    
    # Escala as features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treina o modelo
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    
    # Salva o modelo e o scaler
    #joblib.dump(model, f'model_{piece_type.lower()}.joblib')
    #joblib.dump(scaler, f'scaler_{piece_type.lower()}.joblib')
    print(f"Modelo e scaler para {piece_type} salvos como 'model_{piece_type.lower()}.joblib' e 'scaler_{piece_type.lower()}.joblib'")
    
    # Faz previsões
    y_pred_test = model.predict(X_test)
    
    # Calcula métricas com validação cruzada
    mse_scores = []
    r2_scores = []
    for i, dim in enumerate(dimensions):
        y_dim = y[dim]
        mse = -cross_val_score(model, X_scaled, y_dim, cv=5, scoring='neg_mean_squared_error').mean()
        r2 = cross_val_score(model, X_scaled, y_dim, cv=5, scoring='r2').mean()
        mse_scores.append(mse)
        if not np.isnan(r2):
            r2_scores.append(r2)
    
    # Calcula média das métricas
    mse_mean = np.mean(mse_scores)
    r2_mean = np.mean(r2_scores) if r2_scores else np.nan
    print(f"\nMétricas para {piece_type}:")
    print(f"MSE Teste: {mse_mean:.4f}")
    #print(f"R² Teste: {r2_mean:.4f}" if not np.isnan(r2_mean) else "R² Teste: nan")
    
    # Exibe previsões e valores reais
    print(f"\nPrevisões vs Valores Reais para {piece_type} (Conjunto de Teste):")
    if piece_type in ['QUADRADO', 'RETANGULO']:
        for i in range(len(y_test)):
            print(f"\nAmostra {i + 1}:")
            print(f"Previsto [c, l, h]: [{y_pred_test[i, 0]:.1f}, {y_pred_test[i, 1]:.1f}, {y_pred_test[i, 2]:.1f}]")
            print(f"Real [c, l, h]: [{y_test.iloc[i, 0]:.1f}, {y_test.iloc[i, 1]:.1f}, {y_test.iloc[i, 2]:.1f}]")
    else:  # L
        for i in range(len(y_test)):
            print(f"\nAmostra {i + 1}:")
            print(f"Previsto [c1, c2, l1, l2, l3, l4, h]: [{y_pred_test[i, 0]:.1f}, {y_pred_test[i, 1]:.1f}, {y_pred_test[i, 2]:.1f}, {y_pred_test[i, 3]:.1f}, {y_pred_test[i, 4]:.1f}, {y_pred_test[i, 5]:.1f}, {y_pred_test[i, 6]:.1f}]")
            print(f"Real [c1, c2, l1, l2, l3, l4, h]: [{y_test.iloc[i, 0]:.1f}, {y_test.iloc[i, 1]:.1f}, {y_test.iloc[i, 2]:.1f}, {y_test.iloc[i, 3]:.1f}, {y_test.iloc[i, 4]:.1f}, {y_test.iloc[i, 5]:.1f}, {y_test.iloc[i, 6]:.1f}]")