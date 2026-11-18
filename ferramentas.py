from mcp.server.mcpserver import MCPServer
import json
import threading
from datetime import datetime, timezone

NOME = "especialista_lgpd_ferramentas"
mcp = MCPServer(NOME, "ferramentas de apoio ao especialista em LGPD")

with open("conhecimento/classificacao_dados.json", "r", encoding="utf-8") as arquivo:
    CLASSIFICACAO_DADOS = json.load(arquivo)

TIPOS_PERMITIDOS = ", ".join(sorted(CLASSIFICACAO_DADOS.keys()))

_estado_classificador = {
    "executado": False,
    "quantidade_execucoes": 0,
    "ultimo_tipo_dado": None,
    "ultima_execucao": None,
}
_estado_lock = threading.Lock()

def classificar_dado_foi_executado() -> bool:
    """Indica se a ferramenta classificar_dado já foi executada."""
    with _estado_lock:
        return _estado_classificador["executado"]

def obter_status_classificar_dado() -> dict:
    """Retorna o estado atual de execução da ferramenta classificar_dado."""
    with _estado_lock:
        return dict(_estado_classificador)

@mcp.tool(
    name="classificar_dado",
    title="classificacao de um tipo de dado segundo a LGPD",
    description=(
        "Classifica UM tipo de dado que a empresa do usuario coleta ou trata como "
        "'pessoal', 'sensivel', 'nao pessoal' ou 'depende do contexto', e informa o artigo "
        "da LGPD de referencia. Use sempre que o usuario perguntar se um dado especifico "
        "que ele coleta, guarda ou compartilha e pessoal ou sensivel. NAO use para "
        "perguntas conceituais como 'o que e dado sensivel'. Chame uma vez para cada "
        "tipo de dado. O resultado desta ferramenta e a unica fonte autorizada para "
        "classificar o dado: nao infira nem complemente a categoria usando conhecimento "
        "externo. Se nao houver correspondencia, retorne 'nao catalogado'. "
        f"O parametro tipo_dado deve ser, preferencialmente, um destes valores: {TIPOS_PERMITIDOS}."
    )
)
def classificar_dado(tipo_dado: str):
    chave = tipo_dado.lower().strip()

    with _estado_lock:
        _estado_classificador["executado"] = True
        _estado_classificador["quantidade_execucoes"] += 1
        _estado_classificador["ultimo_tipo_dado"] = tipo_dado
        _estado_classificador["ultima_execucao"] = datetime.now(timezone.utc).isoformat()

    print(f"A ferramenta de classificacao de dados foi chamada com o parametro: {tipo_dado}")

    if chave in CLASSIFICACAO_DADOS:
        return CLASSIFICACAO_DADOS[chave]

    return {
        "categoria": "não catalogado",
        "orientacao": "Peça ao usuário mais detalhes sobre o dado e o contexto em que é coletado."
    }

@mcp.tool(
    name="status_classificar_dado",
    title="status de execucao da ferramenta classificar_dado",
    description="Informa se classificar_dado foi executada e os dados da última execução."
)
def status_classificar_dado():
    return obter_status_classificar_dado()

if __name__ == "__main__":
    mcp.run(transport = "streamable-http", host = "0.0.0.0", streamable_http_path = "/mcp")
