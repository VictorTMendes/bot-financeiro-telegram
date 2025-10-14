import logging
import json

import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import database

import os  
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("As variáveis de ambiente TELEGRAM_TOKEN e GEMINI_API_KEY não foram definidas.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

gemini_model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    safety_settings=safety_settings
)

async def analisar_texto_com_gemini(texto_usuario: str) -> dict | None:
    """Usa o Gemini para extrair dados financeiros de uma mensagem de texto de forma mais flexível."""
    
    prompt = f"""
    Você é um especialista em processamento de linguagem natural para uma aplicação financeira.
    Sua tarefa é analisar o texto do usuário e extrair os detalhes de uma transação financeira.

    Texto do usuário: "{texto_usuario}"

    **Regras:**
    1.  **Tipo**: Identifique se é 'renda' (dinheiro entrando, ex: recebi, ganhei, salário) ou 'despesa' (dinheiro saindo, ex: gastei, paguei, comprei).
    2.  **Valor**: Extraia o valor numérico. Ignore moedas (R$, reais) e use ponto como separador decimal.
    3.  **Descrição**: Extraia o item ou motivo principal da transação. Se não houver um item explícito, use uma descrição curta baseada no contexto (ex: "Entrada de dinheiro", "Pagamento geral"). Palavras como 'hoje', 'ontem' não são a descrição principal.
    4.  **Formato de Saída**: Responda **APENAS** com um objeto JSON válido.
    5.  **Não-Financeiro**: Se o texto não for uma transação, retorne um JSON com "tipo": "invalido".

    **Exemplos:**
    - Texto: "gastei 55,90 no supermercado" -> {{"tipo": "despesa", "valor": 55.90, "descricao": "supermercado"}}
    - Texto: "recebi 100 reais hoje" -> {{"tipo": "renda", "valor": 100.0, "descricao": "Entrada de dinheiro"}}
    - Texto: "lanche da tarde, R$15" -> {{"tipo": "despesa", "valor": 15.0, "descricao": "lanche da tarde"}}
    - Texto: "pagamento do freela 850" -> {{"tipo": "renda", "valor": 850.0, "descricao": "pagamento do freela"}}
    - Texto: "25 na farmacia" -> {{"tipo": "despesa", "valor": 25.0, "descricao": "farmacia"}}
    - Texto: "ganhei 50" -> {{"tipo": "renda", "valor": 50.0, "descricao": "Entrada de dinheiro"}}
    - Texto: "paguei a conta de luz de 120,50" -> {{"tipo": "despesa", "valor": 120.50, "descricao": "conta de luz"}}
    - Texto: "ola tudo bem" -> {{"tipo": "invalido"}}
    - Texto: "que dia é hoje?" -> {{"tipo": "invalido"}}
    """
    try:
        response = gemini_model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('`', '').replace('json', '')
        dados = json.loads(cleaned_response)
        return dados
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Erro ao analisar com Gemini ou decodificar JSON: {e}")
        return None

async def gerar_relatorio_com_gemini(transacoes: list) -> str:
    """Usa o Gemini para criar um texto de relatório amigável a partir dos dados."""
    if not transacoes:
        return "Você ainda não tem nenhuma transação registrada este mês para que eu possa gerar um relatório. Comece a me enviar seus gastos e rendas! 🚀"

    total_renda = sum(t[1] for t in transacoes if t[0] == 'renda')
    total_despesa = sum(t[1] for t in transacoes if t[0] == 'despesa')
    saldo = total_renda - total_despesa

    resumo_dados = (
        f"- Total de Renda do mês: R$ {total_renda:.2f}\n"
        f"- Total de Despesas do mês: R$ {total_despesa:.2f}\n"
        f"- Saldo do mês: R$ {saldo:.2f}"
    )

    prompt_relatorio = f"""
    Você é um assistente financeiro amigável e motivador.
    Com base nos seguintes dados financeiros de um usuário para o mês atual, escreva um breve relatório sobre a saúde financeira dele.
    
    - Se o saldo for positivo, parabenize o usuário pelo bom controle e dê uma dica para continuar assim.
    - Se o saldo for negativo, ofereça uma mensagem de apoio e uma dica prática para melhorar nas próximas semanas.
    - Seja conciso, use emojis para deixar a mensagem mais leve e formate o texto com negrito usando a sintaxe do Telegram (*texto*).

    Dados do usuário:
    {resumo_dados}
    """
    try:
        response = gemini_model.generate_content(prompt_relatorio)
        return response.text
    except Exception as e:
        logger.error(f"Erro ao gerar relatório com Gemini: {e}")
        return "Desculpe, não consegui gerar o relatório no momento. Tente novamente mais tarde."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Olá, {user.first_name}! 👋\n\n"
        "Eu sou seu assistente financeiro pessoal. Basta me enviar suas transações em linguagem natural, como:\n"
        "➡️ *'Gastei R$ 50 no almoço'*\n"
        "➡️ *'Recebi 1500 do meu salário'*\n\n"
        "Eu vou registrar tudo para você! A qualquer momento, use o comando /relatorio para ver um resumo do seu mês."
    )

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /relatorio."""
    user_id = update.effective_user.id
    await update.message.reply_text("Gerando seu relatório mensal, um momento... 🤖")

    transacoes = database.consultar_transacoes_do_mes(user_id)
    texto_relatorio = await gerar_relatorio_com_gemini(transacoes)
    
    await update.message.reply_text(texto_relatorio, parse_mode='Markdown')

async def limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /limpar. Apaga o histórico do usuário."""
    user_id = update.effective_user.id
    if context.args and context.args[0].lower() == 'sim':
        await update.message.reply_text("Processando... Apagando seu histórico.")
        try:
            transacoes_apagadas = database.limpar_historico_usuario(user_id)
            await update.message.reply_text(
                f"✅ Pronto! Seu histórico foi limpo. {transacoes_apagadas} transações foram removidas."
            )
        except Exception as e:
            logger.error(f"Erro ao limpar o histórico do usuário {user_id}: {e}")
            await update.message.reply_text("❌ Ocorreu um erro ao tentar limpar seu histórico.")
    else:
        await update.message.reply_html(
            "<b>⚠️ ATENÇÃO: Ação irreversível! ⚠️</b>\n\n"
            "Para apagar permanentemente seu histórico, envie o comando:\n"
            "👉 <b>/limpar sim</b> 👈"
        )

async def lidar_com_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para processar mensagens de texto normais."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    texto = update.message.text

    dados_transacao = await analisar_texto_com_gemini(texto)

    if dados_transacao and dados_transacao.get('tipo') in ['renda', 'despesa']:
        tipo = dados_transacao['tipo']
        valor = dados_transacao['valor']
        descricao = dados_transacao['descricao']

        try:
            valor_float = float(valor)
            database.adicionar_transacao(user_id, user_name, tipo, valor_float, descricao)
            
            emoji = "🟢" if tipo == "renda" else "🔴"
            await update.message.reply_text(
                f"{emoji} Registrado!\n\n"
                f"*Tipo:* {tipo.capitalize()}\n"
                f"*Valor:* R$ {valor_float:.2f}\n"
                f"*Descrição:* {descricao}",
                parse_mode='Markdown'
            )
        except (ValueError, TypeError):
            await update.message.reply_text("Ocorreu um erro ao registrar o valor. Verifique se ele é um número válido.")
    else:
        await update.message.reply_text("Não entendi isso como uma transação financeira. 🤔\nTente algo como 'gastei 25 reais no lanche' ou 'recebi R$100'.")

def main():
    """Função principal que inicia o bot."""
    database.inicializar_db()

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("relatorio", relatorio))
    application.add_handler(CommandHandler("limpar", limpar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lidar_com_mensagem))

    logger.info("Bot iniciado e aguardando mensagens...")

    application.run_polling()

if __name__ == '__main__':
    main()
