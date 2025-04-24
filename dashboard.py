from collections import defaultdict
from decimal import Decimal
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import consultaSQL

st.set_page_config(
    page_title='Dashboard',
    page_icon=':a:',
    layout='wide'
)

#sidebar
#with st.sidebar:
 # st.image('imgs\VERTICAL\PNG\ATOS CAPITAL BRANCO.png', width=200)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #800000; /* Cor de exemplo em vermelho com transparência */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filtros")
filiais= consultaSQL.obter_nmfilial()
filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)

meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

mes_referencia = st.sidebar.multiselect("Selecione o mês de referencia", meses)

#sidebar

#inicio cabeçalho
left_co, cent_co, last_co = st.columns(3)
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

vendas_mensais = consultaSQL.obter_vendas_anual_e_filial(filial_selecionada)


@st.cache_data #as informações da função vai ficar em cache
# Criar gráfico de comparação Meta x Previsão x Vendas
def grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas):
    # Converte os valores para float (caso venham como Decimal)
    meta_mes = float(meta_mes)
    previsao = float(previsao)
    acumulo_meta_ano_anterior = float(acumulo_meta_ano_anterior)
    acumulo_de_vendas = float(acumulo_de_vendas)

    categorias = ["Meta do mês", "Previsão", "Acumulado meta", "Acumulado Vendas"]
    valores = [meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas]
    cores = ["darkgray", "darkblue", "darkred", "white"]

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


@st.cache_data #as informações da função vai ficar em cache
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

@st.cache_data #as informações da função vai ficar em cache
def grafico_linhas_por_filial(mes_referencia, filial_selecionada): 
    vendas = consultaSQL.obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada)

    if not vendas:
        st.warning("Nenhuma venda encontrada para os filtros selecionados.")
        return

    # Extrai e organiza os dados
    valores = [float(v[0]) if isinstance(v[0], Decimal) else v[0] for v in vendas]
    datas = [v[1] for v in vendas]
    meses = [v[2] for v in vendas]

    df_vendas = pd.DataFrame({
        "Data": pd.to_datetime(datas),
        "Valor": valores,
        "Mês": [str(m) for m in meses]
    })

    df_vendas["Mês"] = df_vendas["Mês"].astype(str)
    df_vendas["Dia"] = df_vendas["Data"].dt.day 

    fig = go.Figure()

    # Adiciona uma linha para cada mês com cor diferente
    for mes in df_vendas["Mês"].unique():
        df_mes = df_vendas[df_vendas["Mês"] == mes]

        fig.add_trace(go.Scatter(
            x=df_mes["Dia"], 
            y=df_mes["Valor"],
            mode='lines+markers',
            name=mes
        ))

    fig.update_layout(
        title=f"📈 Vendas comparadas por dia do mês - {filial_selecionada}",
        xaxis_title="Dia do Mês",
        yaxis_title="Vendas (R$)",
        template="plotly_white"
    )

    #st.plotly_chart(fig, use_container_width=True)
    return fig

@st.cache_data #as informações da função vai ficar em cache
def acompanhamento_anual(filial_selecionada):
    vendas = consultaSQL.obter_vendas_anual_e_filial(filial_selecionada)

    if vendas:
        datas = [v[1] for v in vendas]
        valores = [float(v[0]) if isinstance(v[0], Decimal) else v[0] for v in vendas]
    
        df_vendas = pd.DataFrame({
                "AnoMes": pd.to_datetime(datas, format="%Y-%m"),
                "Valor": valores
            })
        
           # Ordena os meses
        df_vendas = df_vendas.sort_values("AnoMes")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_vendas["AnoMes"].dt.strftime('%b/%Y'),
            y=df_vendas["Valor"],
            mode='lines+markers',
            name="Vendas"
        ))

        fig.update_layout(
            title=f"📊 Vendas nos últimos 12 meses - {filial_selecionada}",
            xaxis_title="Mês/Ano",
            yaxis_title="Vendas (R$)",
            template="plotly_white"
        )

        return fig
    else:
        st.warning("Nenhuma venda encontrada para os últimos 12 meses.")


def grafico_de_evolucao_vendas(vendas_mensais):

    df_vendas = pd.DataFrame(list(vendas_mensais.items()), columns=['Mês', 'Vendas'])
    df_vendas['Mês'] = pd.to_datetime(df_vendas['Mês'], format='%m/%Y')
    fig = px.line(df_vendas, x='Mês', y='Vendas',
                  title=f'Evolução das Vendas - Últimos 12 meses ({filial_selecionada})')
    
    fig.update_layout(
        xaxis_title="Meses",
        yaxis_title="Valor das Vendas (R$)",
        font=dict(color="white", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat="R$ ,.2f"
    )
    return fig

# Exibição


#criando o dataframe para a tabela
df = pd.DataFrame(
   [
    {"Filial": f"{filial_selecionada}", "Vendas 2024": f"{total_vendas:,.2f}", "Acum. 2024": f"{acumulo_vendas_ano_anterior:,.2f}", "Vendas do dia": f"{vendas_dia_anterior:,.2f}" }
   ]
)

#Mapa das filiais
coordenadas_filiais = {
    'FILIAL BELÉM': {'latitude': -1.455, 'longitude': -48.489},
    'FILIAL BELO HORIZONTE': {'latitude': -19.9167, 'longitude': -43.9345},
    'FILIAL BRASÍLIA': {'latitude': -15.7939, 'longitude': -47.8828},
    'FILIAL CAMPINAS': {'latitude': -22.9056, 'longitude': -47.0608},
    'FILIAL CURITIBA': {'latitude': -25.4284, 'longitude': -49.2733},
    'FILIAL DUQUE DE CAXIAS': {'latitude': -22.7868, 'longitude': -43.3054},
    'FILIAL FORTALEZA': {'latitude': -3.7172, 'longitude': -38.5433},
    'FILIAL GOIÂNIA': {'latitude': -16.6869, 'longitude': -49.2648},
    'FILIAL GUARULHOS': {'latitude': -23.4545, 'longitude': -46.5333},
    'FILIAL MACEIÓ': {'latitude': -9.6658, 'longitude': -35.735},
    'FILIAL MANAUS': {'latitude': -3.119, 'longitude': -60.0217},
    'FILIAL RECIFE': {'latitude': -8.0476, 'longitude': -34.877},
    'FILIAL RIO DE JANEIRO': {'latitude': -22.9068, 'longitude': -43.1729},
    'FILIAL SALVADOR': {'latitude': -12.9714, 'longitude': -38.5014},
    'FILIAL SÃO GONÇALO': {'latitude': -22.8268, 'longitude': -43.0634},
    'FILIAL SÃO LUÍS': {'latitude': -2.5307, 'longitude': -44.3068},
    'FILIAL SÃO PAULO': {'latitude': -23.5505, 'longitude': -46.6333},
}

# Suponha que isso veio do banco
dados_vendas = pd.DataFrame({
    'filial': ['FILIAL BELÉM', 'FILIAL BELO HORIZONTE', 'FILIAL BRASÍLIA', 'FILIAL CAMPINAS', 'FILIAL CURITIBA', 'FILIAL DUQUE DE CAXIAS', 'FILIAL FORTALEZA', 'FILIAL GOIÂNIA', 'FILIAL GUARULHOS', 'FILIAL MACEIÓ', 'FILIAL MANAUS', 'FILIAL RECIFE', 'FILIAL RIO DE JANEIRO', 'FILIAL SALVADOR', 'FILIAL SÃO GONÇALO', 'FILIAL SÃO LUÍS', 'FILIAL SÃO PAULO']
})


# Adiciona latitude e longitude ao DataFrame
dados_vendas['latitude'] = dados_vendas['filial'].map(lambda x: coordenadas_filiais[x]['latitude'])
dados_vendas['longitude'] = dados_vendas['filial'].map(lambda x: coordenadas_filiais[x]['longitude'])


#Exibição:

col1, col2, col3 = st.columns(3)

with col1:
   st.write(f"""#### Vendas 2024: \n 
            R$ {total_vendas:,.2f}
            """)
with col2:
   st.write(f"""#### Acumulado 2024: \n
            R$ {acumulo_vendas_ano_anterior:,.2f}
            """)
with col3:
   st.write(f"""#### Vendas do dia: \n 
            R$ {vendas_dia_anterior:,.2f}""") 
   

exibindo_grafico_de_barras = grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas)
st.plotly_chart(exibindo_grafico_de_barras, use_container_width=True)

st.divider()

exibindo_grafico_de_crescimento = grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta)
st.sidebar.plotly_chart(exibindo_grafico_de_crescimento)

#exibindo a tabela
st.dataframe(df, use_container_width=True, hide_index= True)

st.divider()

#grafico de linhas vendas por mes
exibindo_grafico_de_linhas_vendas_por_mes = grafico_linhas_por_filial(mes_referencia,filial_selecionada)
st.write(exibindo_grafico_de_linhas_vendas_por_mes)

#Grafico de linhas anual
exibindo_grafico_acompanhamanto_anual = grafico_de_evolucao_vendas(vendas_mensais)
st.write(exibindo_grafico_acompanhamanto_anual)


st.subheader("📍 Mapa das filiais")
st.map(dados_vendas[['latitude', 'longitude']]) 



