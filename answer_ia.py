import subprocess
import re
import shutil
import sys

def strip_think_blocks_a(text: str) -> str:
    return re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()

def generate_answer(question: str, result: str) -> str:
    # Verifica se 'ollama' está no PATH
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        sys.exit("Erro: não encontrei o comando 'ollama' no PATH. "
                 "Verifique se o Ollama está instalado e no PATH.")

    context = f"""
Você é um modelo que elabora respostas em linguagem natural para perguntas de usuários,
com base na pergunta original e no resultado retornado pelo SQL Server.

Tabelas disponíveis:
- tbVendasDashboard (tabela fato principal)
- idVendas (int)
- nrCNPJ (varchar)
- nmFilial (varchar)
- dtVenda (date)
- vlVenda (float)
- txMeta (float)

Exemplo de dados em tbVendasDashboard:
idVendas = 14, nrCNPJ = 12345678000118, nmFilial = 'FILIAL 0001', dtVenda = '2024-01-01', vlVenda = 14759.74, txMeta = 5.00

Pergunta do usuário:
{question}

Resultado da consulta:
{result}

Agora, **gere apenas a resposta em linguagem natural** para o usuário, sem incluir código SQL ou explicações internas:
""".strip()

    # Sanitiza eventuais caracteres problemáticos
    context = context.replace('\u2011', '-')

    # Executa o Ollama usando o nome 'ollama' que deve estar no PATH
    proc = subprocess.run(
        [ollama_path, "run", "deepseek-r1:14b"],
        input=context,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    cleaned = strip_think_blocks_a(proc.stdout)
    return cleaned