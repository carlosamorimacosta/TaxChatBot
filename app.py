import streamlit as st
import os
from data_loader import load_documents, create_vector_store, load_vector_store, get_document_count

# Configuração da página
st.set_page_config(
    page_title="TaxBot - Assistente Fiscal",
    page_icon="📊",
    layout="wide"
)

# Título da aplicação
st.title("🤖 TaxBot - Assistente Fiscal Inteligente")
st.markdown("---")

# Inicializar session states
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Upload de arquivos
    uploaded_files = st.file_uploader(
        "📎 Fazer upload de PDFs",
        type=['pdf'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Garantir que a pasta docs existe
        os.makedirs("docs", exist_ok=True)
        
        # Salvar arquivos na pasta docs
        for uploaded_file in uploaded_files:
            file_path = os.path.join("docs", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)!")
    
    # Botão para processar documentos (versão simplificada)
    if st.button("🔄 Processar Documentos"):
        with st.spinner("Processando documentos..."):
            try:
                documents = load_documents()
                st.success(f"✅ {len(documents)} documentos processados!")
            except Exception as e:
                st.error(f"❌ Erro: {e}")
    
    # Informações do sistema
    st.markdown("---")
    st.header("📊 Status do Sistema")
    
    # Contar arquivos na pasta docs
    doc_files = []
    if os.path.exists("docs"):
        doc_files = [f for f in os.listdir("docs") if f.endswith('.pdf')]
    
    st.write(f"📁 Documentos carregados: {len(doc_files)}")
    
    # Botão para limpar chat
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# Abas principais
tab1, tab2 = st.tabs(["💬 Chat Fiscal", "🧮 Calculadora IR"])

with tab1:
    st.header("💬 Chat Fiscal Básico")
    
    # Exibir histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta sobre impostos..."):
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Gerar resposta básica
        with st.chat_message("assistant"):
            resposta = f"**Resposta simulada para:** '{prompt}'\n\n📝 *Sistema em configuração. Em breve teremos respostas baseadas em documentos fiscais.*"
            st.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})

with tab2:
    st.header("🧮 Calculadora de Imposto de Renda")
    
    with st.form("calculadora_ir"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Rendimentos")
            salario = st.number_input("Salário Bruto Mensal (R$)", min_value=0.0, value=3000.0, step=100.0)
            outros = st.number_input("Outros Rendimentos (R$)", min_value=0.0, value=0.0, step=100.0)
        
        with col2:
            st.subheader("📝 Deduções")
            dependentes = st.number_input("Número de Dependentes", min_value=0, value=0, step=1)
            previdencia = st.number_input("Previdência (R$)", min_value=0.0, value=0.0, step=50.0)
            pensao = st.number_input("Pensão Alimentícia (R$)", min_value=0.0, value=0.0, step=50.0)
        
        if st.form_submit_button("🎯 Calcular IR"):
            # Cálculo simplificado
            renda_mensal = salario + outros
            deducao_dependentes = dependentes * 189.59
            total_deducoes = previdencia + pensao + deducao_dependentes
            base_calculo = max(0, renda_mensal - total_deducoes)
            
            # Tabela IRPF 2024 (mensal)
            if base_calculo <= 1903.98:
                ir_devido = 0
            elif base_calculo <= 2826.65:
                ir_devido = base_calculo * 0.075 - 142.80
            elif base_calculo <= 3751.05:
                ir_devido = base_calculo * 0.15 - 354.80
            elif base_calculo <= 4664.68:
                ir_devido = base_calculo * 0.225 - 636.13
            else:
                ir_devido = base_calculo * 0.275 - 869.36
            
            ir_devido = max(0, ir_devido)
            
            # Exibir resultados
            st.success("✅ Cálculo realizado!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Renda Mensal", f"R$ {renda_mensal:,.2f}")
                st.metric("IR Mensal", f"R$ {ir_devido:,.2f}")
            
            with col2:
                st.metric("Base de Cálculo", f"R$ {base_calculo:,.2f}")
                st.metric("Salário Líquido", f"R$ {renda_mensal - ir_devido:,.2f}")
            
            with col3:
                aliquota_efetiva = (ir_devido / renda_mensal * 100) if renda_mensal > 0 else 0
                st.metric("Alíquota Efetiva", f"{aliquota_efetiva:.1f}%")

# Rodapé
st.markdown("---")
st.markdown("💡 **Sistema em desenvolvimento** - Funcionalidades avançadas em implementação!")
