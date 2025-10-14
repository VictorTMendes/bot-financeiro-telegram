# 🤖 Assistente Financeiro para Telegram com Gemini AI

Um bot para o Telegram, desenvolvido em Python, que atua como um assistente financeiro pessoal. Ele utiliza a API do Google Gemini para interpretar mensagens em linguagem natural, permitindo que os usuários registrem suas despesas e rendas de forma intuitiva.

O bot foi projetado para ser multi-usuário, armazenando os dados de cada pessoa de forma segura e isolada em um banco de dados SQLite.

## ✨ Funcionalidades Principais

-   **✍️ Registro com Linguagem Natural:** Envie mensagens como "gastei 50 reais no almoço" ou "recebi 1500 do salário" e o bot irá entender e registrar a transação.
-   **📊 Relatório Mensal Inteligente:** Use o comando `/relatorio` para receber uma análise do seu mês, gerada pela IA do Gemini, com dicas e observações sobre sua saúde financeira.
-   **🗑️ Limpeza de Histórico:** Apague com segurança todo o seu histórico de transações com o comando `/limpar` (requer confirmação).
-   **👥 Suporte Multi-usuário:** Dados financeiros são vinculados ao ID único de cada usuário do Telegram, garantindo total privacidade.

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python 3
-   **Inteligência Artificial:** Google Gemini API
-   **API do Bot:** `python-telegram-bot`
-   **Banco de Dados:** SQLite3
-   **Gerenciamento de Segredos:** `python-dotenv`