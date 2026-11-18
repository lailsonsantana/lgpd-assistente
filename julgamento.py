from chat import *
from llm import *
import asyncio

MODELO_ASSISTENTE = "gemini-3.5-flash-lite"
MODELO_JULGAMENTO = "gemini-3.1-flash-lite"

async def iniciar_persona_julgamento(conhecimento):
    persona = [
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": f"Você é um especialista na Lei Geral de Proteção de Dados (LGPD)" }]
        },
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "Sua função é avaliar se uma determinada resposta responde adequadamente uma pergunta sobre a LGPD" }]
        }
    ]

    for mensagem, resposta in conhecimento:
        persona.append({
            "type": "user_input",
            "content": [{ "type": "text", "text": f"Caso a pergunta seja '{mensagem}' ou algo parecido, você deve verificar se a resposta é '{resposta}' ou algo parecido" }]
        })

    persona.append(
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "A sua resposta deve conter APENAS uma string que informe, 'ATENDE', se a resposta responde a pergunta e 'NÃO ATENDE' se a resposta não responde a pergunta. Não é necessário explicar o seu julgamento." }]
        }
    )

    return persona

async def testar_alucinacoes(llm, julgador):
    alucinacoes = [
        {
            "pergunta": "O que é Programação Orientada a Objetos?",
            "resposta": "É um tipo de pássaro que voa para o sul durante o inverno."
        },
        {
            "pergunta": "O que é uma classe?",
            "resposta": "É um tipo de comida que serve para alimentar pássaros."
        }
    ]

    for alucinacao in alucinacoes:
        pergunta = alucinacao["pergunta"]
        resposta = alucinacao["resposta"]

        sucesso, julgamento = await obter_resposta(llm, julgador + [
            {
                "type": "user_input",
                "content": [{ "type": "text", "text": f"Pergunta: '{pergunta}', resposta: '{resposta}'" }]
            }
        ], None, modelo = MODELO_JULGAMENTO)
        assert(sucesso == True)
        assert("NÃO ATENDE" in julgamento.output_text)    

        print(f"👍👍 a resposta foi julgada INADEQUADA para a pergunta 👍👍")


async def testar_assistente(llm, conhecimento, assistente, julgador):
    for pergunta, _ in conhecimento:
        sucesso, resposta = await obter_resposta(llm, assistente + [
            {
                "type": "user_input",
                "content": [{ "type": "text", "text": pergunta }]
            }
        ], None, modelo = MODELO_ASSISTENTE)
        assert(sucesso == True)

        resposta = resposta.output_text

        print(f"julgando a resposta '{resposta}' para a pergunta '{pergunta}'")
        sucesso, julgamento = await obter_resposta(llm, julgador + [
            {
                "type": "user_input",
                "content": [{ "type": "text", "text": f"pergunta: '{pergunta}', resposta: '{resposta}'" }]
            }
        ], None, modelo = MODELO_JULGAMENTO)
        assert(sucesso == True)
        assert("NÃO ATENDE" not in julgamento.output_text)    

        print(f"👍👍 a resposta foi julgada ADEQUADA para a pergunta 👍👍")

async def executar():
    iniciado, llm = await iniciar_llm()
    assert(iniciado == True)

    carregado, conhecimento = await carregar_conhecimento(base_conhecimento = "conhecimento/lgpd_menor.json")
    assert(carregado == True and len(conhecimento) > 0)

    julgador = await iniciar_persona_julgamento(conhecimento)
    await testar_alucinacoes(llm, julgador)

    assistente = iniciar_persona_assistente(conhecimento)
    await testar_assistente(llm, conhecimento, assistente, julgador)

if __name__ == "__main__":
    asyncio.run(executar())