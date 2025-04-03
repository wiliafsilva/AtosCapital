import spacy
import numpy
from sklearn.metrics.pairwise import cosine_similarity

# Carregando o modelo spaCy com embeddings grandes
nlp = spacy.load("pt_core_news_lg")

# Metadados do banco de dados
tabelas_metadata = ["tbVendasDashboard"]
colunas_metadata = {"tbVendasDashboard": ["idVendas", "nrCNPJ", "nmFilial", "dtVenda", "vlVenda", "txMeta"]}

# Função para obter embedding de uma palavra
def get_embedding(word):
    return nlp(str(word)).vector

# Consulta do usuário
consulta = "Mostrar o valor das vendas e o nome da filial"
doc_consulta = nlp(consulta)

tabelas_similares = {}
colunas_selecionadas = []

# Encontrar tabelas similares
for tabela in tabelas_metadata:
    similarity = doc_consulta.similarity(nlp(tabela))
    tabelas_similares[tabela] = similarity

tabela_selecionada = max(tabelas_similares, key=tabelas_similares.get)

# Encontrar colunas similares para cada token (foco em substantivo)
for token in doc_consulta:
    if token.pos_ in ["NOUN", "ADJ"]:
        similaridades = {}  # Inicializa similaridades aqui
        for coluna in colunas_metadata.get(tabela_selecionada, []):
            similarity = cosine_similarity(get_embedding(token.text).reshape(1, -1), get_embedding(coluna).reshape(1, -1))[0][0]
            similaridades[coluna] = similarity

        if similaridades:
            coluna_mais_similar = max(similaridades, key=similaridades.get)
            colunas_selecionadas.append(coluna_mais_similar)

# Identificar condição (exemplo muito básico)
condicao_coluna = None
condicao_valor = None
for i, token in enumerate(doc_consulta):
    if token.text.lower() == 'de' and i + 1 < len(doc_consulta):
        condicao_valor = doc_consulta[i + 1].text
        melhor_similaridade = -1
        for coluna in colunas_metadata.get(tabela_selecionada, []):
            similaridade = cosine_similarity(get_embedding(condicao_valor).reshape(1, -1), get_embedding(coluna).reshape(1, -1))[0][0]
            if similarity > melhor_similaridade:
                melhor_similaridade = similarity
                condicao_coluna = coluna

# Montar o script SQL (muito básico)
script_sql = f"SELECT {', '.join(set(colunas_selecionadas))} FROM {tabela_selecionada}"
if condicao_coluna and condicao_valor:
    script_sql += f" WHERE {condicao_coluna} = '{condicao_valor}'"

print(script_sql)