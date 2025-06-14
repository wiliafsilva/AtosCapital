# AtosCapital Código

### 1.3 - Passo a Passo para execução do MVP 
### 1.3.2 - Dashboard
### 1. Instale a IDE Visual Studio Code
Baixe e instale a partir de: https://code.visualstudio.com/

### 2. Instale o Python no dispositivo
Disponível em: https://www.python.org/downloads/

### 3. Configure o Python no VS Code
Abra o VS Code
Pressione Ctrl+Shift+P → escolha Python: Select Interpreter
Selecione o interpretador do Python instalado

### 4. Faça o download do git
https://git-scm.com/

### 5. Faça uma cópia do repositório do projeto
No terminal da IDE, execute os seguintes passos
git clone https://github.com/wiliafsilva/AtosCapital.git
Mude para a pasta correta com o comando cd AtosCapital

### 6. Instale as dependências do projeto:
No terminal, verifique se está na pasta do arquivo “AtosCapital” e execute o comando: pip install -r requirements.txt

### 7. Execute o projeto:
No terminal, verifique se está na pasta do arquivo “AtosCapital” e  execute o projeto com o seguinte comando: streamlit run main.py

# AtosCapital IA

### 1. Groq
1. Crie uma conta no <a href="https://groq.com/" target="_blank">Groq</a>

2. Após a conta criada acesse <a href="https://console.groq.com/keys" target="_blank">https://console.groq.com/keys</a> , clique em Create API Key, escolha o nome da instância e clique em submit, após isso copie sua chave API gratuita e guarde em algum local 

### 2. Docker
Instale o <a href="https://www.docker.com/" target="_blank">Docker</a> no seu dispositivo e faça as configurações iniciais para futuramente baixar aplicativos dentro do contêiner


### 3. Evolution
1. Baixe a Evolution API dentro do seu contêiner do docker seguido o vídeo a seguir: <a href="https://www.youtube.com/watch?v=KXSvWzJuv_U" target="_blank">https://www.youtube.com/watch?v=KXSvWzJuv_U</a>

2. Ao abrir o Evolution API clique no botão “Instace +” para criar sua nova instância, escolha o nome, mantenha o channel Baileys e clique em SAVE
3. Após isso clique em sua instância criada, clique em Get QR Code e conecte o seu whatsapp


### 4. N8N


1. Baixe o N8N no contêiner do docker seguindo o vídeo a seguir: <a href="https://www.youtube.com/watch?v=8hQ1u0TAyAc" target="_blank">https://www.youtube.com/watch?v=8hQ1u0TAyAc</a>


2. Ao abrir o N8N no localhost crie sua conta e faça login


3. Selecione a opção Create Workflow clique nos **3 pontos** localizados no canto superior direito, e selecione a opção “Import from File” e selecione o arquivo json com o nome **“Responder_com_Ia.json”**, localizado dentro da pasta AtosCapital


4. Após workflow importado substituir nós de Banco de Dados, Evolution API, Groq com suas credenciais para o fluxo funcionar perfeitamente
