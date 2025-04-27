from collections import defaultdict
from decimal import Decimal
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import locale as lc
import consultaSQL

lc.setlocale(lc.LC_ALL, 'pt_BR')

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

mes_referencia = st.sidebar.selectbox("Selecione o mês de referência", meses)

# Transforma o mês selecionado em lista
mes_referencia = [mes_referencia]

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
        text=[f"R$ {lc.currency(v, grouping=True, symbol=False)}" for v in valores],
        textposition='outside'
    ))

    fig.update_layout(
        title= f"📊 Metas e previsões da {filial_selecionada}",
        xaxis_title="",
        yaxis_title="Valor (R$)",
        font=dict(color="white", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=550, 
        width=500,
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True, 
            tickformat=",." 
        )
    )

    return fig

@st.cache_data #as informações da função vai ficar em cache
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
        height=500, 
        width=500
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
    anos = [v[3] for v in vendas]

    df_vendas = pd.DataFrame({
        "Data": pd.to_datetime(datas),
        "Valor": valores,
        "Mês": [str(m) for m in meses],
        "Ano": [str(a) for a in anos]
    })

    df_vendas["Dia"] = df_vendas["Data"].dt.day 
    df_vendas["Valor_formatado"] = df_vendas["Valor"].apply(lambda x: lc.currency(x, grouping=True))

    fig = go.Figure()

    # Criar um agrupador mês/ano para diferenciar as linhas
    df_vendas["MesAno"] = df_vendas["Mês"] + "/" + df_vendas["Ano"]

    for mesano in df_vendas["MesAno"].unique():
        df_mesano = df_vendas[df_vendas["MesAno"] == mesano]

        fig.add_trace(go.Scatter(
            x=df_mesano["Dia"], 
            y=df_mesano["Valor"],
            mode='lines+markers',
            name=mesano,
            hovertemplate='Dia %{x}<br>Valor: %{customdata}<extra></extra>',
            customdata=df_mesano["Valor_formatado"]
        ))

    fig.update_layout(
        title=f"📈 Vendas comparadas {mes_referencia[0]} - {filial_selecionada}",
        xaxis_title="Dia do Mês",
        yaxis_title="Vendas (R$)",
        template="plotly_white",
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True, 
            tickformat=",."
        )
    )

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

        df_vendas["Valor_formatado"] = df_vendas["Valor"].apply(lambda y: lc.currency(y, grouping=True))

        fig.add_trace(go.Scatter(
            x=df_vendas["AnoMes"].dt.strftime('%m/%Y'),
            y=df_vendas["Valor"],
            mode='lines+markers',
            name="Vendas",
            hovertemplate='Mês %{x}<br>Valor: %{customdata}<extra></extra>',
            customdata=df_vendas["Valor_formatado"]
        ))

        fig.update_layout(
            title=f"📊 Vendas nos últimos 12 meses - {filial_selecionada}",
            xaxis_title="Mês/Ano",
            yaxis_title="Vendas (R$)",
            template="plotly_white",
            yaxis=dict(
                tickprefix="R$ ",
                separatethousands=True,  # coloca separador de milhar
                tickformat=",."  # formato numérico com separador de milhar
            )
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
            R$ {lc.currency(total_vendas, grouping=True, symbol=False)}
            """)
with col2:
   st.write(f"""#### Acumulado 2024: \n
            R$ {lc.currency(acumulo_vendas_ano_anterior, grouping=True, symbol=False)}
            """)
with col3:
   st.write(f"""#### Vendas do dia: \n 
            R$ {lc.currency(vendas_dia_anterior, grouping=True, symbol=False)}""") 
   
exibindo_grafico_de_barras = grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas)
st.plotly_chart(exibindo_grafico_de_barras, use_container_width=True)

st.divider()

exibindo_grafico_de_crescimento = grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta)
st.sidebar.plotly_chart(exibindo_grafico_de_crescimento)

exibindo_grafico_de_linhas_vendas_por_mes = grafico_linhas_por_filial(mes_referencia,filial_selecionada)
st.write(exibindo_grafico_de_linhas_vendas_por_mes)

exibindo_grafico_acompanhamanto_anual = grafico_de_evolucao_vendas(vendas_mensais)
st.write(exibindo_grafico_acompanhamanto_anual)

st.subheader("📍 Mapa das filiais")
st.map(dados_vendas[['latitude', 'longitude']]) 



