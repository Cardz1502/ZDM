import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Carregar o dataset
file_path = 'processed_z_lower_1.csv'
df = pd.read_csv(file_path, encoding='utf-8')

# Garantir que 'Resultado' esteja codificado como 0 (NOK) e 1 (OK) se necessário
# Assumindo que 'Resultado' já está como 'OK'/'NOK' ou 0/1
df['Resultado'] = df['Resultado'].map({'NOK': 0, 'OK': 1})  # Ajuste se o formato for diferente

# Definir as features a analisar
features = [
    'Máximo Delta temp_nozzle', 'Desvio Padrão temp_nozzle',
    'Média PWM Extrusora', 'Média PWM Bed',
    'Tempo Fora do Intervalo Extrusora (%)'
]

# Configurar o estilo dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# 1. Boxplots para cada feature
plt.figure(figsize=(12, 8))
for i, feature in enumerate(features, 1):
    plt.subplot(2, 3, i)
    sns.boxplot(x='Resultado', y=feature, data=df)
    plt.title(f'Boxplot de {feature}')
    plt.xlabel('Resultado (0=NOK, 1=OK)')
    plt.ylabel(feature)
plt.tight_layout()
plt.savefig('boxplots_features.png')
plt.show()

# 2. Gráficos de densidade para cada feature
plt.figure(figsize=(12, 8))
for i, feature in enumerate(features, 1):
    plt.subplot(2, 3, i)
    sns.kdeplot(data=df[df['Resultado'] == 0][feature], label='NOK', shade=True)
    sns.kdeplot(data=df[df['Resultado'] == 1][feature], label='OK', shade=True)
    plt.title(f'Densidade de {feature}')
    plt.xlabel(feature)
    plt.ylabel('Densidade')
    plt.legend()
plt.tight_layout()
plt.savefig('density_plots_features.png')
plt.show()

# 3. Gráfico de dispersão para pares de features (exemplo: as duas mais importantes)
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='Média PWM Extrusora', y='Desvio Padrão temp_nozzle', hue='Resultado', style='Resultado', s=100)
plt.title('Dispersão: Média PWM Extrusora vs Desvio Padrão temp_nozzle')
plt.xlabel('Média PWM Extrusora')
plt.ylabel('Desvio Padrão temp_nozzle')
plt.legend(title='Resultado', labels=['NOK', 'OK'])
plt.savefig('scatter_plot_pwm_vs_temp.png')
plt.show()

# 4. Matriz de correlação com heatmap
plt.figure(figsize=(10, 6))
correlation_matrix = df[features + ['Resultado']].corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Matriz de Correlação das Features')
plt.savefig('correlation_heatmap.png')
plt.show()

# Imprimir algumas estatísticas básicas
print("Estatísticas por Resultado:")
print(df.groupby('Resultado')[features].describe())