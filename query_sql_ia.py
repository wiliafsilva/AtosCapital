import subprocess
import re
import shutil
import sys

def strip_think_blocks(text: str) -> str:
    return re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()

def generate_sql(question: str) -> str:
    # Verifica se 'ollama' está no PATH
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        sys.exit("Erro: não encontrei o comando 'ollama' no PATH. "
                 "Verifique se o Ollama está instalado e no PATH.")

    context = f"""
Você é um modelo que gera consultas em T-SQL especificamente para SQL Server Management Studio 20.
Gere apenas o código SQL, sem explicações ou qualquer outro texto.

Lembrete de comandos SQL Server:

-- Comandos básicos
- Para listar colunas: SELECT coluna FROM tbVendasDashboard
- Para renomear coluna: SELECT coluna AS alias
- Para limitar resultados: SELECT TOP(n) coluna FROM tabela
- Para ordenar: ORDER BY nome_coluna DESC

-- Filtros e condições
- Para filtrar por valor exato: WHERE nome_coluna = valor
- Para datas específicas: WHERE dtVenda = '2024-04-10'
- Para valores maiores/menores: WHERE vlVenda > 10000, WHERE vlVenda < txMeta
- Para comparar colunas: WHERE vlVenda >= txMeta

-- Datas e agregações
- Para somar: SUM(vlVenda)
- Para média: AVG(vlVenda)
- Para contar: COUNT(*), COUNT(idVendas)
- Para agrupar resultados: GROUP BY nome_coluna
- Para condições após agrupamento: HAVING SUM(vlVenda) > 10000
- Para agrupar por mês: GROUP BY MONTH(dtVenda)

-- Exemplos úteis:
- Qual filial vendeu mais? → SELECT TOP 1 nmFilial, SUM(vlVenda) FROM tbVendasDashboard GROUP BY nmFilial ORDER BY SUM(vlVenda) DESC
- Quantas vendas por filial? → SELECT nmFilial, COUNT(idVendas) FROM tbVendasDashboard GROUP BY nmFilial
- Filiais que bateram a meta → WHERE vlVenda >= txMeta
- Total de vendas por mês → GROUP BY MONTH(dtVenda)

Estrutura das tabelas:
- tbVendasDashboard (tabela fato principal)
- idVendas (int)
- nrCNPJ (varchar)
- nmFilial (varchar)
- dtVenda (date)
- vlVenda (float)
- txMeta (float)

Pergunta: {question}
Resposta (apenas o código T-SQL):
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

    cleaned = strip_think_blocks(proc.stdout)
    sql = ""
    for line in cleaned.splitlines():
        if re.match(r'^(SELECT|WITH)', line, flags=re.I):
            sql = line.strip()
            break
    if not sql:
        sql = cleaned.splitlines()[0].strip()

    # Junta tudo numa linha e garante ponto-e-vírgula
    sql = " ".join(sql.split())
    if not sql.endswith(";"):
        sql += ";"
    return sql