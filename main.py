import mysql.connector
import streamlit as st
import webbrowser

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def conectar_bd():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="atoscapital"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def validacao(usr, passw):
    conn = conectar_bd()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM usuarios WHERE usuario = %s AND senha = %s"
    cursor.execute(query, (usr, passw))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        st.session_state.authenticated = True  
        st.success('Login feito com sucesso! Redirecionando...')
        st.markdown("<meta http-equiv='refresh' content='0; url=https://site.atoscapital.com.br/'>", unsafe_allow_html=True)
    else:
        st.error('Usuário ou senha incorretos, tente novamente.')

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logoatos.png", width=150)

    with st.form('sign_in'):
        st.caption('Por favor, insira seu usuário e senha.')
        username = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')

        submit_btn = st.form_submit_button(label="Entrar", type="primary", use_container_width=True)

    if submit_btn:
        validacao(username, password)
else:
    st.success("Você está logado!")
    st.markdown("[Acessar Atos Capital](https://site.atoscapital.com.br/)")
