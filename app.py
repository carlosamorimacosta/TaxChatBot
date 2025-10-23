import streamlit as st
import os
from data_loader import load_documents, create_vector_store, load_vector_store, get_document_count

# -----------------------------
# 🎨 Configuração da página
# -----------------------------
st.set_page_config(
    page_title="TaxBot - Assistente Fiscal",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 🏷️ Título e introdução
# -----------------------------
st.title("🤖 TaxBot - Assistente Fiscal Inteligente")
st.markdown("Analisando documentos fiscais baixados no notebook 📚")

# -----------------------------
# 💾 Inicialização do estado
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents_processed" not in st.session_state:
    st.session_state.documents_processed = False

# -----------------------------
# 🧭 Sidebar - Controle e status
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Upload de arquivos PDF
    uploaded_files = st.file_uploader(
        "📎 Fazer upload de PDFs fiscais",
        type=['pdf'],
        accept_multiple_files=True,
        help="Faça upload dos PDFs baixados no notebook"
    )
    
    if uploaded_files:
        os.makedirs("docs", exist_ok=True)
        for uploaded_file in uploaded_files:
            file_path = os.path.join("docs", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"✅ {len(uploaded_files)} PDF(s) salvo(s) na pasta 'docs'!")
    
    # Botão para processar documentos
    if st.button("🔄 Processar Documentos PDF"):
        with st.spinner("Carregando e processando PDFs..."):
            try:
                documents = load_documents()
                if documents:
                    st.session_state.documents_processed = True
                    st.success(f"✅ {len(documents)} documentos PDF processados!")
                    
                    # Exibir lista de documentos carregados
                    with st.expander("📋 Ver documentos carregados"):
                        for doc in documents:
                            st.write(f"**Arquivo:** {doc.metadata.get('filename', 'N/A')}")
                            st.write(f"**Página:** {doc.metadata.get('page', 'N/A')}")
                            st.markdown("---")
                else:
                    st.warning("⚠️ Nenhum PDF encontrado para processar.")
            except Exception as e:
                st.error(f"❌ Erro ao processar documentos: {e}")
    
    # Informações do sistema
    st.markdown("---")
    st.header("📊 Status do Sistema")
    
    doc_count = get_document_count()
    st.write(f"📁 PDFs na pasta 'docs': {doc_count}")
    st.write(f"🔧 Processado: {'✅' if st.session_state.documents_processed else '❌'}")
    
    # Botão para limpar chat
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# 💬 Área principal do chat
# -----------------------------
st.header("💬 Chat com Documentos Fiscais")

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
if prompt := st.chat_input("Pergunte sobre os documentos fiscais..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Geração de resposta
    with st.chat_message("assistant"):
        if st.session_state.documents_processed:
            resposta = (
                f"**Analisando sua pergunta sobre:** '{prompt}'\n\n"
                "📚 **Documentos disponíveis para consulta:**\n"
                "- Lei 7.713/88 e alterações\n"
                "- Projetos de lei sobre IR\n"
                "- Estudos sobre impactos tributários\n"
                "- Análises de progressividade fiscal\n\n"
                "💡 *Sistema em desenvolvimento — Em breve respostas precisas baseadas nos PDFs.*"
            )
        else:
            resposta = (
                "❌ **Por favor, processe os documentos PDF primeiro!**\n\n"
                "1. Faça upload dos PDFs baixados no notebook\n"
                "2. Clique em **'Processar Documentos PDF'**\n"
                "3. Depois faça suas perguntas sobre o conteúdo"
            )
        
        st.markdown(resposta)
        st.session_state.messages.append({"role": "assistant", "content": resposta})

# -----------------------------
# 📎 Rodapé
# -----------------------------
st.markdown("---")
st.markdown("💡 **Instruções:** Faça upload dos PDFs baixados no notebook e clique em 'Processar Documentos PDF' para começar!")
