from mcp.client.streamable_http import streamable_http_client
from contextlib import AsyncExitStack
from mcp import ClientSession
from cache import *
from llm import *
import asyncio
import json

NOME_ESPECIALISTA = "LGPD Assistent"
BASE_CONHECIMENTO = "conhecimento/lgpd.json"
MODELO = "gemini-3.5-flash-lite"

CACHE = "cache"
MODELO_CACHE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
NOME_CACHE = "lgpd_cache"

URL_FERRAMENTAS = "http://localhost:8000/mcp"

def iniciar_persona_assistente(conhecimento):
    persona = [
        
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    f"Você é um especialista na Lei Geral de Proteção de Dados (LGPD) "
                    "para pequenas empresas e profissionais autônomos chamado {NOME_ESPECIALISTA}"
                )
            }]
        },
        
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Se o usuário te cumprimentar ou perguntar quem é você, identifique-se como "
                    f"{NOME_ESPECIALISTA}, informe que você é um especialista na Lei Geral de Proteção de Dados (LGPD) "
                    "para pequenas empresas e profissionais autônomos e pergunte como pode ajudar."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Use exclusivamente as respostas do conhecimento fornecido e os "
                    "resultados das ferramentas MCP como fontes factuais. Não complete "
                    "lacunas com conhecimento geral, memória de treinamento ou suposições. "
                    "Se a informação solicitada não estiver nessas fontes, diga que não "
                    "há informação suficiente na base e peça os dados necessários."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Quando o usuário perguntar se um tipo específico de dado é pessoal "
                    "ou sensível, você DEVE chamar classificar_dado uma vez para cada "
                    "tipo antes de responder. Não classifique com base no seu conhecimento. "
                    "Após a chamada, use somente a categoria, referência e orientação "
                    "retornadas pela ferramenta; não acrescente conclusões jurídicas."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Não execute classificar_dado para perguntas conceituais, como "
                    "'o que é dado sensível'. Responda apenas se a resposta estiver "
                    "na base de conhecimento fornecida; caso contrário, informe que "
                    "não há informação suficiente na base."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "Se a ferramenta classificar_dado retornar 'depende do contexto' ou 'não catalogado', não afirme uma classificação definitiva: explique o motivo da dúvida e peça ao usuário mais detalhes sobre como o dado é coletado e usado" }]
        },
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "Ao responder com base na ferramenta, cite o artigo da LGPD informado no resultado e lembre que sua orientação não substitui assessoria jurídica" }]
        }
    ]

    for mensagem, resposta in conhecimento:
        persona.append({
            "type": "user_input",
            "content": [{ "type": "text", "text": (
            f"Se o usuário perguntar o mesmo que '{mensagem}', ainda que com outras palavras, "
            f"responda com o conteúdo de '{resposta}'. "
            "Se a pergunta apenas tocar no mesmo tema, mas pedir algo diferente, não use esta resposta."
        )}]
    })

    return persona

async def carregar_conhecimento(base_conhecimento = BASE_CONHECIMENTO):
    carregado, conhecimento = False, []

    try:
        with open(base_conhecimento, "r", encoding = "utf-8") as arquivo:
            conteudo = json.load(arquivo)
            arquivo.close()

        for pergunta_resposta in conteudo:
            pergunta = pergunta_resposta["pergunta"]
            resposta = pergunta_resposta["resposta"]

            conhecimento.append((pergunta, resposta))

        carregado = True
    except Exception as e:
        print(f"erro carregando conhecimento: {e}")

    return carregado, conhecimento

async def conectar_ferramentas(contexto, url_ferramentas = URL_FERRAMENTAS):
    conexao_mcp, ferramentas = None, [] 

    try:
        stream_leitura, stream_escrita = await contexto.enter_async_context(streamable_http_client(url_ferramentas))

        conexao_mcp = await contexto.enter_async_context(ClientSession(stream_leitura, stream_escrita))

        await conexao_mcp.initialize()

        listagem_ferramentas = await conexao_mcp.list_tools()
        for f in listagem_ferramentas.tools:
            ferramentas.append({
                "type": "function",
                "name": f.name,
                "description": f.description,
                "parameters": f.input_schema
            })
    except Exception as e:
        print(f"erro conectando as ferramentas: {e}")

    return conexao_mcp, ferramentas

def extrair_texto_execucao(resultado):
    if resultado.structured_content:
        return json.dumps(resultado.structured_content, ensure_ascii = False)

    conteudo = []
    for c in resultado.content:
        if hasattr(c, "text"):
            conteudo.append(c.text)
        else:
            conteudo.append(str(c))

    return "\n".join(conteudo)

async def executar_ferramentas(conexao_mcp, resposta, mensagens):
    ferramentas_para_executar = [passo for passo in resposta.steps if passo.type == "function_call"]
    status_classificador = None

    if ferramentas_para_executar:
        for ferramenta in ferramentas_para_executar:
            execucao = await conexao_mcp.call_tool(ferramenta.name, arguments = ferramenta.arguments)

            mensagens.append({
                "type": "function_result",
                "name": ferramenta.name,
                "call_id": ferramenta.id,
                "result": [
                    {
                        "type": "text",
                        "text": extrair_texto_execucao(execucao)
                    }
                ]
            })

            if ferramenta.name == "classificar_dado":
                try:
                    status_execucao = await conexao_mcp.call_tool(
                        "status_classificar_dado",
                        arguments = {}
                    )
                    status_classificador = json.loads(
                        extrair_texto_execucao(status_execucao)
                    )
                    print(
                        "status classificar_dado: "
                        f"executado={status_classificador.get('executado')}, "
                        f"total={status_classificador.get('quantidade_execucoes')}"
                    )
                except Exception as e:
                    print(f"não foi possível consultar o status da ferramenta: {e}")

    houve_ferramentas = ferramentas_para_executar != None and len(ferramentas_para_executar) > 0
    return houve_ferramentas, status_classificador

async def executar():
    contexto = AsyncExitStack()
    conexao_mcp, ferramentas = await conectar_ferramentas(contexto)
    if not ferramentas:
        print("não foram encontradas ferramentas")
    else:
        for ferramenta in ferramentas:
            print(f"ferramenta encontrada: {ferramenta['name']}, descrição: {ferramenta['description']}")

    iniciado, llm = await iniciar_llm()
    if not iniciado:
        await contexto.aclose()

        print("erro iniciando llm")
        return    

    carregado, conhecimento = await carregar_conhecimento()
    if not carregado:
        await contexto.aclose()

        print("erro carregando conhecimento")
        return    

    iniciado, modelo_cache, colecao_cache = iniciar_cache(MODELO_CACHE, CACHE, NOME_CACHE)
    if not iniciado:
        await contexto.aclose()

        print("erro iniciando cache")
        return    

    persona = iniciar_persona_assistente(conhecimento)

    while True:
        mensagem = input("👤 ")
        if mensagem in ["sair", "/s"]:
            await contexto.aclose()

            break

        persona.append({
            "type": "user_input",
            "content": [{ "type": "text", "text": mensagem }]
        })

        encontrada, resposta = buscar_cache(mensagem, modelo_cache, colecao_cache)
        if encontrada:
            persona.append({ "type": "model_output", "text": resposta})

            print(f"🤖 {resposta} [resposta do cache]")
        else:
            ferramentas_executadas = False

            while True:
                sucesso, resposta = await obter_resposta(llm, persona, ferramentas, modelo = MODELO)
                persona.extend(resposta.steps)                

                if sucesso:
                    #print(f"🤖 tokens consumidos: {get_consumo_tokens(resposta)}")
                    
                    houve_ferramentas, status_classificador = await executar_ferramentas(
                        conexao_mcp,
                        resposta,
                        persona
                    )

                    if not houve_ferramentas:
                        resposta = resposta.output_text

                        break
                    else:
                        ferramentas_executadas = True

            print(f"🤖 {resposta} [resposta do llm]")
            if not ferramentas_executadas:
                gravar_cache(mensagem, resposta, modelo_cache, colecao_cache)

    await contexto.aclose()

if __name__ == "__main__":
    asyncio.run(executar())
