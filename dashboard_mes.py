from decimal import Decimal
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import locale as lc
import consulta_SQL_mes
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

lc.setlocale(lc.LC_ALL, 'pt_BR')

st.set_page_config(
    page_title='Dashboard Mês',
    page_icon=':a:',
    layout='wide'
)

#inicio sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #800000; 
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filtros")
filiais= consulta_SQL_mes.obter_nmfilial()
filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)

meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

hoje = datetime.today()
dia_hoje = hoje.day
mes_atual = hoje.month
ano_atual = hoje.year

anos_disponiveis = consulta_SQL_mes.obter_anos_disponiveis()
ano_selecionado = st.sidebar.selectbox("Selecione o ano de referência", anos_disponiveis, index=len(anos_disponiveis) - 1)

if dia_hoje == 1 and mes_atual == 1:
    # Remove o ano atual da lista (não deixa selecionar Janeiro de X)
    anos_disponiveis.remove(ano_atual)

if ano_selecionado == ano_atual:
    if dia_hoje == 1:
        if mes_atual == 1:
            # 1º de Janeiro do ano atual → nenhum mês disponível
            meses_disponiveis = []
        else:
            # 1º de qualquer outro mês → exclui mês atual e mês anterior
            meses_disponiveis = meses[:mes_atual - 2]  # até dois meses atrás
    else:
        # Dia 2 em diante → permite até o mês anterior
        meses_disponiveis = meses[:mes_atual - 1]
else:
    # Ano anterior → todos os meses
    meses_disponiveis = meses

if meses_disponiveis:
    mes_referencia = st.sidebar.selectbox("Selecione o mês de referência", meses_disponiveis)
else:
    st.sidebar.warning("Nenhum mês disponível para seleção com base na data atual.")
    mes_referencia = None
      
# Após o st.selectbox do mes_referencia:

indice_mes_referencia = meses.index(mes_referencia) + 1

if dia_hoje == 1 and indice_mes_referencia == mes_atual and ano_selecionado == ano_atual:
    # Pega dois meses atrás
    data_ref = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
    data_ref = (data_ref - timedelta(days=1)).replace(day=1)
    mes_final = data_ref.month
    ano_final = data_ref.year 
elif dia_hoje != 1 and indice_mes_referencia == mes_atual and ano_selecionado == ano_atual:
    # Pega um mês atrás
    data_ref = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
    mes_final = data_ref.month
    ano_final = data_ref.year
else:
    # Usa mês selecionado mesmo
    mes_final = indice_mes_referencia
    ano_final = ano_selecionado


# Transforma o mês selecionado em lista
mes_referencia = [mes_referencia]
mes_selecionado = mes_referencia[0]
#fim sidebar

#inicio cabeçalho
left_co, cent_co, last_co = st.columns(3)
with cent_co:
    st.image('imgs\HORIZONTAL\PNG\ATOS CAPITAL BRANCO.png', width=500)
st.write(f"# Relatório de venda da {filial_selecionada}")
#fim cabeçalho

total_vendas = consulta_SQL_mes.obter_vendas_ano_anterior_mes_anterior(filial_selecionada, mes_final, ano_final - 1) # Método que realizou a mudança
meta_mes = consulta_SQL_mes.obter_meta_mes_anterior(filial_selecionada, mes_final, ano_final) # Realizou mudança no método
vendas_mes_atual = consulta_SQL_mes.obter_vendas_mes_anterior(filial_selecionada, mes_final, ano_selecionado) # Método usado # Requer continuar
percentual_crescimento_meta = consulta_SQL_mes.obter_percentual_crescimento_meta(filial_selecionada) # Requer continuar
vendas_mensais = consulta_SQL_mes.obter_vendas_anual_e_filial_mes_anterior(filial_selecionada, mes=mes_final, ano=ano_final)


# Criado -----
def calcular_percentual_crescimento(vendas_mes_atual, total_vendas):
    """Calcula o percentual de crescimento com base nos valores de vendas do mês/ano atual e do mesmo mês no ano anterior."""

    if total_vendas and total_vendas > 0:
        percentual = ((vendas_mes_atual / total_vendas) - Decimal("1")) * Decimal("100")
        return percentual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        return Decimal("0.00")
percentual_crescimento = calcular_percentual_crescimento(vendas_mes_atual, total_vendas)

def calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes):
    """Calcula o percentual de crescimento com base nos valores de vendas do mês/ano atual e do mesmo mês no ano anterior."""

    if meta_mes and meta_mes > 0:
        percentual = ((vendas_mes_atual / meta_mes) - Decimal("1")) * Decimal("100")
        return percentual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        return Decimal("0.00")
percentual_crescimento_meta = calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes)

#-----------

@st.cache_data
def grafico_de_barras_mes_anterior(meta_mes, vendas_ano, vendas_mes_atual):
    def safe_float(value):
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    meta_mes = safe_float(meta_mes)
    vendas_ano = safe_float(vendas_ano)
    vendas_mes_atual = safe_float(vendas_mes_atual)

    categorias = ["Vendas ano anterior", "Meta do mês", f"Vendas de {mes_selecionado}"]
    valores = [vendas_ano, meta_mes, vendas_mes_atual]
    cores = ["darkgray", "darkblue", "darkred"]
    textos_formatados = [f'R$ {lc.currency(v, grouping=True, symbol=False)}' for v in valores]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=textos_formatados,
        textposition='outside',
        hovertemplate=[
            f'{cat}, {txt}<extra></extra>' for cat, txt in zip(categorias, textos_formatados)
        ]
    ))

    fig.update_layout(
        title=f"📊 Mês: {mes_selecionado}",
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

# Alterado
@st.cache_data 
def grafico_de_crescimento_mes(vendas_mes_atual, total_vendas, meta_mes):
    try:
        percentual_crescimento = calcular_percentual_crescimento(vendas_mes_atual, total_vendas)
        percentual_crescimento = float(percentual_crescimento)
    except (ValueError, TypeError):
        percentual_crescimento = 0.0

    # Gerado
    try:
        percentual_crescimento_meta = calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes)
        percentual_crescimento_meta = float(percentual_crescimento_meta)
    except (ValueError, TypeError):
        percentual_crescimento_meta = 0.0
        
    fig = go.Figure()

    categorias = ["Cresc. Mês", "Cresc. meta"]
    valores = [calcular_percentual_crescimento(vendas_mes_atual, total_vendas), calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes)]
    cores = ["green","aqua"]

    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=[f"{float(v):,.2f} %" for v in valores],
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

@st.cache_data
def grafico_linhas_por_filial(mes_referencia, filial_selecionada, ano_selecionado):
    vendas = consulta_SQL_mes.obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada, ano_selecionado)

    if not vendas:
        st.warning("Nenhuma venda encontrada para os filtros selecionados.")
        return

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
    df_vendas["MesAno"] = df_vendas["Mês"] + "/" + df_vendas["Ano"]

    fig = go.Figure()

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
        showlegend=True,
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True, 
            tickformat=",."
        )
    )

    return fig


def grafico_de_evolucao_vendas_mes_anterior(vendas_mensais, filial, ano): # Foi modificado
    df_vendas = pd.DataFrame(list(vendas_mensais.items()), columns=['Mês', 'Vendas'])
    df_vendas['Mês'] = pd.to_datetime(df_vendas['Mês'], format='%m/%Y')
    df_vendas = df_vendas.sort_values("Mês")

    fig = go.Figure()

    df_vendas["Valor_formatado"] = df_vendas["Vendas"].apply(lambda y: lc.currency(y, grouping=True))

    fig.add_trace(go.Scatter(
        x=df_vendas["Mês"].dt.strftime('%m/%Y'),
        y=df_vendas["Vendas"],
        mode='lines+markers',
        name="Vendas",
        hovertemplate='Mês %{x}<br>Valor: %{customdata}<extra></extra>',
        customdata=df_vendas["Valor_formatado"]
    ))

    fig.update_layout(
        title=f"📊 Vendas - Evolução até {mes_final:02d}/{ano} - {filial}",
        xaxis_title="Meses",
        yaxis_title="Valor das Vendas (R$)",
        font=dict(color="white", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat="R$ ,.2f",
        template="plotly_white",
        yaxis=dict(
            tickprefix="R$ ",
            separatethousands=True,
            tickformat=",."
        )
    )
    return fig



#Exibição:
col1, col2, col3 = st.columns(3)

   
exibindo_grafico_de_barras = grafico_de_barras_mes_anterior(meta_mes, total_vendas, vendas_mes_atual)
st.plotly_chart(exibindo_grafico_de_barras, use_container_width=True)

st.divider()

exibindo_grafico_de_crescimento = grafico_de_crescimento_mes(vendas_mes_atual, total_vendas, meta_mes) # Alterado
st.sidebar.plotly_chart(exibindo_grafico_de_crescimento)

exibindo_grafico_de_linhas_vendas_por_mes = grafico_linhas_por_filial(mes_referencia, filial_selecionada, ano_selecionado)
st.write(exibindo_grafico_de_linhas_vendas_por_mes)

exibindo_grafico_acompanhamanto_mensal = grafico_de_evolucao_vendas_mes_anterior(vendas_mensais, filial_selecionada, ano_selecionado) # Foi modificado
st.write(exibindo_grafico_acompanhamanto_mensal)
