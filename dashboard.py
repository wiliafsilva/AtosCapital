import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import plotly.express as px
import consultaSQL

st.set_page_config(
    page_title='Relatório',
    page_icon=':a:',
    layout='wide'
)

#inicio cabeçalho
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image('imgs\HORIZONTAL\PNG\ATOS CAPITAL BRANCO.png', width=500)
st.write(f"# Relatório venda loja")
#fim cabeçalho

#sidebar
with st.sidebar:
  st.image('imgs\VERTICAL\PNG\ATOS CAPITAL BRANCO.png', width=400)

st.sidebar.header("Filtros")
filiais= consultaSQL.obter_nmfilial()
filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)
#sidebar

#cahamada das consultas
total_vendas =  consultaSQL.obter_vendas_ano_anterior(filial_selecionada)
#Vendas do mês no ano anterior + 5%
meta_mes = consultaSQL.obter_meta_mes(filial_selecionada)

previsao = consultaSQL.obter_previsao_vendas(filial_selecionada)

acumulo_vendas_ano_anterior = consultaSQL.acumulo_vendas_periodo_ano_anterior(filial_selecionada)

acumulo_meta_ano_anterior = consultaSQL.obter_acumulo_meta_ano_anterior(filial_selecionada)

acumulo_de_vendas = consultaSQL.obter_acumulo_de_vendas(filial_selecionada)

vendas_dia_anterior = consultaSQL.obter_ultima_venda_com_valor(filial_selecionada)



# Criar gráfico de comparação Meta x Previsão x Vendas
fig, ax = plt.subplots(figsize=(8, 3))
categorias = ["Meta do mês","Previsão", "Acumulado meta","Acumulado Vendas"]
valores = [meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas]
ax.bar(categorias, valores, color=["gray","blue", "red", "orange"])
ax.set_title(f"Metas e previsões da {filial_selecionada}")
ax.set_ylabel("Valor (R$)")


#Exibição:

#grafico Meta x Previsão x Vendas
st.pyplot(fig)
st.write(f"**Meta ddo mês:** R$ {meta_mes:,.2f}")
st.write(f"**Previsão:** R$ {previsao:,.2f}")
st.write(f"**Acumulado Meta:** R$ {acumulo_meta_ano_anterior:,.2f}")
st.write(f"**Acumulado Vendas:** R$ {acumulo_vendas_ano_anterior:,.2f}")


st.divider()

st.write(f"Acumulo da meta no ano anterior {acumulo_meta_ano_anterior}")
st.write(f"Acumulo de vandas da {filial_selecionada} no mes atual: {acumulo_de_vendas}")
st.write(f"Vendas do dia anterior da {filial_selecionada}: {vendas_dia_anterior}")


