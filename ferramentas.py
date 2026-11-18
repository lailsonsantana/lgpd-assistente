from mcp.server.mcpserver import MCPServer
import json

NOME = "especialista_lgpd_ferramentas"
mcp = MCPServer(NOME, "ferramentas de apoio ao especialista em LGPD")

with open("conhecimento/classificacao_dados.json", "r", encoding="utf-8") as arquivo:
    CLASSIFICACAO_DADOS = json.load(arquivo)

TIPOS_PERMITIDOS = ", ".join(sorted(CLASSIFICACAO_DADOS.keys()))

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

    if chave in CLASSIFICACAO_DADOS:
        return CLASSIFICACAO_DADOS[chave]

    return {
        "categoria": "não catalogado",
        "orientacao": "Peça ao usuário mais detalhes sobre o dado e o contexto em que é coletado."
    }

if __name__ == "__main__":
    mcp.run(transport = "streamable-http", host = "0.0.0.0", streamable_http_path = "/mcp")
