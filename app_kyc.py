import streamlit as st
import requests
import json
import time
import random
import qrcode
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Celcoin KYC Simulator", page_icon="🧪", layout="wide")

st.title("🧪 Simulador de Onboarding Celcoin (Cenários)")
st.markdown("---")

# --- FUNÇÕES AUXILIARES (GERADORES) ---
def gerar_cpf():
    cpf = [random.randint(0, 9) for _ in range(9)]
    
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(11 - val if val > 1 else 0)
    
    return "".join(map(str, cpf))

def gerar_cnpj():
    def calculate_special_digit(l):
        digit = 0
        for i, v in enumerate(l):
            digit += v * (list(range(5, 1, -1)) + list(range(9, 1, -1)))[i]
        return 11 - digit % 11 if digit % 11 >= 2 else 0

    cnpj = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    cnpj.append(calculate_special_digit(cnpj))
    cnpj.append(calculate_special_digit(cnpj))
    return "".join(map(str, cnpj))

# --- BARRA LATERAL (CREDENCIAIS E CENÁRIOS) ---
with st.sidebar:
    st.header("🔐 Configuração")
    
    # Credenciais
    default_id = st.secrets.get("CLIENT_ID", "") if "CLIENT_ID" in st.secrets else ""
    default_secret = st.secrets.get("CLIENT_SECRET", "") if "CLIENT_SECRET" in st.secrets else ""
    
    client_id = st.text_input("Client ID", value=default_id)
    client_secret = st.text_input("Client Secret", value=default_secret, type="password")
    
    st.markdown("---")
    st.header("🎭 Seletor de Cenários")
    st.info("Escolha um cenário para preencher os dados automaticamente.")
    
    cenario = st.selectbox(
        "Qual cenário deseja testar?",
        [
            "Manual (Preencher eu mesmo)",
            "✅ PF - Aprovado (Happy Path)",
            "🚫 PF - Reprovado (Menor de Idade)",
            "🏢 PJ - Empresa Padrão (Happy Path)"
        ]
    )
    
    # Botão para gerar novos dados aleatórios dentro do cenário
    gerar_novos = st.button("🔄 Gerar Novos Dados para o Cenário")

# --- LÓGICA DE PREENCHIMENTO AUTOMÁTICO ---
# Inicializa session_state se não existir para manter os dados ao recarregar
if 'form_data' not in st.session_state or gerar_novos:
    st.session_state['form_data'] = {
        "tipo": "Pessoa Física (PF)",
        "nome": "", "doc": "", "nasc": "", "mae": "",
        "razao": "", "fantasia": "", "cnpj": "", "dt_const": "",
        "socio_nome": "", "socio_cpf": "", "socio_nasc": "",
        "email": "teste@celcoin.com.br", "tel": "11999999999"
    }
    
    # Lógica dos Cenários
    if "Aprovado" in cenario:
        st.session_state['form_data']['tipo'] = "Pessoa Física (PF)"
        st.session_state['form_data']['nome'] = "Usuario Teste Aprovado"
        st.session_state['form_data']['doc'] = gerar_cpf()
        st.session_state['form_data']['nasc'] = "1995-05-20" # Maior de idade
        st.session_state['form_data']['mae'] = "Maria Aprovada"
        
    elif "Menor de Idade" in cenario:
        st.session_state['form_data']['tipo'] = "Pessoa Física (PF)"
        st.session_state['form_data']['nome'] = "Usuario Teste Menor"
        st.session_state['form_data']['doc'] = gerar_cpf()
        st.session_state['form_data']['nasc'] = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d") # 10 anos
        st.session_state['form_data']['mae'] = "Maria Reprovada"
        
    elif "PJ" in cenario:
        st.session_state['form_data']['tipo'] = "Pessoa Jurídica (PJ)"
        st.session_state['form_data']['razao'] = "Empresa Sucesso LTDA"
        st.session_state['form_data']['fantasia'] = "Loja do Sucesso"
        st.session_state['form_data']['cnpj'] = gerar_cnpj()
        st.session_state['form_data']['dt_const'] = "2020-01-01"
        # Sócio
        st.session_state['form_data']['socio_nome'] = "Sócio Administrador"
        st.session_state['form_data']['socio_cpf'] = gerar_cpf()
        st.session_state['form_data']['socio_nasc'] = "1980-01-01"


# --- INTERFACE PRINCIPAL ---

# Radio Button controlado pelo estado
tipo_pessoa = st.radio(
    "Tipo de Abertura:", 
    ["Pessoa Física (PF)", "Pessoa Jurídica (PJ)"], 
    index=0 if st.session_state['form_data']['tipo'] == "Pessoa Física (PF)" else 1,
    horizontal=True
)

col1, col2 = st.columns(2)

# --- COLUNA 1: DADOS PRINCIPAIS ---
with col1:
    if tipo_pessoa == "Pessoa Física (PF)":
        st.subheader("Dados Pessoais")
        nome_completo = st.text_input("Nome Completo", value=st.session_state['form_data'].get('nome', ''))
        doc_number_principal = st.text_input("CPF", value=st.session_state['form_data'].get('doc', ''), max_chars=11)
        dt_nascimento = st.text_input("Data Nascimento", value=st.session_state['form_data'].get('nasc', ''))
        nome_mae = st.text_input("Nome da Mãe", value=st.session_state['form_data'].get('mae', ''))
        
    else: # PJ
        st.subheader("Dados da Empresa")
        razao_social = st.text_input("Razão Social", value=st.session_state['form_data'].get('razao', ''))
        nome_fantasia = st.text_input("Nome Fantasia", value=st.session_state['form_data'].get('fantasia', ''))
        doc_number_principal = st.text_input("CNPJ", value=st.session_state['form_data'].get('cnpj', ''), max_chars=14)
        dt_constituicao = st.text_input("Data Constituição", value=st.session_state['form_data'].get('dt_const', ''))
        
        st.info("Sócio (Facematch)")
        socio_nome = st.text_input("Nome Sócio", value=st.session_state['form_data'].get('socio_nome', ''))
        socio_cpf = st.text_input("CPF Sócio", value=st.session_state['form_data'].get('socio_cpf', ''), max_chars=11)
        socio_nasc = st.text_input("Nasc. Sócio", value=st.session_state['form_data'].get('socio_nasc', ''))

# --- COLUNA 2: ENDEREÇO E CONTATO ---
with col2:
    st.subheader("Endereço & Contato")
    email = st.text_input("E-mail", value=st.session_state['form_data'].get('email', ''))
    telefone = st.text_input("Celular", value=st.session_state['form_data'].get('tel', ''))
    
    # Endereço Fixo para facilitar teste
    c_cep, c_num = st.columns([1,1])
    with c_cep: cep = st.text_input("CEP", "06455000")
    with c_num: numero = st.text_input("Número", "100")
    
    logradouro = st.text_input("Logradouro", "Alameda Rio Negro")
    bairro = st.text_input("Bairro", "Alphaville")
    cidade = st.text_input("Cidade", "Barueri")
    estado = st.text_input("UF", "SP")

st.markdown("---")

# --- FUNÇÃO DE TOKEN ---
BASE_URL = "https://sandbox.openfinance.celcoin.dev"

def get_token(c_id, c_secret):
    try:
        payload = {'client_id': c_id, 'client_secret': c_secret, 'grant_type': 'client_credentials'}
        resp = requests.post(f"{BASE_URL}/v5/token", data=payload, timeout=10)
        return resp.json().get('access_token') if resp.status_code == 200 else None
    except: return None

# --- BOTÃO DE AÇÃO ---
if st.button("🚀 Enviar Proposta para Sandbox", type="primary"):
