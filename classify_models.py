import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.svm import SVC
from xgboost import XGBClassifier
import seaborn as sns
import matplotlib.pyplot as plt
import joblib


# Função para data augmentation
def augment_data(X, y, features, noise_factor=0.05, n_augmentations=10):
    X_augmented = [X]
    y_augmented = [y]
    
    for _ in range(n_augmentations):
        # Ruído gaussiano
        noise = np.random.normal(0, noise_factor * X.std(axis=0), X.shape)
        X_noisy = X + noise
        
        # Perturbações baseadas em domínio
        X_perturbed = X.copy()
        if 'Speed Factor' in features:
            idx = features.index('Speed Factor')
            X_perturbed[:, idx] *= np.random.uniform(0.9, 1.1, X.shape[0])
        if 'Média Delta temp_nozzle' in features:
            idx = features.index('Média Delta temp_nozzle')
            X_perturbed[:, idx] *= np.random.uniform(0.95, 1.05, X.shape[0])
        
        X_augmented.extend([X_noisy, X_perturbed])
        y_augmented.extend([y, y])
    
    return np.vstack(X_augmented), np.hstack(y_augmented)

# Função para avaliar o modelo e mostrar métricas
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
    
    # Matriz de confusão
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['NOK', 'OK'], yticklabels=['NOK', 'OK'])
    plt.title(f'Matriz de Confusão - {model_name}')
    plt.xlabel('Predito')
    plt.ylabel('Real')
    plt.show()
    
    return metrics

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

# Exibir tamanho e distribuição do dataset
print(f"Tamanho do dataset: {len(df)} amostras")
print("Distribuição de OK/NOK no dataset:")
print(df['Resultado'].value_counts(normalize=True))

# Pré-processamento
piece_types = df['Tipo de Peça'].copy()
ids = df['id_peça'].copy()

# Codificar 'Tipo de Peça' com one-hot encoding
df = pd.get_dummies(df, columns=['Tipo de Peça'], prefix='Peça')

# Codificar 'Resultado' (OK=1, NOK=0)
le = LabelEncoder()
df['Resultado'] = le.fit_transform(df['Resultado'])  # OK=1, NOK=0

# Selecionar features e target
features_to_drop = ['Peça_L', 'Peça_QUADRADO', 'Peça_RETANGULO' ,'Variação X', 'X_min', 'id_peça', 'Data', 'Resultado']
#features = [col for col in df.columns if col not in features_to_drop]
features = ['Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle', 
            'Média PWM Extrusora', 'Média PWM Bed', 
            'Tempo Fora do Intervalo Extrusora (%)']
X = df[features]
y = df['Resultado']

# Normalizar as features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test, ids_train, ids_test, piece_types_train, piece_types_test = train_test_split(
    X_scaled, y, ids, piece_types, test_size=0.2, random_state=42, stratify=y
)

# Exibir distribuição no treino e teste
print("Distribuição de OK/NOK no treino:")
print(pd.Series(y_train).value_counts(normalize=True))
print("Distribuição de OK/NOK no teste:")
print(pd.Series(y_test).value_counts(normalize=True))

# Aplicar data augmentation
print("Aplicando data augmentation...")
X_train_aug, y_train_aug = augment_data(X_train, y_train, features, noise_factor=0.05, n_augmentations=2)
print(f"Tamanho do conjunto de treino após augmentation: {X_train_aug.shape[0]} amostras")

# Inicializar os modelos
models = {
    'Random Forest': RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42
    ),
    'XGBoost': XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        scale_pos_weight=len(y_train_aug[y_train_aug == 0]) / len(y_train_aug[y_train_aug == 1])
    ),
    'SVM': SVC(
        kernel='rbf',
        probability=True,
        random_state=42,
        class_weight='balanced'
    )
}

# Treinar e avaliar os modelos
all_metrics = []
for model_name, model in models.items():
    print(f"\nTreinando {model_name}...")
    model.fit(X_train_aug, y_train_aug)
    
    # Previsões no treino
    y_pred_train = model.predict(X_train)
    metrics_train = evaluate_model(y_train, y_pred_train, f'{model_name} - Treino')
    
    # Previsões no teste
    y_pred_test = model.predict(X_test)
    metrics_test = evaluate_model(y_test, y_pred_test, f'{model_name} - Teste')
    all_metrics.append(metrics_test)
    
    # Exibir previsões vs valores reais por tipo de peça
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
    
    # Importância das features (apenas para Random Forest e XGBoost)
    if model_name in ['Random Forest', 'XGBoost']:
        feature_importance = pd.DataFrame({
            'Feature': features,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=False)
        print(f"\nImportância das Features - {model_name}:")
        print(feature_importance)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Importance', y='Feature', data=feature_importance)
        plt.title(f'Importância das Features - {model_name}')
        plt.show()
    
    # Salvar o modelo
    model_file = f'{model_name.lower().replace(" ", "_")}_ok_nokv2.joblib'
    joblib.dump(model, model_file)
    print(f"Modelo salvo em {model_file}")

# Comparar métricas
metrics_df = pd.DataFrame(all_metrics)
print("\nComparação de Métricas (Conjunto de Teste):")
print(metrics_df[['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].round(4))

# Salvar o LabelEncoder e o Scaler
le_file = 'label_encoderv2.joblib'
joblib.dump(le, le_file)
print(f"LabelEncoder salvo em {le_file}")

scaler_file = 'scalerv2.joblib'
joblib.dump(scaler, scaler_file)
print(f"Scaler salvo em {scaler_file}")