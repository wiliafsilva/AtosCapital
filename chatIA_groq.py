import groq
import pyodbc
import re

# --- Configurações ---
GROQ_API_KEY = "SUA_CHAVE_API_GROQ"
SQL_SERVER_CONFIG = {
    'server': 'seu_servidor',
    'database': 'seu_banco_de_dados',
    'username': 'seu_usuario',
    'password': 'sua_senha'
}

# --- Funções ---

def conectar_sql_server(config):
    """Conecta ao SQL Server."""
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={config["server"]};'
        f'DATABASE={config["database"]};'
        f'UID={config["username"]};'
        f'PWD={config["password"]};'
    )
    try:
        cnxn = pyodbc.connect(conn_str)
        return cnxn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Erro ao conectar ao SQL Server: {sqlstate}")
        return None

def executar_consulta_sql(conexao, query):
    """Executa uma consulta SQL e retorna os resultados."""
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(query)
            colunas = [column[0] for column in cursor.description]
            resultados = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            return resultados
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            print(f"Erro ao executar a consulta SQL: {sqlstate}")
            return None
        finally:
            cursor.close()
    return None

def obter_resposta_groq(prompt_com_instrucao_sql):
    """Obtém uma resposta da API da Groq com instrução para gerar SQL."""
    client = groq.Groq(api_key=GROQ_API_KEY)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt_com_instrucao_sql}
            ]
        )
        return response.choices[0].message.content
    except groq.APIError as e:
        print(f"Erro na API da Groq: {e}")
        return None

def main():
    """Função principal para interagir com o usuário, Groq e SQL Server."""
    conexao_sql = conectar_sql_server(SQL_SERVER_CONFIG)
    if not conexao_sql:
        return

    while True:
        pergunta_usuario = input("Digite sua pergunta (ou 'sair' para encerrar): ")
        if pergunta_usuario.lower() == 'sair':
            break

        # Criar um prompt com instrução para gerar SQL e uma resposta concisa
        prompt_com_instrucao_sql = f"""Você tem acesso a um banco de dados SQL Server com os seguintes dados:
        Tabela: tbVendasDashboard
        Colunas:
        - idVendas (PK, int, não nulo)
        - nrCNPJ (char(14), não nulo)
        - nmFilial (varchar(50), não nulo)
        - dtVenda (date, não nulo)
        - vlVenda (numeric(13,2), nulo)
        - txMeta (numeric(4,2), não nulo)

        Tente gerar uma consulta SQL para responder à seguinte pergunta. Se a consulta for bem-sucedida e retornar resultados, forneça uma resposta concisa e amigável ao usuário, apresentando os dados de forma clara. Se a pergunta não puder ser respondida com uma consulta SQL, responda normalmente:
        '{pergunta_usuario}'"""

        # Obter resposta da Groq
        resposta_groq = obter_resposta_groq(prompt_com_instrucao_sql)
        if resposta_groq:
            print("Resposta da IA:")
            match = re.search(r"```sql\n(.*?)\n```", resposta_groq, re.DOTALL)
            if match:
                consulta_sql = match.group(1).strip()
                resultados_sql = executar_consulta_sql(conexao_sql, consulta_sql)
                if resultados_sql:
                    if resultados_sql:
                        if len(resultados_sql) == 1:
                            # Tentar formatar a resposta com base no conteúdo da primeira linha
                            primeiro_resultado = resultados_sql[0]
                            if 'nmFilial' in primeiro_resultado and 'TotalVendas' in primeiro_resultado:
                                data_pesquisada = re.search(r"(\d{4}-\d{2}-\d{2})", pergunta_usuario)
                                data_formatada = data_pesquisada.group(1) if data_pesquisada else "data pesquisada"
                                print(f"Claro! A filial que mais vendeu na data {data_formatada} foi a {primeiro_resultado['nmFilial']}")
                                if len(primeiro_resultado) > 1:
                                    print("Total de vendas:", primeiro_resultado['TotalVendas'])
                            elif 'QuantidadeFiliais' in primeiro_resultado:
                                print(f"Você tem {primeiro_resultado['QuantidadeFiliais']} filiais cadastradas.")
                            elif 'dtVenda' in primeiro_resultado and 'TotalVendas' in primeiro_resultado:
                                print(f"O dia com o maior número de vendas foi {primeiro_resultado['dtVenda']} com um total de {primeiro_resultado['TotalVendas']}.")
                            else:
                                # Resposta genérica se não corresponder aos padrões conhecidos
                                print("Com base nos dados, temos:")
                                for key, value in primeiro_resultado.items():
                                    print(f"{key}: {value}")
                        elif len(resultados_sql) > 1:
                            print("Resultados encontrados:")
                            for row in resultados_sql:
                                print(row)
                        else:
                            print("Nenhum resultado encontrado para a consulta.")
                else:
                    print("Nenhum resultado encontrado para a consulta.")
            else:
                print(resposta_groq)
        else:
            print("Erro ao obter resposta da IA.")

    if conexao_sql:
        conexao_sql.close()
        print("Conexão com o SQL Server encerrada.")

if __name__ == "__main__":
    main()