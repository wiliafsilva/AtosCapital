import pyodbc
from query_sql_ia import generate_sql

# 1) String de conexão
sql_server = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=aquidaba.infonet.com.br;'
    'DATABASE=dbproinfo;'
    'UID=leituraVendas;'
    'PWD=KRphDP65BM;'
)

def get_conection():
    """Estabelece e retorna a conexão com o SQL Server."""
    try:
        return pyodbc.connect(sql_server)
    except pyodbc.Error as e:
        print(f"[ERRO CONEXÃO] {e}")
        return None

def execute_sql_command(sql: str):
    """
    Executa a query SQL passada e retorna todas as linhas.
    Cada linha é uma tupla de colunas.
    """
    conn = get_conection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        # Para SELECT, fetchall; para DML, você pode commitar:
        # conn.commit()
        return cursor.fetchall()
    except pyodbc.Error as e:
        print(f"[ERRO EXECUÇÃO] {e}")
        return []
    finally:
        conn.close()