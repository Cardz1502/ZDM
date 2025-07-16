from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import re

# --- Modelo de Dados ---
class TerminalMessage(BaseModel):
    terminal_data: list[str]

# Lista para armazenar as temperaturas recebidas
historico_temperaturas = []

# --- Inicialização do App ---
app = FastAPI(
    title="Servidor de Recebimento de Dados do OctoPrint",
    description="Este servidor recebe mensagens do terminal do OctoPrint via POST e também guarda a temperatura.",
    version="1.0.0"
)

# --- Função para extrair temperatura ---
def extrair_temperatura(linha: str) -> float | None:
    match = re.search(r"T:(\d+\.\d+)", linha)
    if match:
        return float(match.group(1))
    return None

# --- POST /message ---
@app.post("/message")
async def receive_message(message: TerminalMessage):
    """
    Recebe mensagens do terminal via POST.
    Extrai e guarda a temperatura da cabeça de impressão (T).
    """
    novas_temperaturas = []

    for line in message.terminal_data:
        print(f"  > {line.strip()}")
        temp = extrair_temperatura(line)
        if temp is not None:
            historico_temperaturas.append(temp)
            novas_temperaturas.append(temp)

    return {
        "status": "success",
        "received_lines": len(message.terminal_data),
        "new_temperatures": novas_temperaturas,
        "total_temperatures_stored": len(historico_temperaturas)
    }

# --- GET para consultar histórico (opcional) ---
@app.get("/temperaturas")
async def listar_temperaturas():
    return {"historico_temperaturas": historico_temperaturas}

# --- Execução do Servidor ---
if __name__ == "__main__":
    print("Iniciando o servidor...")
    print("Acesse http://127.0.0.1:8000 para verificar.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
