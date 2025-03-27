import mysql.connector
import streamlit as st

def conexaobanco():
    try:
        conn = mysql.connector.connect(
            host="crossover.proxy.rlwy.net",
            port=17025,
            user="root",
            password="nwiMDSsxmcmDXWChimBQOIswEFlTUMms",
            database="railway"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def validacao(usr, passw):
    conn = conexaobanco()
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
        st.success('Login feito com sucesso!')

        permissao = user.get('permissao') 
        if permissao == 'adm':
            st.session_state.page = "adm"
            st.rerun()  # Redireciona para a página de admin
        elif permissao == 'cliente':
            st.session_state.page = "dashboard"
            st.rerun()  # Redireciona para a página do cliente
        else:
            st.error('Permissão desconhecida. Não foi possível redirecionar.')

    else:
        st.error('Usuário ou senha incorretos, tente novamente.')

# Página principal de login
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logoatos.png", width=150)

    with st.form('sign_in'):
        st.caption('Por favor, insira seu usuário e senha.')
        username = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')

        botaoentrar = st.form_submit_button(label="Entrar", type="primary", use_container_width=True)

    if botaoentrar:
        validacao(username, password)

if st.session_state.authenticated:
    if "page" in st.session_state:
        if st.session_state.page == "adm":
            # Aqui começa a parte do admin que você pediu para adicionar
            import streamlit as st
            import mysql.connector

            def conectarbanco():
                try:
                    conn = mysql.connector.connect(
                        host="localhost",
                        port=3306,
                        user="root",
                        password="dudu2305",
                        database="atoscapital"
                    )
                    return conn
                except mysql.connector.Error as e:
                    st.error(f"Erro ao conectar ao banco de dados: {e}")
                    return None

            def puxarusuarios():
                conexao = conectarbanco()
                if conexao:
                    cursor = conexao.cursor()
                    cursor.execute("SELECT id, Nome/Empresa, usuario, senha, numero, permissao FROM usuarios ORDER BY id ASC")
                    usuarios = cursor.fetchall()
                    conexao.close()
                    return usuarios
                return []

            def atualizacaousuarios(user_id, nome_empresa, usuario, senha, numero, permissao):
                conexao = conectarbanco()
                if conexao:
                    cursor = conexao.cursor()

                    cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (usuario,))
                    usuario_existente = cursor.fetchone()

                    cursor.execute("SELECT id FROM usuarios WHERE numero = %s", (numero,))
                    numero_existente = cursor.fetchone()

                    if usuario_existente and usuario_existente[0] != user_id:
                        st.error("Nome de usuário já está sendo utilizado por outro usuário.")
                        return False

                    if numero_existente and numero_existente[0] != user_id:
                        st.error("Número já está sendo utilizado por outro usuário.")
                        return False

                    cursor.execute(
                        "UPDATE usuarios SET Nome/Empresa = %s, usuario = %s, senha = %s, numero = %s, permissao = %s WHERE id = %s",
                        (nome_empresa, usuario, senha, numero, permissao, user_id)
                    )
                    conexao.commit()
                    conexao.close()
                    return True
                return False

            def excluirusuario(user_id):
                conexao = conectarbanco()
                if conexao:
                    cursor = conexao.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
                    conexao.commit()
                    conexao.close()
                    st.success("Usuário excluído com sucesso!")

            def novousuario(nome_empresa, usuario, senha, numero, permissao):
                conexao = conectarbanco()
                if conexao:
                    cursor = conexao.cursor()

                    # Verifica se o nome de usuário já existe
                    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (usuario,))
                    count_usuario = cursor.fetchone()[0]

                    # Verifica se o número já existe
                    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE numero = %s", (numero,))
                    count_numero = cursor.fetchone()[0]

                    if count_usuario > 0:
                        st.error("Nome de usuário já está sendo utilizado.")
                        return False

                    if count_numero > 0:
                        st.error("Número já está sendo utilizado.")
                        return False

                    cursor.execute(
                        "INSERT INTO usuarios (Nome/Empresa, usuario, senha, numero, permissao) VALUES (%s, %s, %s, %s, %s)",
                        (nome_empresa, usuario, senha, numero, permissao)
                    )
                    conexao.commit()
                    conexao.close()
                    return True
                return False

            def formularionovousuario():
                col1, col2 = st.columns([9, 1])
                with col2:
                    if st.button("❌ Fechar", key="fecharformulario"):
                        st.session_state.novousuario = False
                        st.rerun()

                st.subheader("Adicionar Novo Usuário")

                with st.form(key="formnovousuario"):
                    nome_empresa = st.text_input("Nome/Empresa")
                    usuario = st.text_input("Usuário")
                    senha = st.text_input("Senha", type="password")
                    numero = st.text_input("Número")
                    permissao = st.radio("Permissão", ["adm", "cliente"])

                    submit_button = st.form_submit_button(label="Adicionar Usuário")

                    if submit_button:
                        if novousuario(nome_empresa, usuario, senha, numero, permissao):
                            st.session_state.mensagem = "Novo usuário cadastrado com sucesso!"
                            st.session_state.novousuario = False
                            st.rerun()

            def formularioeditarusuario(user):
                col1, col2 = st.columns([9, 1])
                with col2:
                    if st.button("❌ Fechar", key=f"fecharformularioeditar{user[0]}"):
                        st.session_state.editar_usuario = None
                        st.rerun()

                st.subheader(f"Editar Usuário: {user[1]}")

                with st.form(key=f"editarusuario{user[0]}"):
                    nome_empresa = st.text_input("Nome/Empresa", value=user[1])
                    usuario = st.text_input("Usuário", value=user[2])
                    senha = st.text_input("Senha", value=user[3], type="password")
                    numero = st.text_input("Número", value=user[4])
                    permissao = st.radio("Permissão", ["adm", "cliente"], index=0 if user[5] == "adm" else 1)
                    submit_button = st.form_submit_button(label="Atualizar Usuário")

                    if submit_button:
                        if atualizacaousuarios(user[0], nome_empresa, usuario, senha, numero, permissao):
                            st.session_state.editar_usuario = None
                            st.rerun()

            def listarusuarios():
                usuarios = puxarusuarios()

                table_columns = [2, 10, 5, 5, 8, 4, 2, 2]
                header = st.columns(table_columns)
                headers = ["ID", "Nome/Empresa", "Usuário", "Senha", "Número", "Permissão", "Editar", "Excluir"]

                for col, header_text in zip(header, headers):
                    with col:
                        st.write(f"**{header_text}**")

                for user in usuarios:
                    with st.container():
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 10, 5, 5, 8, 4, 2, 2])
                        col1.write(user[0])  # ID
                        col2.write(user[1])  # Nome/Empresa
                        col3.write(user[2])  # Usuário
                        col4.write(user[3])  # Senha
                        col5.write(user[4])  # Número
                        col6.write(user[5])  # Permissão

                        if col7.button("✏️", key=f"edit_{user[0]}"):
                            st.session_state.editar_usuario = user[0]
                            st.rerun()
                        
                        # Confirmar exclusão
                        if col8.button("🗑️", key=f"delete_{user[0]}"):
                            st.session_state.confirmarexclusao = user[0]
                            st.session_state.usuario_a_excluir = user[1]
                            st.session_state.exclusao_confirmada = False
                            st.rerun()

                    # Exibir a confirmação para excluir o usuário
                    if "confirmarexclusao" in st.session_state and st.session_state.confirmarexclusao == user[0] and not st.session_state.exclusao_confirmada:
                        st.subheader(f"Você realmente deseja excluir o usuário {st.session_state.usuario_a_excluir}?")

                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Sim", key=f"sim_{user[0]}"):
                                excluirusuario(user[0])
                                st.session_state.exclusao_confirmada = True
                                st.session_state.confirmarexclusao = None
                                st.rerun()

                        with col2:
                            if st.button("Não", key=f"nao_{user[0]}"):
                                st.session_state.exclusao_confirmada = True
                                st.session_state.confirmarexclusao = None
                                st.rerun()

                        st.markdown("---")

            st.set_page_config(layout="wide")
            st.title("Gerenciamento de Usuários")

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Adicionar Novo Usuário"):
                    st.session_state.novousuario = True
                    st.rerun()

            with col2:
                if st.button("Dashboard"):
                    st.session_state.page = "dashboard"  # Redireciona para o dashboard
                    st.rerun()

            if "novousuario" in st.session_state and st.session_state.novousuario:
                formularionovousuario()

            listarusuarios()

            if "editar_usuario" in st.session_state and st.session_state.editar_usuario:
                usuario_editar = next(user for user in puxarusuarios() if user[0] == st.session_state.editar_usuario)
                formularioeditarusuario(usuario_editar)

        elif st.session_state.page == "dashboard":
            # Configuração da página do dashboard
            st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
            st.title("DASHBOARD")
            # Aqui você pode incluir o conteúdo da página de cliente
