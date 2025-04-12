import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import consultaSQL

st.set_page_config(
    page_title='Relatório',
    page_icon=':a:',
    layout='wide'
)

#sidebar
with st.sidebar:
  st.image('imgs\VERTICAL\PNG\ATOS CAPITAL BRANCO.png', width=200)

st.sidebar.header("Filtros")
filiais= consultaSQL.obter_nmfilial()
filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)
#sidebar

#inicio cabeçalho
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image('imgs\HORIZONTAL\PNG\ATOS CAPITAL BRANCO.png', width=500)
st.write(f"# Relatório de venda da {filial_selecionada}")
#fim cabeçalho


total_vendas =  consultaSQL.obter_vendas_ano_anterior(filial_selecionada)

meta_mes = consultaSQL.obter_meta_mes(filial_selecionada)

previsao = consultaSQL.obter_previsao_vendas(filial_selecionada)

acumulo_vendas_ano_anterior = consultaSQL.acumulo_vendas_periodo_ano_anterior(filial_selecionada)

acumulo_meta_ano_anterior = consultaSQL.obter_acumulo_meta_ano_anterior(filial_selecionada)

acumulo_de_vendas = consultaSQL.obter_acumulo_de_vendas(filial_selecionada)

vendas_dia_anterior = consultaSQL.obter_ultima_venda_com_valor(filial_selecionada)

percentual_crescimento_atual = consultaSQL.obter_percentual_de_crescimento_atual(filial_selecionada)

percentual_crescimento_meta = consultaSQL.obter_percentual_crescimento_meta(filial_selecionada)


# Criar gráfico de comparação Meta x Previsão x Vendas
def grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas):
    # Converte os valores para float (caso venham como Decimal)
    meta_mes = float(meta_mes)
    previsao = float(previsao)
    acumulo_meta_ano_anterior = float(acumulo_meta_ano_anterior)
    acumulo_de_vendas = float(acumulo_de_vendas)

    categorias = ["Meta do mês", "Previsão", "Acumulado meta", "Acumulado Vendas"]
    valores = [meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas]
    cores = ["gray", "blue", "red", "orange"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=[f"R$ {v:,.2f}" for v in valores],
        textposition='outside'
    ))

    fig.update_layout(
        title= f"📊 Metas e previsões da {filial_selecionada}",
        xaxis_title="",
        yaxis_title="Valor (R$)",
        font=dict(color="white", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


#criando o dataframe para a tabela
df = pd.DataFrame(
   [
    {"Filial": f"{filial_selecionada}", "Vendas 2024": f"{total_vendas:,.2f}", "Acum. 2024": f"{acumulo_vendas_ano_anterior:,.2f}", "Vendas do dia": f"{vendas_dia_anterior:,.2f}" }
   ]
)

#grafico de crescimento
def grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta):
    percentual_crescimento_atual = float(percentual_crescimento_atual)
    percentual_crescimento_meta = float(percentual_crescimento_meta)

    fig = go.Figure()

    categorias = ["Cresc. 2025", "Cresc. meta"]
    valores = [percentual_crescimento_atual, percentual_crescimento_meta]
    cores = ["green","aqua"]

    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=[f"{v:,.2f} %" for v in valores],
        textposition='outside'
    ))

    fig.update_layout(
        title= f"% Crescimento",
        xaxis_title="",
        yaxis_title="Valor %",
        font=dict(color="white", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig






#Exibição:

grafico1 = grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas)
st.plotly_chart(grafico1, use_container_width=True)

st.divider()

#exibindo grafico de crescimento
grafico2 = grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta)
st.sidebar.plotly_chart(grafico2)

#exibindo a tabela
st.dataframe(df, use_container_width=True, hide_index= True)

st.divider()








