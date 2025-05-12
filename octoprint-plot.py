import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

# Carregar o CSV com codificação ajustada
csv_file = "printer_data.csv"
df = pd.read_csv(csv_file, encoding="utf-8")
df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])

# Filtrar para apenas o dia desejado
target_date = "2025-04-11"
target_date_checker = pd.to_datetime(target_date).date()  # Ex.: 2025-04-02
df = df[df["Data/Hora"].dt.date == target_date_checker]

# Calcular os deltas (extrusora e mesa)
df["Extrusora Delta (°C)"] = df["Extrusora (°C)"] - df["Extrusora Alvo (°C)"]
df["Mesa Delta (°C)"] = df["Mesa (°C)"] - df["Mesa Alvo (°C)"]

# Configurações gerais
plt.rcParams["figure.figsize"] = (12, 4)  # Tamanho padrão para cada gráfico
marker_size = 3  # Tamanho dos marcadores
line_width = 1   # Espessura das linhas

# Diretórios para salvar os gráficos
output_dir = "plots"
day_dir = os.path.join(output_dir, target_date)
if not os.path.exists(day_dir):
    os.makedirs(day_dir)

individual_dir = "plots_individual"
if not os.path.exists(individual_dir):
    os.makedirs(individual_dir)

# 1. Extrusora (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Extrusora (°C)"], label="Extrusora Atual", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Temperatura da Extrusora ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_extrusora_temp.png"))
feature_dir = os.path.join(individual_dir, "extrusora_temp")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 2. Extrusora Alvo (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Extrusora Alvo (°C)"], label="Extrusora Alvo", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Temperatura Alvo da Extrusora ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_extrusora_alvo.png"))
feature_dir = os.path.join(individual_dir, "extrusora_alvo")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 3. Extrusora Delta (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Extrusora Delta (°C)"], label="Extrusora Delta", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Delta da Temperatura da Extrusora ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Delta (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_extrusora_delta.png"))
feature_dir = os.path.join(individual_dir, "extrusora_delta")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 4. Extrusora PWM
plt.figure()
plt.plot(df["Data/Hora"], df["Extrusora PWM"], label="Extrusora PWM", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("PWM da Extrusora ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("PWM (0-255)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_extrusora_pwm.png"))
feature_dir = os.path.join(individual_dir, "extrusora_pwm")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 5. Mesa (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Mesa (°C)"], label="Mesa Atual", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Temperatura da Mesa ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_mesa_temp.png"))
feature_dir = os.path.join(individual_dir, "mesa_temp")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 6. Mesa Alvo (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Mesa Alvo (°C)"], label="Mesa Alvo", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Temperatura Alvo da Mesa ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_mesa_alvo.png"))
feature_dir = os.path.join(individual_dir, "mesa_alvo")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 7. Mesa Delta (°C)
plt.figure()
plt.plot(df["Data/Hora"], df["Mesa Delta (°C)"], label="Mesa Delta", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Delta da Temperatura da Mesa ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Delta (°C)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_mesa_delta.png"))
feature_dir = os.path.join(individual_dir, "mesa_delta")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 8. Mesa PWM
plt.figure()
plt.plot(df["Data/Hora"], df["Mesa PWM"], label="Mesa PWM", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("PWM da Mesa ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("PWM (0-255)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_mesa_pwm.png"))
feature_dir = os.path.join(individual_dir, "mesa_pwm")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 9. X (mm)
plt.figure()
plt.plot(df["Data/Hora"], df["X (mm)"], label="X", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Posição X ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("X (mm)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_x.png"))
feature_dir = os.path.join(individual_dir, "x")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 10. Y (mm)
plt.figure()
plt.plot(df["Data/Hora"], df["Y (mm)"], label="Y", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Posição Y ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Y (mm)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_y.png"))
feature_dir = os.path.join(individual_dir, "y")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 11. Z (mm)
plt.figure()
plt.plot(df["Data/Hora"], df["Z (mm)"], label="Z", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Posição Z ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Z (mm)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_z.png"))
feature_dir = os.path.join(individual_dir, "z")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 12. E (mm)
plt.figure()
plt.plot(df["Data/Hora"], df["E (mm)"], label="Extrusão (E)", marker="o", markersize=marker_size, linewidth=line_width, color="purple")
plt.title("Extrusão ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Extrusão (mm)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_e.png"))
feature_dir = os.path.join(individual_dir, "e")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 13. Aceleração (mm/s²)
plt.figure()
plt.plot(df["Data/Hora"], df["Aceleração (mm/s²)"], label="Aceleração", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Aceleração ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Aceleração (mm/s²)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_aceleracao.png"))
feature_dir = os.path.join(individual_dir, "aceleracao")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 14. Jerk X (mm/s)
plt.figure()
plt.plot(df["Data/Hora"], df["Jerk X (mm/s)"], label="Jerk X", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Jerk X ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Jerk X (mm/s)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_jerk_x.png"))
feature_dir = os.path.join(individual_dir, "jerk_x")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()

# 15. Jerk Y (mm/s)
plt.figure()
plt.plot(df["Data/Hora"], df["Jerk Y (mm/s)"], label="Jerk Y", marker="o", markersize=marker_size, linewidth=line_width)
plt.title("Jerk Y ao Longo do Tempo")
plt.xlabel("Tempo")
plt.ylabel("Jerk Y (mm/s)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(day_dir, "plot_jerk_y.png"))
feature_dir = os.path.join(individual_dir, "jerk_y")
if not os.path.exists(feature_dir):
    os.makedirs(feature_dir)
plt.savefig(os.path.join(feature_dir, f"{target_date}.png"))
plt.show()