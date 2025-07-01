import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.svm import SVC
from xgboost import XGBClassifier
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
from sklearn.decomposition import PCA

# Função para data augmentation
def augment_data(X, y, noise_factor=0.05, n_augmentations=10):
    X_augmented = [X]
    y_augmented = [y]
    
    for _ in range(n_augmentations):
        noise = np.random.normal(0, noise_factor * X.std(axis=0), X.shape)
        X_noisy = X + noise
        X_augmented.append(X_noisy)
        y_augmented.append(y)
    
    return np.vstack(X_augmented), np.hstack(y_augmented)

# Função para avaliar o modelo
def evaluate_model(y_true, y_pred, model_name):
    metrics = {
        'Model': model_name,
        'Accuracy': accuracy_score(y_true, y_pred),
        'Precision': precision_score(y_true, y_pred),
        'Recall': recall_score(y_true, y_pred),
        'F1-Score': f1_score(y_true, y_pred)
    }
    print(f"\nAvaliação do modelo {model_name}:")
    print(f"Acurácia: {metrics['Accuracy']:.4f}")
    print(f"Precisão: {metrics['Precision']:.4f}")
    print(f"Recall: {metrics['Recall']:.4f}")
    print(f"F1-Score: {metrics['F1-Score']:.4f}")
    
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['NOK', 'OK'], yticklabels=['NOK', 'OK'])
    plt.title(f'Matriz de Confusão - {model_name}')
    plt.xlabel('Predito')
    plt.ylabel('Real')
    plt.show()
    
    return metrics

# Carregar dados
input_file = 'processed_z_lower_1.csv'
print(f"Lendo {input_file}...")
try:
    df = pd.read_csv(input_file, encoding='utf-8')
    print("Arquivo lido com sucesso.")
except FileNotFoundError:
    print(f"Erro: Arquivo {input_file} não encontrado.")
    exit(1)

if df.empty:
    print("Erro: O dataset está vazio.")
    exit(1)

print(f"Tamanho do dataset: {len(df)} amostras")
print("Distribuição de OK/NOK no dataset:")
print(df['Resultado'].value_counts(normalize=True).rename('proportion'))

# Pré-processamento
piece_types = df['Tipo de Peça'].copy()
ids = df['id_peça'].copy()
df = pd.get_dummies(df, columns=['Tipo de Peça'], prefix='Peça')
le = LabelEncoder()
df['Resultado'] = le.fit_transform(df['Resultado'])  # OK=1, NOK=0

# Seleção de features
features = ['Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle', 
            'Média PWM Extrusora', 'Média PWM Bed', 
            'Tempo Fora do Intervalo Extrusora (%)']
X = df[features]
y = df['Resultado']

# Normalização
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Divisão treino/teste
X_train, X_test, y_train, y_test, ids_train, ids_test, piece_types_train, piece_types_test = train_test_split(
    X_scaled, y, ids, piece_types, test_size=0.15, random_state=42, stratify=y
)

print("Distribuição de OK/NOK no treino:")
print(pd.Series(y_train).value_counts(normalize=True))
print("Distribuição de OK/NOK no teste:")
print(pd.Series(y_test).value_counts(normalize=True))

# Data Augmentation
print("Aplicando data augmentation...")
X_train_aug, y_train_aug = augment_data(X_train, y_train, noise_factor=0.05, n_augmentations=2)
print(f"Tamanho do conjunto de treino após augmentation: {X_train_aug.shape[0]} amostras")
print("Distribuição de OK/NOK após augmentation no treino:")
print(pd.Series(y_train_aug).value_counts(normalize=True))

# # PCA
# pca = PCA(n_components=0.95)
# X_train_aug_pca = pca.fit_transform(X_train_aug)
# X_train_pca = pca.transform(X_train)  # para avaliação no conjunto original
# X_test_pca = pca.transform(X_test)
# print(f"Redução com PCA: {X.shape[1]} → {X_train_aug_pca.shape[1]} componentes principais")

# Hiperparâmetros
param_grid_rf = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5, 7],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [2, 4],
    'class_weight': [{0: 1.2, 1: 1.0}, {0: 1.5, 1: 1.0}]
}

param_grid_xgb = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5],
    'learning_rate': [0.1, 0.2],
    'scale_pos_weight': [1.5, 2.0]
}

param_grid_svm = {
    'C': [1, 10],
    'kernel': ['rbf'],
    'gamma': ['scale'],
    'class_weight': [None, 'balanced']
}


models = {
    'Random Forest': (RandomForestClassifier(random_state=42), param_grid_rf),
    'XGBoost': (XGBClassifier(random_state=42), param_grid_xgb),
    'SVM': (SVC(probability=True, random_state=42), param_grid_svm)
}

all_metrics = []
for model_name, (model, param_grid) in models.items():
    print(f"\nOtimizando hiperparâmetros para {model_name}...")
    grid_search = GridSearchCV(
        model, param_grid, cv=5, scoring='f1', n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train_aug, y_train_aug)
    
    print(f"Melhores parâmetros para {model_name}: {grid_search.best_params_}")
    best_model = grid_search.best_estimator_
    
    # Avaliação no treino (original)
    y_pred_train = best_model.predict(X_train)
    metrics_train = evaluate_model(y_train, y_pred_train, f'{model_name} - Treino')
    
    # Avaliação no teste
    y_pred_test = best_model.predict(X_test)
    metrics_test = evaluate_model(y_test, y_pred_test, f'{model_name} - Teste')
    all_metrics.append(metrics_test)
    
    # Previsões por tipo de peça
    print(f"\nPrevisões vs Valores Reais (Conjunto de Teste - {model_name}):")
    for piece_type in ['QUADRADO', 'RETANGULO', 'L']:
        print(f"\n--- {piece_type} ---")
        indices = piece_types_test[piece_types_test == piece_type].index
        if len(indices) == 0:
            print("Nenhuma amostra deste tipo no conjunto de teste.")
            continue
        for idx in indices:
            i = piece_types_test.index.get_loc(idx)
            id_peça = ids_test.iloc[i]
            real_label = le.inverse_transform([y_test.iloc[i]])[0]
            pred_label = le.inverse_transform([y_pred_test[i]])[0]
            print(f"\nAmostra (id_peça: {id_peça}):")
            print(f"Previsto: {pred_label}")
            print(f"Real: {real_label}")
    
    # # Importância das features
    # if model_name in ['Random Forest', 'XGBoost']:
    #     feature_importance = pd.DataFrame({
    #         'Feature': features,
    #         'Importance': best_model.feature_importances_
    #     }).sort_values('Importance', ascending=False)
        
    #     print(f"\nImportância das Features - {model_name}:")
    #     print(feature_importance)
        
    #     plt.figure(figsize=(10, 6))
    #     sns.barplot(x='Importance', y='Feature', data=feature_importance)
    #     plt.title(f'Importância das Features - {model_name}')
    #     plt.show()
    
    # Salvar o modelo
    model_file = f'{model_name.lower().replace(" ", "_")}_ok_nokv2.joblib'
    joblib.dump(best_model, model_file)
    print(f"Modelo salvo em {model_file}")

# Comparar métricas
metrics_df = pd.DataFrame(all_metrics)
print("\nComparação de Métricas (Conjunto de Teste):")
print(metrics_df[['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].round(4))

# Salvar codificadores
joblib.dump(le, 'label_encoderv2.joblib')
joblib.dump(scaler, 'scalerv2.joblib')
print("LabelEncoder e Scaler salvos.")
