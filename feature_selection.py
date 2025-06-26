import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import make_scorer, f1_score
import numpy as np

# Carregar o dataset
data = pd.read_csv('processed_z_lower_1.csv')
data['Resultado'] = data['Resultado'].map({'OK': 1, 'NOK': 0})

# Features selecionadas
selected_features = ['Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle', 
                    'Média PWM Extrusora', 'Média PWM Bed', 'Tempo Fora do Intervalo Extrusora (%)']
X = data[selected_features]
y = data['Resultado']

# Normalização
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Grid Search para Random Forest
rf = RandomForestClassifier(random_state=42)
rf_param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}
rf_grid = GridSearchCV(rf, rf_param_grid, cv=5, scoring='accuracy')
rf_grid.fit(X_scaled, y)
print("Melhores parâmetros (RF):", rf_grid.best_params_)
print("Melhor acurácia (RF):", rf_grid.best_score_)

# Grid Search para SVM
svm = SVC(random_state=42)
svm_param_grid = {
    'C': [0.1, 1, 10],
    'kernel': ['linear', 'rbf'],
    'gamma': ['scale', 'auto', 0.1]
}
svm_grid = GridSearchCV(svm, svm_param_grid, cv=5, scoring='accuracy')
svm_grid.fit(X_scaled, y)
print("Melhores parâmetros (SVM):", svm_grid.best_params_)
print("Melhor acurácia (SVM):", svm_grid.best_score_)

# Avaliação com F1-score
rf_best = rf_grid.best_estimator_
svm_best = svm_grid.best_estimator_
f1_scorer = make_scorer(f1_score)
rf_f1 = cross_val_score(rf_best, X_scaled, y, cv=5, scoring=f1_scorer).mean()
svm_f1 = cross_val_score(svm_best, X_scaled, y, cv=5, scoring=f1_scorer).mean()
print("F1-score médio (RF):", rf_f1)
print("F1-score médio (SVM):", svm_f1)