# LGPD Assistent

Assistente conversacional para orientações introdutórias sobre a LGPD, voltado a pequenas empresas e profissionais autônomos. O projeto combina uma base de conhecimento local, cache semântico, modelo generativo da Google e ferramentas MCP.

## Estrutura do projeto

```text
LGPD Assistent/
├── chat.py                    # CLI conversacional e integração com LLM/MCP
├── llm.py                     # Inicialização e chamadas ao Google Gemini
├── ferramentas.py             # Servidor MCP e ferramenta classificar_dado
├── cache.py                  # Cache semântico persistente com embeddings
├── julgamento.py             # Testes básicos de adequação das respostas
├── conhecimento/
│   ├── lgpd.json             # Base principal de perguntas e respostas
│   ├── lgpd_menor.json       # Conjunto menor usado nos testes
│   └── classificacao_dados.json # Catálogo de tipos e categorias LGPD
├── cache/                    # Dados locais gerados pelo Chroma
├── requirements.txt          # Dependências Python
├── .env.example              # Modelo do arquivo de configuração
└── README.md
```

## Como funciona

- `chat.py` recebe mensagens no terminal, consulta o cache e chama o modelo Gemini.
- `llm.py` encapsula o acesso à API da Google.
- `cache.py` procura respostas semanticamente semelhantes antes de chamar o LLM.
- `ferramentas.py` publica ferramentas MCP em HTTP.
- `julgamento.py` executa verificações automatizadas com um julgador separado.
- Os arquivos em `conhecimento/` fornecem respostas factuais e classificações locais.

## Pré-requisitos

- Python 3.10 ou superior
- Uma chave da Google AI em https://aistudio.google.com/api-keys
- Node.js somente para usar o Inspector visual opcional

## Instalação

Crie e ative um ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copie o arquivo de configuração e informe sua chave:

```powershell
Copy-Item .env.example .env
```

O `.env` deve conter:

```dotenv
GOOGLE_API_KEY=SUA_CHAVE_GOOGLE_AQUI
```

## Execução

Em um terminal, inicie o servidor MCP:

```powershell
python ferramentas.py
```

Em outro terminal, inicie o assistente:

```powershell
python chat.py
```

Use `sair` ou `/s` para encerrar o chat.

Para inspecionar as ferramentas MCP declaradas:

```powershell
fastmcp inspect ferramentas.py
npx @modelcontextprotocol/inspector
```

## Verificação do classificador MCP

Dentro de `ferramentas.py`, `classificar_dado_foi_executado()` informa se a ferramenta já foi chamada:

```python
if classificar_dado_foi_executado():
    print("classificar_dado já foi executado")
```

`obter_status_classificar_dado()` retorna um dicionário com:

- `executado`: indica se houve ao menos uma execução;
- `quantidade_execucoes`: número de chamadas;
- `ultimo_tipo_dado`: último parâmetro recebido;
- `ultima_execucao`: horário UTC da última chamada.

Também é publicada a ferramenta MCP `status_classificar_dado`, que permite consultar esse estado por um cliente MCP sem alterar o retorno de `classificar_dado`.
No `chat.py`, o estado é consultado imediatamente após cada execução de `classificar_dado`; o terminal informa se ela foi executada e o total acumulado de chamadas.

