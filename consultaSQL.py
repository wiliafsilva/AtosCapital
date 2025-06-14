#Conxão com o banco
import calendar
from datetime import datetime, timedelta
from matplotlib.dates import relativedelta
import pandas as pd
import pyodbc
from decimal import Decimal

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

def obter_vendas_ano_anterior(filial):
    """Executa a consulta para obter o total de vendas do mesmo período do ano anterior para a filial especificada."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
            WITH dados_referencia AS (
                SELECT 
                    MONTH(CASE 
                              WHEN EXISTS (
                                  SELECT 1 
                                  FROM tbVendasDashboard 
                                  WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                    AND MONTH(dtVenda) = 
                                        CASE 
                                            WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                            ELSE MONTH(GETDATE())
                                        END
                                    AND vlVenda IS NOT NULL
                                    AND nmFilial = ?
                              )
                              THEN GETDATE()
                              ELSE DATEADD(MONTH, -1, GETDATE())
                         END) AS mes_referencia,
                    YEAR(CASE 
                              WHEN EXISTS (
                                  SELECT 1 
                                  FROM tbVendasDashboard 
                                  WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                    AND MONTH(dtVenda) = 
                                        CASE 
                                            WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                            ELSE MONTH(GETDATE())
                                        END
                                    AND vlVenda IS NOT NULL
                                    AND nmFilial = ?
                              )
                              THEN GETDATE()
                              ELSE DATEADD(MONTH, -1, GETDATE())
                         END) AS ano_referencia
            )

            SELECT SUM(vlVenda) AS total_vendas_ano_anterior
            FROM tbVendasDashboard, dados_referencia
            WHERE YEAR(dtVenda) = ano_referencia - 1
              AND MONTH(dtVenda) = mes_referencia
              AND nmFilial = ?
        '''
        cursor.execute(consulta, (filial, filial, filial))
        resultado = cursor.fetchone()
        if resultado and resultado.total_vendas_ano_anterior is not None:
            return resultado.total_vendas_ano_anterior
        else:
            return 0  # Caso não haja vendas
    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        conn.close()

def obter_meta_mes(filial):
    """Obtém a meta de vendas (vendas do mesmo mês do ano anterior + 5%) para uma filial específica."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH dados_referencia AS (
            SELECT 
                MONTH(CASE 
                          WHEN EXISTS (
                              SELECT 1 
                              FROM tbVendasDashboard 
                              WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                          )
                          THEN GETDATE()
                          ELSE DATEADD(MONTH, -1, GETDATE())
                     END) AS mes_referencia,
                YEAR(CASE 
                          WHEN EXISTS (
                              SELECT 1 
                              FROM tbVendasDashboard 
                              WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                          )
                          THEN GETDATE()
                          ELSE DATEADD(MONTH, -1, GETDATE())
                     END) AS ano_referencia
        )

        SELECT 
            SUM(vlVenda) * 1.05 AS meta_mes
        FROM tbVendasDashboard, dados_referencia
        WHERE YEAR(dtVenda) = ano_referencia - 1
          AND MONTH(dtVenda) = mes_referencia
          AND nmFilial = ?
        '''
        # Passa o mesmo parâmetro 3 vezes: para os dois EXISTS e para o filtro final
        cursor.execute(consulta, (filial, filial, filial))
        resultado = cursor.fetchone()
        return resultado.meta_mes if resultado and resultado.meta_mes else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()

def obter_previsao_vendas(filial):
    """Calcula a previsão de vendas do mês atual para uma filial específica."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
            SELECT
                CAST(
                    (
                        SUM(vlVenda) / 
                        CAST(COUNT(DISTINCT CONVERT(DATE, CASE WHEN vlVenda IS NOT NULL THEN dtVenda END)) AS FLOAT)
                    ) *
                    CAST(
                        DAY(DATEADD(DAY, -1, DATEADD(MONTH, 1, CAST(CAST(YEAR(GETDATE()) AS VARCHAR) + '-' + 
                            RIGHT('0' + CAST(MONTH(GETDATE()) AS VARCHAR), 2) + '-01' AS DATE)))) AS FLOAT
                    )
                AS DECIMAL(10,2)) AS previsao_vendas
            FROM tbVendasDashboard
            WHERE
                dtVenda >= 
                    CASE 
                        WHEN DAY(GETDATE()) = 1 THEN 
                            CAST(YEAR(DATEADD(MONTH, -1, GETDATE())) AS VARCHAR) + '-' +
                            RIGHT('0' + CAST(MONTH(DATEADD(MONTH, -1, GETDATE())) AS VARCHAR), 2) + '-01'
                        ELSE
                            CAST(YEAR(GETDATE()) AS VARCHAR) + '-' +
                            RIGHT('0' + CAST(MONTH(GETDATE()) AS VARCHAR), 2) + '-01'
                    END
                AND dtVenda <= (
                    SELECT MAX(dtVenda)
                    FROM tbVendasDashboard
                    WHERE 
                        YEAR(dtVenda) = YEAR(GETDATE())
                        AND MONTH(dtVenda) = MONTH(GETDATE())
                        AND dtVenda < GETDATE()
                        AND nmFilial = ?
                )
                AND nmFilial = ?
        '''
        cursor.execute(consulta, (filial, filial))
        resultado = cursor.fetchone()
        return resultado.previsao_vendas if resultado and resultado.previsao_vendas is not None else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()
       
def acumulo_vendas_periodo_ano_anterior(filial):
    """Obtém as vendas do mesmo período do ano anterior para uma filial específica."""
    conn = obter_conexao()
    if conn is None:
        return 0  # Retorna 0 caso a conexão falhe

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH dados_referencia AS (
            SELECT 
                MONTH(CASE 
                          WHEN EXISTS (
                              SELECT 1 
                              FROM tbVendasDashboard 
                              WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                          )
                          THEN GETDATE()
                          ELSE DATEADD(MONTH, -1, GETDATE())
                     END) AS mes_referencia,
                YEAR(CASE 
                          WHEN EXISTS (
                              SELECT 1 
                              FROM tbVendasDashboard 
                              WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                          )
                          THEN GETDATE()
                          ELSE DATEADD(MONTH, -1, GETDATE())
                     END) AS ano_referencia
        ),
        DiasValidos AS (
            SELECT DISTINCT DAY(dtVenda) AS dia
            FROM dbo.tbVendasDashboard, dados_referencia
            WHERE 
                MONTH(dtVenda) = dados_referencia.mes_referencia
                AND YEAR(dtVenda) = YEAR(GETDATE())
                AND dtVenda <= GETDATE()
                AND vlVenda IS NOT NULL
                AND nmFilial = ?
        ),
        AcumuloAnoAnterior AS (
            SELECT 
                vlVenda
            FROM dbo.tbVendasDashboard, dados_referencia
            WHERE 
                MONTH(dtVenda) = dados_referencia.mes_referencia
                AND YEAR(dtVenda) = dados_referencia.ano_referencia - 1
                AND vlVenda IS NOT NULL
                AND nmFilial = ?
                AND DAY(dtVenda) IN (
                    SELECT dia FROM DiasValidos
                )
        )
        SELECT 
            CASE 
                WHEN DAY(GETDATE()) = 1 THEN 
                    (
                        SELECT SUM(vlVenda)
                        FROM dbo.tbVendasDashboard, dados_referencia
                        WHERE 
                            MONTH(dtVenda) = dados_referencia.mes_referencia
                            AND YEAR(dtVenda) = dados_referencia.ano_referencia - 1
                            AND vlVenda IS NOT NULL
                            AND nmFilial = ?
                    )
                ELSE 
                    (
                        SELECT SUM(vlVenda)
                        FROM AcumuloAnoAnterior
                    )
            END AS acumulo_vendas_ano_anterior;
        '''
        # O parâmetro é usado 5 vezes na query
        cursor.execute(consulta, (filial, filial, filial, filial, filial))
        resultado = cursor.fetchone()

        # Verifica se resultado é None e retorna 0
        return resultado[0] if resultado and resultado[0] is not None else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return 0  # Retorna 0 em caso de erro
    finally:
        conn.close()

def obter_acumulo_meta_ano_anterior(filial):
    """Obtém o acúmulo de meta (vendas do mês anterior + 5%) para uma filial específica, com base no mesmo período do ano anterior."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH dados_referencia AS (
            SELECT 
                MONTH(CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM tbVendasDashboard 
                            WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                        )
                        THEN GETDATE()
                        ELSE DATEADD(MONTH, -1, GETDATE())
                    END) AS mes_referencia,
                YEAR(CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM tbVendasDashboard 
                            WHERE YEAR(dtVenda) = YEAR(GETDATE())
                                AND MONTH(dtVenda) = 
                                    CASE 
                                        WHEN DAY(GETDATE()) = 1 THEN MONTH(DATEADD(MONTH, -1, GETDATE()))
                                        ELSE MONTH(GETDATE())
                                    END
                                AND vlVenda IS NOT NULL
                                AND nmFilial = ?
                        )
                        THEN GETDATE()
                        ELSE DATEADD(MONTH, -1, GETDATE())
                    END) AS ano_referencia
        ),
        DiasValidos AS (
            SELECT DISTINCT DAY(dtVenda) AS dia
            FROM dbo.tbVendasDashboard, dados_referencia
            WHERE 
                MONTH(dtVenda) = dados_referencia.mes_referencia
                AND YEAR(dtVenda) = YEAR(GETDATE())
                AND dtVenda <= GETDATE()
                AND vlVenda IS NOT NULL
                AND nmFilial = ?
        ),
        AcumuloAnoAnterior AS (
            SELECT 
                vlVenda
            FROM dbo.tbVendasDashboard, dados_referencia
            WHERE 
                MONTH(dtVenda) = dados_referencia.mes_referencia
                AND YEAR(dtVenda) = dados_referencia.ano_referencia - 1
                AND vlVenda IS NOT NULL
                AND nmFilial = ?
                AND DAY(dtVenda) IN (
                    SELECT dia FROM DiasValidos
                )
        )
        SELECT 
            CASE 
                WHEN DAY(GETDATE()) = 1 THEN 
                    (
                        SELECT SUM(vlVenda) * 1.05
                        FROM dbo.tbVendasDashboard, dados_referencia
                        WHERE 
                            MONTH(dtVenda) = dados_referencia.mes_referencia
                            AND YEAR(dtVenda) = dados_referencia.ano_referencia - 1
                            AND vlVenda IS NOT NULL
                            AND nmFilial = ?
                    )
                ELSE 
                    (
                        SELECT SUM(vlVenda) * 1.05
                        FROM AcumuloAnoAnterior
                    )
            END AS acumulo_meta_ano_anterior;
        '''
        # O parâmetro é usado 5 vezes na query
        cursor.execute(consulta, (filial, filial, filial, filial, filial))
        resultado = cursor.fetchone()
        return resultado.acumulo_meta_ano_anterior if resultado else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()

def obter_acumulo_de_vendas(filial):
    """Obtém o acúmulo de vendas do mês atual para uma filial específica.
    Se não houver dados no mês atual, retorna os dados do mês anterior.
    """
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        consulta = '''
        WITH VendasMesAtual AS (
            SELECT SUM(vlVenda) AS acumulo_de_vendas
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
        ),
        VendasMesAnterior AS (
            SELECT SUM(vlVenda) AS acumulo_de_vendas
            FROM dbo.tbVendasDashboard
            WHERE 
                YEAR(dtVenda) = YEAR(DATEADD(MONTH, -1, GETDATE()))
              AND MONTH(dtVenda) = MONTH(DATEADD(MONTH, -1, GETDATE()))
              AND nmFilial = ?
        )
        SELECT 
            COALESCE(VendasMesAtual.acumulo_de_vendas, VendasMesAnterior.acumulo_de_vendas) AS acumulo_de_vendas
        FROM 
            VendasMesAtual, VendasMesAnterior;
        '''
        cursor.execute(consulta, (filial, filial))
        resultado = cursor.fetchone()
        return resultado.acumulo_de_vendas if resultado and resultado.acumulo_de_vendas is not None else 0
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()

def obter_ultima_venda_com_valor(filial):
    """Obtém a última venda com valor do mês atual ou, se não houver, dos meses anteriores para uma filial específica."""
    conn = obter_conexao()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        consulta = '''
        SELECT TOP 1
            vlVenda,
            dtVenda,
            nmFilial
        FROM tbVendasDashboard
        WHERE YEAR(dtVenda) = YEAR(GETDATE())  -- Ano atual
          AND MONTH(dtVenda) <= MONTH(GETDATE())  -- Meses anteriores e o mês atual
          AND nmFilial = ?  -- Filial específica
          AND vlVenda IS NOT NULL  -- Garantir que a venda tenha um valor
        ORDER BY dtVenda DESC;  -- Ordena pela data de venda mais recente
        '''
        cursor.execute(consulta, (filial,))
        resultado = cursor.fetchone()
        
        if resultado and resultado.vlVenda is not None:
            return resultado.vlVenda, resultado.dtVenda  # Retorna o valor da última venda com valor
        else:
            return (0, None)  # Retorna 0 se não houver vendas com valor para o mês atual ou anteriores
    except pyodbc.Error as e:
        print(f"Erro: {e}")
        return None
    finally:
        conn.close()

def obter_percentual_de_crescimento_atual(filial):
    atual = obter_acumulo_de_vendas(filial)
    ano_anterior = acumulo_vendas_periodo_ano_anterior(filial)

    if ano_anterior == 0:
        return None  # Evita divisão por zero

    percentual = ((atual / ano_anterior) - 1) * 100
    return percentual

def obter_percentual_crescimento_meta(filial):
    """Calcula o percentual de crescimento das vendas em relação à meta do ano anterior (com 5% de acréscimo)."""
    try:
        vendas = obter_acumulo_de_vendas(filial)
        meta = obter_acumulo_meta_ano_anterior(filial)

        if meta == 0:
            return 0  # Evita divisão por zero

        percentual = ((vendas / meta) - 1) * 100
        return percentual
    except Exception as e:
        print(f"Erro ao calcular percentual de crescimento: {e}")
        return None

def obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada):
    nomes_para_numeros = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }

    numeros_para_nomes = {v: k for k, v in nomes_para_numeros.items()}

    if not (mes_referencia and filial_selecionada):
        return []

    data_base = datetime.now() - timedelta(days=1)
    ano_base = data_base.year

    resultados_totais = []

    conn = obter_conexao()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        for mes_nome in mes_referencia:
            mes_num = nomes_para_numeros.get(mes_nome)
            if not mes_num:
                print(f"Erro: Mês '{mes_nome}' inválido. Pulando.")
                continue

            # Tentativa 1: mês atual
            ultimo_dia = calendar.monthrange(ano_base, mes_num)[1]
            data_inicio = f"{ano_base}-{mes_num:02d}-01"
            data_fim = f"{ano_base}-{mes_num:02d}-{ultimo_dia}"

            query = """
                SELECT vlVenda, dtVenda, ? as mes_nome, ? as ano
                FROM tbVendasDashboard
                WHERE dtVenda BETWEEN ? AND ?
                AND nmFilial = ?
                ORDER BY dtVenda
            """
            cursor.execute(query, (mes_nome, ano_base, data_inicio, data_fim, filial_selecionada))
            resultados = cursor.fetchall()

            # Se não houver dados no mês atual, tenta o mês anterior
            if not resultados:
                mes_anterior = mes_num - 1
                ano_anterior_mes = ano_base

                if mes_anterior == 0:
                    mes_anterior = 12
                    ano_anterior_mes -= 1

                mes_anterior_nome = numeros_para_nomes[mes_anterior]
                ultimo_dia_ant = calendar.monthrange(ano_anterior_mes, mes_anterior)[1]
                data_inicio_ant = f"{ano_anterior_mes}-{mes_anterior:02d}-01"
                data_fim_ant = f"{ano_anterior_mes}-{mes_anterior:02d}-{ultimo_dia_ant}"

                cursor.execute(query, (mes_anterior_nome, ano_anterior_mes, data_inicio_ant, data_fim_ant, filial_selecionada))
                resultados = cursor.fetchall()

            resultados_totais.extend(resultados)

            # Busca também para o mesmo mês do ano anterior
            ano_anterior = ano_base - 1
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

"""Dash mês anterior"""   
 
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


def obter_vendas_por_mes_e_filial_mes_anterior(mes_referencia, filial_selecionada, ano_selecionado):
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
        
def obter_vendas_anual_e_filial_mes_anterior(filial_selecionada, mes=None, ano=None):
    """
    Retorna um dicionário com o total de vendas dos últimos 12 meses para uma filial específica,
    com base no mês e ano fornecidos. Se não forem informados, considera o mês atual.
    """
    conn = obter_conexao()
    if conn is None:
        return {}

    try:
        cursor = conn.cursor()

        # Se mês e ano não forem informados, usa o mês atual
        if mes is None or ano is None:
            hoje = datetime.today().replace(day=1)
        else:
            hoje = datetime(year=ano, month=mes, day=1)

        # Gera os últimos 12 meses a partir da data de referência
        meses = []
        for i in range(12):
            mes_ref = hoje - relativedelta(months=i)
            meses.append((mes_ref.year, mes_ref.month))

        vendas_por_mes = {}

        for ano_item, mes_item in meses:
            ultimo_dia = calendar.monthrange(ano_item, mes_item)[1]
            data_inicio = f"{ano_item}-{mes_item:02d}-01"
            data_fim = f"{ano_item}-{mes_item:02d}-{ultimo_dia}"

            consulta = '''
                SELECT SUM(vlVenda) as total
                FROM tbVendasDashboard
                WHERE dtVenda BETWEEN ? AND ?
                  AND nmFilial = ?
            '''
            cursor.execute(consulta, (data_inicio, data_fim, filial_selecionada))
            resultado = cursor.fetchone()
            chave = f"{mes_item:02d}/{ano_item}"
            vendas_por_mes[chave] = resultado.total if resultado and resultado.total else 0

        # Ordena por data crescente (do mais antigo para o mais recente)
        vendas_ordenadas = dict(sorted(vendas_por_mes.items(), key=lambda x: datetime.strptime(x[0], "%m/%Y")))

        return vendas_ordenadas

    except pyodbc.Error as e:
        print(f"Erro ao consultar o banco de dados: {e}")
        return {}
    finally:
        conn.close()
        
def obter_percentual_crescimento_meta_mes_anterior(filial):
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


#Relatório única quary

def obter_relatorio_vendas(data_usuario):
    """Executa a consulta e retorna os dados do relatório de vendas por filial."""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        if isinstance(data_usuario, str):
            data_sql = data_usuario
        else:
            data_sql = data_usuario.strftime('%Y-%m-%d')

        consulta = f"""
        DECLARE @data_usuario DATE = '{data_sql}'; -- Data escolhida pelo usuário (04-06-25)

        DECLARE @data_inicio DATE = CASE WHEN DAY(@data_usuario) = 1 
                                  THEN DATEADD(MONTH, -1, CAST(CONVERT(VARCHAR(6), YEAR(@data_usuario)) + RIGHT('0' + CONVERT(VARCHAR(2), MONTH(@data_usuario)), 2) + '01' AS DATE)) 
                                  ELSE CAST(CONVERT(VARCHAR(6), YEAR(@data_usuario)) + RIGHT('0' + CONVERT(VARCHAR(2), MONTH(@data_usuario)), 2) + '01' AS DATE) 
                             END; 

        -- RESTANTE DA QUERY ORIGINAL (MANTIDA EXATAMENTE COMO ESTÁ)
        WITH MaxDatas AS ( 
            SELECT nmFilial, MAX(dtVenda) AS max_dtVenda 
            FROM tbVendasDashboard 
            WHERE dtVenda >= @data_inicio AND dtVenda < CAST(@data_usuario AS DATE) AND vlVenda IS NOT NULL 
            GROUP BY nmFilial 
        ), 
        Previsao AS ( 
            SELECT v.nmFilial, 
                   'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(SUM(v.vlVenda) / NULLIF(COUNT(DISTINCT CONVERT(VARCHAR, v.dtVenda, 112)), 0) * 
                          DAY(DATEADD(DAY, -1, DATEADD(MONTH, 1, @data_inicio))) AS MONEY), 1), '.', ','), ',', '.') AS previsao_vendas 
            FROM tbVendasDashboard v 
            INNER JOIN MaxDatas md ON v.nmFilial = md.nmFilial 
            WHERE v.dtVenda >= @data_inicio AND v.dtVenda <= md.max_dtVenda AND v.vlVenda IS NOT NULL 
            GROUP BY v.nmFilial 
        ),
        VendasMesAnterior AS (
            SELECT 
                nmFilial,
                SUM(vlVenda) AS total_mes_anterior,
                'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(SUM(vlVenda) AS MONEY), 1), '.', ','), ',', '.') AS vendas_2024,
                'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(SUM(vlVenda) * 1.05 AS MONEY), 1), '.', ','), ',', '.') AS meta_mes
            FROM tbVendasDashboard
            WHERE YEAR(dtVenda) = YEAR(DATEADD(YEAR, -1, @data_usuario))
            AND MONTH(dtVenda) = CASE WHEN DAY(@data_usuario) = 1 
                                      THEN MONTH(DATEADD(MONTH, -1, @data_usuario)) 
                                      ELSE MONTH(@data_usuario) 
                                 END
            AND vlVenda IS NOT NULL
            GROUP BY nmFilial
        ),
        UltimaVendaAtual AS ( 
            SELECT t1.nmFilial, 
                   MAX(t1.dtVenda) AS ultima_data,
                   'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(t1.vlVenda AS MONEY), 1), '.', ','), ',', '.') AS vlVenda 
            FROM tbVendasDashboard t1 
            INNER JOIN ( 
                SELECT 
                    v.nmFilial, 
                    MAX(v.dtVenda) AS ultima_data 
                FROM tbVendasDashboard v
                WHERE v.vlVenda IS NOT NULL 
                  AND v.dtVenda < @data_usuario
                  AND v.dtVenda >= @data_inicio
                GROUP BY v.nmFilial 
            ) t2 ON t1.nmFilial = t2.nmFilial AND t1.dtVenda = t2.ultima_data AND t1.vlVenda IS NOT NULL
            GROUP BY t1.nmFilial, t1.vlVenda
        ),
        AcumuladoVendas AS ( 
            SELECT u.nmFilial, 
                   'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(SUM(v.vlVenda) AS MONEY), 1), '.', ','), ',', '.') AS acumulado_vendas,
                   SUM(v.vlVenda) AS valor_acumulado
            FROM UltimaVendaAtual u
            LEFT JOIN tbVendasDashboard v ON u.nmFilial = v.nmFilial 
                                        AND v.dtVenda >= @data_inicio 
                                        AND v.dtVenda <= u.ultima_data
                                        AND v.vlVenda IS NOT NULL
            GROUP BY u.nmFilial 
        ),
        UltimaVendaAnoAnterior AS (
            SELECT t1.nmFilial,
                   MAX(t1.dtVenda) AS ultima_data_anterior
            FROM tbVendasDashboard t1
            INNER JOIN (
                SELECT 
                    v.nmFilial,
                    MAX(v.dtVenda) AS ultima_data
                FROM tbVendasDashboard v
                WHERE v.vlVenda IS NOT NULL
                  AND v.dtVenda < DATEADD(YEAR, -1, @data_usuario)
                  AND v.dtVenda >= DATEADD(YEAR, -1, @data_inicio)
                GROUP BY v.nmFilial
            ) t2 ON t1.nmFilial = t2.nmFilial AND t1.dtVenda = t2.ultima_data AND t1.vlVenda IS NOT NULL
            GROUP BY t1.nmFilial
        ),
        Acumulo AS ( 
            SELECT u.nmFilial, 
                   'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(SUM(v.vlVenda) AS MONEY), 1), '.', ','), ',', '.') AS acumulo_2024,
                   SUM(v.vlVenda) AS valor_acumulo_2024
            FROM UltimaVendaAnoAnterior u
            LEFT JOIN tbVendasDashboard v ON u.nmFilial = v.nmFilial 
                                        AND v.dtVenda >= DATEADD(YEAR, -1, @data_inicio)
                                        AND v.dtVenda <= u.ultima_data_anterior
                                        AND v.vlVenda IS NOT NULL
            GROUP BY u.nmFilial 
        ),
        AcumuloMeta AS ( 
            SELECT a.nmFilial, 
                   'R$ ' + REPLACE(REPLACE(CONVERT(VARCHAR, CAST(a.valor_acumulo_2024 * 1.05 AS MONEY), 1), '.', ','), ',', '.') AS acumulo_meta 
            FROM Acumulo a
        ),
        Crescimento AS ( 
            SELECT a.nmFilial, 
                   REPLACE(STR(ROUND(((av.valor_acumulado / NULLIF(a.valor_acumulo_2024, 0)) - 1) * 100, 2), 10, 2), ' ', '') + '%' AS cresc_vs_ano_anterior 
            FROM Acumulo a
            JOIN AcumuladoVendas av ON a.nmFilial = av.nmFilial 
            WHERE a.valor_acumulo_2024 IS NOT NULL AND a.valor_acumulo_2024 <> 0 
        ),
        VendasAnoAtualMeta AS ( 
            SELECT nmFilial, SUM(vlVenda) AS total_ano_atual 
            FROM dbo.tbVendasDashboard 
            WHERE YEAR(dtVenda) = CASE WHEN DAY(@data_usuario) = 1 THEN YEAR(DATEADD(MONTH, -1, @data_usuario)) ELSE YEAR(@data_usuario) END 
            AND MONTH(dtVenda) = CASE WHEN DAY(@data_usuario) = 1 THEN MONTH(DATEADD(MONTH, -1, @data_usuario)) ELSE MONTH(@data_usuario) END 
            AND DAY(dtVenda) BETWEEN 1 AND DAY(DATEADD(DAY, -1, @data_usuario)) 
            GROUP BY nmFilial 
        ), 
        CrescimentoMeta AS ( 
            SELECT a.nmFilial, 
                   REPLACE(STR(ROUND(((a.total_ano_atual / NULLIF(am.valor_acumulo_2024 * 1.05, 0)) - 1) * 100, 2), 10, 2), ' ', '') + '%' AS cresc_meta 
            FROM VendasAnoAtualMeta a 
            JOIN Acumulo am ON a.nmFilial = am.nmFilial 
            WHERE am.valor_acumulo_2024 IS NOT NULL AND am.valor_acumulo_2024 <> 0 
        ) 
        SELECT f.nmFilial, 
               ISNULL(vm.vendas_2024, 'R$ 0,00') AS vendas_2024, 
               ISNULL(vm.meta_mes, 'R$ 0,00') AS meta_mes, 
               ISNULL(p.previsao_vendas, 'R$ 0,00') AS previsao_vendas, 
               ISNULL(a.acumulo_2024, 'R$ 0,00') AS acumulo_2024, 
               ISNULL(am.acumulo_meta, 'R$ 0,00') AS acumulo_meta, 
               ISNULL(av.acumulado_vendas, 'R$ 0,00') AS acumulado_vendas, 
               ISNULL(u.vlVenda, 'R$ 0,00') AS ultima_venda_valor, 
               ISNULL(c.cresc_vs_ano_anterior, '0,00%') AS crescimento_vs_ano_anterior, 
               ISNULL(cm.cresc_meta, '0,00%') AS crescimento_vs_meta 
        FROM (SELECT DISTINCT nmFilial FROM tbVendasDashboard) f 
        LEFT JOIN VendasMesAnterior vm ON f.nmFilial = vm.nmFilial
        LEFT JOIN Previsao p ON f.nmFilial = p.nmFilial 
        LEFT JOIN Acumulo a ON f.nmFilial = a.nmFilial 
        LEFT JOIN AcumuloMeta am ON f.nmFilial = am.nmFilial 
        LEFT JOIN AcumuladoVendas av ON f.nmFilial = av.nmFilial 
        LEFT JOIN UltimaVendaAtual u ON f.nmFilial = u.nmFilial 
        LEFT JOIN Crescimento c ON f.nmFilial = c.nmFilial 
        LEFT JOIN CrescimentoMeta cm ON f.nmFilial = cm.nmFilial 
        GROUP BY f.nmFilial, vm.vendas_2024, vm.meta_mes, p.previsao_vendas, a.acumulo_2024, am.acumulo_meta, av.acumulado_vendas, u.vlVenda, c.cresc_vs_ano_anterior, cm.cresc_meta 
        ORDER BY f.nmFilial;
        """

        df = pd.read_sql(consulta, conn)
        return df

    except pyodbc.Error as e:
        print(f"Erro ao executar a consulta: {e}")
        return None
    finally:
        conn.close()

def obter_data_ultima_venda(data_usuario):
    """Obtém a data da última venda registrada antes da data selecionada"""
    conn = obter_conexao()
    if conn is None:
        return None

    try:
        data_sql = data_usuario.strftime('%Y-%m-%d') if not isinstance(data_usuario, str) else data_usuario
        
        consulta = f"""
        SELECT MAX(dtVenda) AS data_ultima_venda
        FROM tbVendasDashboard
        WHERE dtVenda < '{data_sql}' AND vlVenda IS NOT NULL
        """
        
        df = pd.read_sql(consulta, conn)
        return df['data_ultima_venda'].iloc[0] if not df.empty else None
        
    except pyodbc.Error as e:
        print(f"Erro ao obter data da última venda: {e}")
        return None
    finally:
        conn.close()        
