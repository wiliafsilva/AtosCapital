import spacy
import numpy
from sklearn.metrics.pairwise import cosine_similarity
import pyodbc
import re

# Carregando o modelo spaCy com embeddings grandes
nlp = spacy.load("pt_core_news_lg")

# Função para obter a conexão com o banco de dados (mantenha como estava)
def obter_conexao():
    dados_empresa = (
        'DRIVER={ODBC driver 17 for SQL Server};'
        'SERVER=aquidaba.infonet.com.br;'
        'DATABASE=dbproinfo;'
        'UID=leituraVendas;'
        'PWD=KRphDP65BM;'
    )
    try:
        return pyodbc.connect(dados_empresa)
    except pyodbc.Error as e:
        print(f'Erro ao conectar ao banco de dados: {e}')
        return None

# Função para obter os metadados do banco de dados (mantenha como estava)
def obter_metadados(conexao):
    tabelas = []
    colunas_por_tabela = {}
    if conexao:
        cursor = conexao.cursor()
        try:
            # Obter nomes das tabelas
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = 'dbproinfo'")
            tabelas = [row[0] for row in cursor.fetchall()]

            # Obter nomes das colunas para cada tabela
            for tabela in tabelas:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabela}' AND TABLE_CATALOG = 'dbproinfo'")
                colunas = [row[0] for row in cursor.fetchall()]
                colunas_por_tabela[tabela] = colunas
        except pyodbc.Error as e:
            print(f"Erro ao obter metadados: {e}")
        finally:
            cursor.close()
    return tabelas, colunas_por_tabela

# Função para obter embedding de uma palavra (mantenha como estava)
def get_embedding(word, colunas_metadata):
    vector = nlp(str(word)).vector
    if numpy.all(vector == 0):
        word_lower = word.lower()
        for tabela, colunas in colunas_metadata.items():
            for coluna in colunas:
                coluna_lower = coluna.lower().replace(" ", "")
                if word_lower == coluna_lower:
                    parts = coluna.split()
                    if len(parts) > 1:
                        vectors = [nlp(part).vector for part in parts if not numpy.all(nlp(part).vector == 0)]
                        if vectors:
                            return numpy.mean(vectors, axis=0)
                    elif word_lower == "nmfilial":
                        return numpy.mean([nlp("nome").vector, nlp("filial").vector], axis=0)
                    elif word_lower == "vlvenda":
                        return numpy.mean([nlp("valor").vector, nlp("venda").vector], axis=0)
                    elif word_lower == "idvendas":
                        return numpy.mean([nlp("id").vector, nlp("vendas").vector], axis=0)
                    elif word_lower == "nrcnpj":
                        return numpy.mean([nlp("numero").vector, nlp("cnpj").vector], axis=0)
                    elif word_lower == "dtvenda":
                        return numpy.mean([nlp("data").vector, nlp("venda").vector], axis=0)
                    elif word_lower == "txmeta":
                        return numpy.mean([nlp("taxa").vector, nlp("meta").vector], axis=0)
    return vector

# Consulta do usuário
consulta = str(input('Digite a sua consulta: '))
doc_consulta = nlp(consulta)
print("Entidades Detectadas:", [(ent.text, ent.label_) for ent in doc_consulta.ents])

# Obter conexão e metadados (mantenha como estava)
conexao = obter_conexao()
tabelas_metadata, colunas_metadata = obter_metadados(conexao)

if not tabelas_metadata:
    print("Não foram encontradas tabelas no banco de dados.")
else:
    tabela_selecionada = tabelas_metadata[0] # Assumindo a primeira tabela

    # Encontrar colunas relevantes (mantenha a lógica atual por enquanto)
    colunas_selecionadas = set()
    limiar_padrao = 0.2
    limiar_vendas = 0.58

    for token in doc_consulta:
        if token.pos_ in ["NOUN", "ADJ"]:
            melhor_similaridade_token = -1
            coluna_mais_similar_token = None
            limiar_atual = limiar_padrao if token.text.lower() != "vendas" else limiar_vendas
            for coluna in colunas_metadata.get(tabela_selecionada, []):
                embedding_token = get_embedding(token.text, colunas_metadata).reshape(1, -1)
                embedding_coluna = get_embedding(coluna, colunas_metadata).reshape(1, -1)
                if not numpy.all(embedding_token == 0) and not numpy.all(embedding_coluna == 0):
                    similarity = cosine_similarity(embedding_token, embedding_coluna)[0][0]
                    if similarity > melhor_similaridade_token and similarity > limiar_atual:
                        melhor_similaridade_token = similarity
                        coluna_mais_similar_token = coluna
            if coluna_mais_similar_token:
                colunas_selecionadas.add(coluna_mais_similar_token)

   # Identificar condição (data) - Priorizando "data" e Refinando Formatos
    condicao_coluna_data = None
    condicao_valor_data = None

    for i, token in enumerate(doc_consulta):
        if token.lower_ == "data" and i + 1 < len(doc_consulta):
            # Tentar pegar o valor da data nos tokens seguintes
            valor_data_str = " ".join([t.text for t in doc_consulta[i + 1:]])
        
            # Verificar por formatos comuns
            data_match = re.search(r'(\d{4}-\d{2}-\d{2})', valor_data_str)
            if data_match:
                condicao_coluna_data = "dtVenda"
                condicao_valor_data = data_match.group(1)
                break

            data_match = re.search(r'(\d{1,2} de \w+ de \d{4})', valor_data_str, re.IGNORECASE)
            if data_match:
                condicao_coluna_data = "dtVenda"
                condicao_valor_data = data_match.group(1)
                # A CONVERSÃO PARA 'YYYY-MM-DD' SERIA IDEAL AQUI
                break

            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', valor_data_str)
            if data_match:
                condicao_coluna_data = "dtVenda"
                condicao_valor_data = data_match.group(1)
                # A CONVERSÃO PARA 'YYYY-MM-DD' SERIA IDEAL AQUI
                break

    # Se nenhuma data for encontrada pela busca por "data", verificar entidades DATE
    if not condicao_coluna_data:
        for ent in doc_consulta.ents:
            if ent.label_ == "DATE":
                condicao_coluna_data = "dtVenda"
                condicao_valor_data = str(ent.text)
                break

    # Verificar se a consulta pede agregação ("mais vendeu")
    if "mais vendeu" in consulta.lower():
        script_sql = f"SELECT TOP 1 nmFilial, SUM(vlVenda) AS total_vendas FROM {tabela_selecionada}"
        if condicao_coluna_data and condicao_valor_data:
            script_sql += f" WHERE {condicao_coluna_data} = '{condicao_valor_data}'"
        script_sql += " GROUP BY nmFilial ORDER BY total_vendas DESC"
    else:
        # Consulta padrão (sem agregação) - Manter a lógica anterior
        script_sql = f"SELECT {', '.join(colunas_selecionadas)} FROM {tabela_selecionada}"
        if condicao_coluna_data and condicao_valor_data:
            script_sql += f" WHERE {condicao_coluna_data} = '{condicao_valor_data}'"

    print("SQL Gerado:", script_sql)

    # Executar a consulta e obter os resultados (mantenha como estava)
    if conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(script_sql)
            resultados = cursor.fetchall()
            colunas_nomes = [column[0] for column in cursor.description]
            print("\nResultados:")
            if resultados:
                print(colunas_nomes)
                for row in resultados:
                    print(row)
            else:
                print("Nenhum resultado encontrado.")
        except pyodbc.Error as e:
            print(f"Erro ao executar a consulta: {e}")
        finally:
            cursor.close()
        conexao.close()

    # --- Blocos de depuração (mantenha como estavam) ---
    print("\n--- Vetores para algumas palavras ---")
    print(f"Vetor para 'nmFilial': {get_embedding('nmFilial', colunas_metadata)[:5]}")
    print(f"Vetor para 'vlVenda': {get_embedding('vlVenda', colunas_metadata)[:5]}")
    print(f"Vetor para 'dtVenda': {get_embedding('dtVenda', colunas_metadata)[:5]}")

    print("\n--- Similaridades entre tokens da consulta e colunas ---")
    for token in doc_consulta:
        if token.pos_ in ["NOUN", "ADJ"]:
            print(f"\nToken: {token.text}")
            melhor_similaridade_token_debug = -1
            coluna_mais_similar_token_debug = None
            limiar_atual_debug = limiar_padrao if token.text.lower() != "vendas" else limiar_vendas
            for coluna in colunas_metadata.get(tabela_selecionada, []):
                embedding_token = get_embedding(token.text, colunas_metadata).reshape(1, -1)
                embedding_coluna = get_embedding(coluna, colunas_metadata).reshape(1, -1)
                if not numpy.all(embedding_token == 0) and not numpy.all(embedding_coluna == 0):
                    similarity = cosine_similarity(embedding_token, embedding_coluna)[0][0]
                    print(f"  Similaridade com '{coluna}': {similarity}")
                    if similarity > melhor_similaridade_token_debug and similarity > limiar_atual_debug:
                        melhor_similaridade_token_debug = similarity
                        coluna_mais_similar_token_debug = coluna
            if coluna_mais_similar_token_debug:
                print(f"  Melhor similaridade para '{token.text}': {melhor_similaridade_token_debug} com '{coluna_mais_similar_token_debug}' (Limiar: {limiar_atual_debug})")