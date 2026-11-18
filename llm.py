from dotenv import load_dotenv
from google import genai
import asyncio
import os

MODELO = "gemini-3.5-flash-lite"

async def iniciar_llm():
    iniciado, llm = False, None

    try:
        load_dotenv()
        llm = genai.Client(api_key = os.environ["GOOGLE_API_KEY"])

        iniciado = True
    except Exception as e:
        print(f"erro iniciando conexão com IA: {e}")

    return iniciado, llm

async def obter_resposta(llm, mensagens, ferramentas, modelo = MODELO):
    sucesso, resposta = False, None

    try:
        if not ferramentas:
            resposta =  await llm.aio.interactions.create(
                input = mensagens,
                model = modelo
            )
        else:
            resposta =  await llm.aio.interactions.create(
                input = mensagens,
                tools = ferramentas,
                model = modelo
            )

        sucesso = True
    except Exception as e:
        print(f"ocorreu um erro ao obter resposta: {e}")

    return sucesso, resposta

def get_consumo_tokens(resposta):
    uso = resposta.usage

    return {
        "entrada": uso.total_input_tokens,
        "saida": uso.total_output_tokens,
        "raciocinio": uso.total_thought_tokens,
        "ferramentas": uso.total_tool_use_tokens,
        "total": uso.total_tokens
    }

async def executar():
    iniciado, llm = await iniciar_llm()
    if not iniciado: 
        return 
    print("llm iniciado")

    mensagens = [
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "Elabore uma resposta curta para uma saudação. Na sua resposta, você deve se identificar como um sistema especialista dedicado a ensinar programação orientada a objetos"}]
        },
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "O seu nome é LGPD Assistent. Sempre se identifique com esse nome durante saudações"}]
        },
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": "olá, tudo bem?"}]
        }
    ]

    sucesso, resposta = await obter_resposta(llm, mensagens, None)
    if sucesso:
        print(f"resposta do llm: {resposta.output_text}")
    else:
        print("não foi possível obter uma resposta do llm")

if __name__ == "__main__":
    asyncio.run(executar())