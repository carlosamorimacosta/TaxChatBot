import streamlit as st
import os
from data_loader import load_documents, create_vector_store, get_document_count
from qa_chain import create_qa_chain

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
if "qa_initialized" not in st.session_state:
    st.session_state.qa_initialized = False
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
    
    # Botão para processar documentos
    if st.button("🔄 Processar Documentos"):
        with st.spinner("Processando documentos..."):
            try:
                documents = load_documents()
                if documents:
                    vector_store = create_vector_store(documents)
                    st.session_state.qa_initialized = False  # Forçar reinicialização
                    st.success(f"✅ {len(documents)} documentos processados!")
                    
                    # Mostrar estatísticas
                    doc_count = get_document_count()
                    st.info(f"📊 Banco vetorial contém: {doc_count} chunks")
                else:
                    st.warning("⚠️ Nenhum documento encontrado na pasta 'docs'")
            except Exception as e:
                st.error(f"❌ Erro ao processar documentos: {e}")
    
    # Informações do sistema
    st.markdown("---")
    st.header("📊 Status do Sistema")
    
    # Contar arquivos na pasta docs
    doc_files = []
    if os.path.exists("docs"):
        doc_files = [f for f in os.listdir("docs") if f.endswith('.pdf')]
    
    st.write(f"📁 Documentos carregados: {len(doc_files)}")
    st.write(f"🤖 QA Inicializada: {'✅' if st.session_state.qa_initialized else '❌'}")
    
    # Botão para limpar chat
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# Abas principais
tab1, tab2 = st.tabs(["💬 Chat Fiscal", "🧮 Calculadora IR"])

with tab1:
    st.header("💬 Faça sua pergunta sobre legislação fiscal")
    
    # Inicializar QA Chain se necessário
    if not st.session_state.qa_initialized:
        try:
            qa_chain = create_qa_chain()
            if qa_chain.initialize():
                st.session_state.qa_initialized = True
                st.sidebar.success("✅ QA Chain inicializada!")
            else:
                st.warning("⚠️ Carregue e processe documentos primeiro")
        except Exception as e:
            st.error(f"❌ Erro ao inicializar QA: {e}")
    
    # Exibir histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Mostrar fontes se for resposta do assistente
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Fontes consultadas"):
                    for source in message["sources"]:
                        st.write(f"**Arquivo:** {os.path.basename(source['source'])}")
                        st.write(f"**Página:** {source['page']}")
                        st.write(f"**Trecho:** {source['content']}")
                        st.markdown("---")
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta sobre impostos, legislação fiscal..."):
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Gerar resposta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando base de conhecimento..."):
                try:
                    if st.session_state.qa_initialized:
                        qa_chain = create_qa_chain()
                        result = qa_chain.ask_question(prompt)
                        
                        # Exibir resposta
                        st.markdown(result["answer"])
                        
                        # Adicionar ao histórico com fontes
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": result["answer"],
                            "sources": result.get("sources", [])
                        })
                    else:
                        error_msg = "❌ Sistema não inicializado. Por favor, carregue e processe documentos primeiro."
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
                        
                except Exception as e:
                    error_msg = f"❌ Erro ao gerar resposta: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

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
            renda_total = salario + outros
            deducao_dependentes = dependentes * 189.59
            total_deducoes = previdencia + pensao + deducao_dependentes
            base_calculo = max(0, renda_total - total_deducoes)
            
            # Cálculo simplificado do IR
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
                st.metric("Renda Total", f"R$ {renda_total:,.2f}")
                st.metric("Total Deduções", f"R$ {total_deducoes:,.2f}")
            
            with col2:
                st.metric("Base de Cálculo", f"R$ {base_calculo:,.2f}")
                st.metric("IR Devido", f"R$ {ir_devido:,.2f}")
            
            with col3:
                aliquota_efetiva = (ir_devido / renda_total * 100) if renda_total > 0 else 0
                st.metric("Alíquota Efetiva", f"{aliquota_efetiva:.1f}%")
                st.metric("Salário Líquido", f"R$ {renda_total - ir_devido:,.2f}")

# Rodapé
st.markdown("---")
st.markdown("💡 **Dica:** Faça upload de documentos fiscais e clique em 'Processar Documentos' para ativar o chat inteligente!")
