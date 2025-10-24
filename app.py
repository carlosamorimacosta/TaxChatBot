import streamlit as st
import PyPDF2
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import os
import time

# Configuração da página
st.set_page_config(
    page_title="Tax Chatbot FGV",
    page_icon="🤖",
    layout="wide"
)

class TaxDocumentProcessor:
    def __init__(self):
        self.documents_path = "documents"
        self.vector_store = None
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto de arquivos PDF"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Página {page_num + 1} ---\n{page_text}\n\n"
        except Exception as e:
            st.warning(f"Erro com pdfplumber em {os.path.basename(pdf_path)}: {e}")
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"--- Página {page_num + 1} ---\n{page_text}\n\n"
            except Exception as e2:
                st.error(f"Erro crítico no PDF {os.path.basename(pdf_path)}: {e2}")
                return ""
        
        return text

    def load_and_process_documents(self):
        """Carrega e processa todos os PDFs da pasta documents"""
        # Verifica se a pasta documents existe
        if not os.path.exists(self.documents_path):
            st.error(f"❌ Pasta '{self.documents_path}' não encontrada!")
            st.info("👉 Crie uma pasta chamada 'documents' e adicione os PDFs lá")
            return None
        
        # Lista todos os PDFs
        pdf_files = [f for f in os.listdir(self.documents_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            st.error(f"❌ Nenhum arquivo PDF encontrado na pasta '{self.documents_path}'")
            st.info("👉 Adicione arquivos PDF na pasta 'documents'")
            return None
        
        st.success(f"📚 Encontrados {len(pdf_files)} documentos PDF")
        
        all_texts = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Processa cada PDF
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(self.documents_path, pdf_file)
            status_text.text(f"📖 Processando: {pdf_file}...")
            
            text = self.extract_text_from_pdf(pdf_path)
            if text and len(text.strip()) > 50:
                all_texts.append(text)
                st.info(f"✅ {pdf_file} - {len(text)} caracteres extraídos")
            else:
                st.warning(f"⚠️ {pdf_file} - Pouco texto extraído ou PDF pode ser imagem")
            
            progress_bar.progress((i + 1) / len(pdf_files))
        
        status_text.text("✅ Processamento concluído!")
        return all_texts

    def create_vector_store(self, texts):
        """Cria o vector store a partir dos textos"""
        if not texts:
            return None
        
        with st.spinner("🔧 Dividindo textos em partes menores..."):
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
                length_function=len
            )
            
            chunks = []
            for text in texts:
                chunks.extend(text_splitter.split_text(text))
            
            st.info(f"📝 Criados {len(chunks)} segmentos de texto")

        with st.spinner("🧠 Criando representações numéricas do texto..."):
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            vector_store = FAISS.from_texts(chunks, embeddings)
        
        return vector_store

def initialize_system():
    """Inicializa o sistema completo"""
    st.title("🤖 Tax Chatbot FGV - Legislação Tributária")
    st.markdown("---")
    
    # Verifica se já está inicializado
    if 'initialized' in st.session_state and st.session_state.initialized:
        st.sidebar.success("✅ Sistema já inicializado")
        return st.session_state.vector_store
    
    # Processo de inicialização
    with st.expander("🔧 Status do Sistema", expanded=True):
        st.info("Inicializando sistema...")
        
        processor = TaxDocumentProcessor()
        
        with st.spinner("📂 Carregando documentos..."):
            texts = processor.load_and_process_documents()
            
            if not texts:
                st.error("🚫 Não foi possível carregar os documentos")
                return None
            
            st.success(f"📄 {len(texts)} documentos carregados com sucesso")
        
        with st.spinner("🤖 Preparando base de conhecimento..."):
            vector_store = processor.create_vector_store(texts)
            
            if vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.initialized = True
                st.success("✅ Sistema inicializado com sucesso!")
                return vector_store
            else:
                st.error("❌ Falha ao criar base de conhecimento")
                return None

def main():
    """Função principal da aplicação"""
    
    # Inicializa o sistema
    vector_store = initialize_system()
    
    if vector_store is None:
        st.error("""
        ❌ **Sistema não pode ser inicializado**
        
        **Soluções possíveis:**
        1. Crie uma pasta chamada `documents` na raiz do projeto
        2. Adicione arquivos PDF com texto extraível na pasta `documents`
        3. Verifique se os PDFs não são apenas imagens
        4. Execute `pip install -r requirements.txt` para instalar dependências
        """)
        return
    
    # Sidebar com informações
    st.sidebar.title("📊 Informações do Sistema")
    st.sidebar.success("✅ Sistema operacional")
    st.sidebar.info("""
    **Documentos Carregados:**
    - Legislação Tributária
    - Código Tributário
    - Leis Fiscais
    - Regulamentos
    """)
    
    # Área principal de perguntas
    st.header("💬 Faça sua pergunta tributária")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_area(
            "**Descreva sua dúvida:**",
            placeholder="Ex: Qual a alíquota do Imposto de Renda para pessoa jurídica em 2024?",
            height=120
        )
    
    with col2:
        st.markdown("### 💡 Dicas")
        st.markdown("""
        - Seja específico
        - Menção artigos/laws
        - Contextualize a situação
        """)
        
        search_type = st.selectbox(
            "Tipo de busca:",
            ["Padrão", "Estrita", "Ampla"]
        )
    
    # Botão de consulta
    if st.button("🔍 Consultar Legislação", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("⚠️ Por favor, digite uma pergunta")
            return
        
        with st.spinner("🔎 Consultando base legislativa..."):
            # Busca documentos relevantes
            k = 3 if search_type == "Estrita" else 5 if search_type == "Ampla" else 4
            docs = vector_store.similarity_search(question, k=k)
            
            # Prepara contexto
            context = "\n\n".join([f"**Documento {i+1}:**\n{doc.page_content}" 
                                 for i, doc in enumerate(docs)])
            
            # Gera resposta
            response = generate_legal_response(question, context)
            
            # Exibe resultados
            st.markdown("## 📋 Resposta Legal")
            st.success(response)
            
            # Mostra fontes
            with st.expander("📚 Fontes Consultadas", expanded=False):
                for i, doc in enumerate(docs):
                    st.markdown(f"### 📄 Fonte {i+1}")
                    st.text(doc.page_content)
                    st.markdown("---")

def generate_legal_response(question, context):
    """Gera resposta baseada na legislação"""
    # SIMULAÇÃO - SUBSTITUA POR SEU MODELO LLM REAL
    
    prompt = f"""
    PERGUNTA DO USUÁRIO: {question}
    
    CONTEXTO LEGAL ENCONTRADO:
    {context}
    
    Por favor, forneça uma resposta técnica e precisa baseada exclusivamente no contexto fornecido.
    """
    
    # Resposta simulada - SUBSTITUA ISSO!
    resposta = f"""
    **Análise da Consulta:** "{question}"

    **Base Legal Consultada:**
    Foram analisados {len(context.split('**Documento'))-1} documentos da base legislativa tributária.

    **Resposta Técnica:**
    Com base na legislação tributária consultada, as informações relevantes foram extraídas dos documentos oficiais. Para uma resposta específica sobre alíquotas, prazos, obrigações acessórias ou procedimentos fiscais, recomenda-se a consulta direta aos artigos e dispositivos legais mencionados nas fontes.

    **Observação:** Esta é uma resposta simulada. Integre com seu modelo LLM para respostas precisas.

    *Fonte: Base de documentos tributários processados.*
    """
    
    return resposta

# Rodar a aplicação
if __name__ == "__main__":
    main()