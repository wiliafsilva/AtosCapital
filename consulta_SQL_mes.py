#Conxão com o banco
import calendar
from datetime import datetime
from matplotlib.dates import relativedelta
import pandas as pd
import pyodbc

dados_empresa = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=aquidaba.infonet.com.br;'
    'DATABASE=dbproinfo;'
    'UID=leituraVendas;'
    'PWD=KRphDP65BM;'
    'Connection Timeout=30'
)

def obter_conexao():
    """Estabelece e retorna uma conexão com o banco de dados."""
    try:
        return pyodbc.connect(dados_empresa)
    except pyodbc.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def obter_nmfilial():
    """Executa a consulta e retorna os nomes das filiais."""
    conn = obter_conexao()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT(nmfilial) FROM tbVendasDashboard ORDER BY nmfilial;')
        nmfilial = [row.nmfilial for row in cursor]  
        return nmfilial
    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return []
    finally:
        conn.close()

def obter_vendas_ano_anterior_mes_anterior(filial, mes, ano):
    """Executa a consulta para obter o total de vendas do mesmo período do ano anterior para a filial especificada."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        SELECT SUM(vlVenda) AS total_vendas_ano_anterior
        FROM tbVendasDashboard
        WHERE YEAR(dtVenda) = ? 
          AND MONTH(dtVenda) = ?
          AND nmFilial = ?
        '''
        cursor.execute(consulta, (ano, mes, filial))
        resultado = cursor.fetchone()
        if resultado and resultado.total_vendas_ano_anterior is not None:
            return resultado.total_vendas_ano_anterior
        else:
            return 0
    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        conn.close()

def obter_meta_mes_anterior(filial, mes, ano):
    """
    Obtém a meta de vendas: soma de vlVenda do mês e ano anteriores ao informados,
    com acréscimo de 5%.
    """
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        consulta = '''
        SELECT SUM(vlVenda) * 1.05 AS meta_mes
        FROM tbVendasDashboard
        WHERE YEAR(dtVenda) = ?
          AND MONTH(dtVenda) = ?
          AND nmFilial = ?
        '''

        ano_anterior = ano - 1
        cursor.execute(consulta, (ano_anterior, mes, filial))
        resultado = cursor.fetchone()

        if resultado and resultado.meta_mes is not None:
            return resultado.meta_mes
        else:
            return 0

    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        conn.close()


def obter_acumulo_de_vendas(filial):
    """Obtém o acúmulo de vendas do mês atual para uma filial específica.
    Se for o primeiro dia do mês, retorna os dados do mês anterior.
    """
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        SELECT 
            SUM(vlVenda) AS acumulo_de_vendas
        FROM dbo.tbVendasDashboard
        WHERE 
            YEAR(dtVenda) = 
                CASE 
                    WHEN DAY(GETDATE()) = 1 THEN YEAR(DATEADD(MONTH, -1, GETDATE()))
                    ELSE YEAR(GETDATE())
                END
          AND MONTH(dtVenda) = 
                CASE 
                    WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                    ELSE MONTH(GETDATE())
                END
          AND nmFilial = ?
        '''
        cursor.execute(consulta, (filial,))
        resultado = cursor.fetchone()
        return resultado.acumulo_de_vendas if resultado and resultado.acumulo_de_vendas is not None else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()
        
        
def obter_vendas_mes_anterior(filial, mes, ano):
    """Executa a consulta para obter o total de vendas do mês e ano especificados para a filial."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        consulta = '''
        SELECT SUM(vlVenda) AS total_vendas_mes_atual
        FROM tbVendasDashboard
        WHERE YEAR(dtVenda) = ?
          AND MONTH(dtVenda) = ?
          AND nmFilial = ?
        '''

        cursor.execute(consulta, (ano, mes, filial))
        resultado = cursor.fetchone()

        if resultado and resultado.total_vendas_mes_atual is not None:
            return resultado.total_vendas_mes_atual
        else:
            return 0

    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        conn.close()


def obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada, ano_selecionado):
    nomes_para_numeros = {
        "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
        "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
        "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
    }

    if not (mes_referencia and filial_selecionada):
        return []

    ano_anterior = ano_selecionado - 1
    resultados_totais = []

    conn = obter_conexao()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        for mes_nome in mes_referencia:
            mes_num = int(nomes_para_numeros[mes_nome])
            ultimo_dia = calendar.monthrange(ano_selecionado, mes_num)[1]

            # Ano selecionado
            data_inicio_atual = f"{ano_selecionado}-{mes_num:02d}-01"
            data_fim_atual = f"{ano_selecionado}-{mes_num:02d}-{ultimo_dia}"

            query = """
                SELECT vlVenda, dtVenda, ? as mes_nome, ? as ano
                FROM tbVendasDashboard
                WHERE dtVenda BETWEEN ? AND ?
                AND nmFilial = ?
                ORDER BY dtVenda
            """
            cursor.execute(query, (mes_nome, ano_selecionado, data_inicio_atual, data_fim_atual, filial_selecionada))
            resultados_totais.extend(cursor.fetchall())

            # Ano anterior
            data_inicio_anterior = f"{ano_anterior}-{mes_num:02d}-01"
            data_fim_anterior = f"{ano_anterior}-{mes_num:02d}-{calendar.monthrange(ano_anterior, mes_num)[1]}"

            cursor.execute(query, (mes_nome, ano_anterior, data_inicio_anterior, data_fim_anterior, filial_selecionada))
            resultados_totais.extend(cursor.fetchall())

        return resultados_totais

    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return []
    finally:
        conn.close()
        
def obter_anos_disponiveis():
    """Retorna uma lista de anos distintos presentes no banco de dados, ordenados em ordem crescente."""
    conn = obter_conexao()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT YEAR(dtVenda) AS ano FROM tbVendasDashboard ORDER BY ano ASC;')  # Mudei para ASC
        anos = [row.ano for row in cursor]
        return anos
    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return []
    finally:
        conn.close()

# Funções que requer ainda utilizar:
def obter_percentual_de_crescimento_atual(filial):
    """Obtém o percentual de diferença entre as vendas do mês atual e o mesmo período do ano anterior, com 2 casas decimais."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH vendas_mes_atual AS (
            SELECT SUM(vlVenda) AS vendas_atual
            FROM tbVendasDashboard
            WHERE 
                YEAR(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN YEAR(DATEADD(MONTH, -1, GETDATE()))
                        ELSE YEAR(GETDATE())
                    END
                AND MONTH(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                        ELSE MONTH(GETDATE())
                    END
                AND nmFilial = ?
        ),
        vendas_mes_ano_anterior AS (
            SELECT SUM(vlVenda) AS vendas_ano_anterior
            FROM tbVendasDashboard
            WHERE 
                YEAR(dtVenda) = YEAR(DATEADD(YEAR, -1, GETDATE()))
                AND MONTH(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                        ELSE MONTH(GETDATE())
                    END
                AND DAY(dtVenda) BETWEEN 1 AND DAY(DATEADD(DAY, -1, GETDATE()))
                AND nmFilial = ?
        )
        SELECT
            CASE
                WHEN vendas_ano_anterior > 0 THEN
                    ROUND(((vendas_atual / vendas_ano_anterior) - 1) * 100.0, 2)
                ELSE NULL
            END AS percentual_diferenca
        FROM vendas_mes_atual, vendas_mes_ano_anterior
        '''
        cursor.execute(consulta, (filial, filial))
        resultado = cursor.fetchone()

        if resultado and resultado[0] is not None:
            return round(resultado[0], 2)
        else:
            return 0.0  # Ou None, se preferir mostrar vazio
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()
        
def obter_percentual_crescimento_meta(filial):
    """Obtém o percentual de diferença entre as vendas do mês atual e a meta (vendas do mesmo período do ano passado +5%)."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH VendasAnoAnterior AS (
            SELECT 
                SUM(vlVenda) * 1.05 AS acumulo_meta_ano_anterior
            FROM dbo.tbVendasDashboard
            WHERE 
                YEAR(dtVenda) = YEAR(DATEADD(YEAR, -1, GETDATE()))  
                AND MONTH(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                        ELSE MONTH(GETDATE())
                    END
                AND DAY(dtVenda) BETWEEN 1 AND DAY(DATEADD(DAY, -1, GETDATE()))  
                AND nmFilial = ?
        ),
        VendasAnoAtual AS (
            SELECT 
                SUM(vlVenda) AS total_ano_atual  
            FROM tbVendasDashboard
            WHERE 
                YEAR(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN YEAR(DATEADD(MONTH, -1, GETDATE()))
                        ELSE YEAR(GETDATE())
                    END
                AND MONTH(dtVenda) = 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                        ELSE MONTH(GETDATE())
                    END
                AND DAY(dtVenda) BETWEEN 1 AND DAY(DATEADD(DAY, -1, GETDATE()))
                AND nmFilial = ?
        )
        SELECT 
            CAST(
                ROUND(
                    ((total_ano_atual / acumulo_meta_ano_anterior) - 1) * 100, 
                    2
                ) AS DECIMAL(10,2)
            ) AS percentual_diferenca
        FROM VendasAnoAtual, VendasAnoAnterior;
        '''
        cursor.execute(consulta, (filial, filial))
        resultado = cursor.fetchone()

        if resultado and resultado[0] is not None:
            return resultado[0]
        else:
            return 0.0

    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()
        
def obter_vendas_anual_e_filial(filial_selecionada):
    """Retorna um dicionário com o total de vendas dos últimos 12 meses para uma filial específica."""
    conn = obter_conexao()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        
        meses = []
        hoje = datetime.today().replace(day=1)
        for i in range(13):
            mes_ref = hoje - relativedelta(months=i)
            ano = mes_ref.year
            mes = mes_ref.month
            meses.append((ano, mes))

        # Cria um dicionário para armazenar os resultados
        vendas_por_mes = {}

        for ano, mes in meses:
            # Pega o último dia do mês de forma precisa
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            data_inicio = f"{ano}-{mes:02d}-01"
            data_fim = f"{ano}-{mes:02d}-{ultimo_dia}"

            consulta = '''
                SELECT SUM(vlVenda) as total
                FROM tbVendasDashboard
                WHERE dtVenda BETWEEN ? AND ?
                  AND nmFilial = ?
            '''
            cursor.execute(consulta, (data_inicio, data_fim, filial_selecionada))
            resultado = cursor.fetchone()
            chave = f"{mes:02d}/{ano}"
            vendas_por_mes[chave] = resultado.total if resultado and resultado.total else 0

        # Ordena por data decrescente (mais recente primeiro)
        vendas_ordenadas = dict(sorted(vendas_por_mes.items(), key=lambda x: datetime.strptime(x[0], "%m/%Y"), reverse=True))
        
        return vendas_ordenadas
    
    except pyodbc.Error as e:
        print(f"Erro ao consultar o banco de dados: {e}")
        return {}
    finally:
        conn.close()
