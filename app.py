import streamlit as st
import PyPDF2
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import os
import google.generativeai as genai
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Tax Chatbot FGV - Especialista Tributário",
    page_icon="🤖",
    layout="wide"
)

# Configuração do Gemini 
GEMINI_API_KEY = "AIzaSyAiZS9q4IZ3TfxI5GCIX8p_g3P_nmHisL4I"  

class TaxAIChatbot:
    def __init__(self):
        self.documents_path = "documents"
        self.vector_store = None
        self.setup_gemini()
    
    def setup_gemini(self):
        """Configura a API do Gemini"""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            return True
        except Exception as e:
            st.error(f"Erro na configuração do Gemini: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto de arquivos PDF"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                st.error(f"Erro no PDF {os.path.basename(pdf_path)}: {e2}")
                return ""
        return text

    def load_and_process_documents(self):
        """Carrega e processa todos os PDFs"""
        if not os.path.exists(self.documents_path):
            st.error(f"❌ Pasta '{self.documents_path}' não encontrada!")
            return None
        
        pdf_files = [f for f in os.listdir(self.documents_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            st.error("❌ Nenhum PDF encontrado")
            return None
        
        all_texts = []
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.documents_path, pdf_file)
            text = self.extract_text_from_pdf(pdf_path)
            if text and len(text.strip()) > 50:
                all_texts.append({
                    'filename': pdf_file,
                    'content': text,
                    'size': len(text)
                })
                st.success(f"✅ {pdf_file} - {len(text)} caracteres")
        
        return all_texts

    def create_vector_store(self, documents):
        """Cria o vector store para busca semântica"""
        if not documents:
            return None
        
        texts = [doc['content'] for doc in documents]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        
        chunks = []
        for text in texts:
            chunks.extend(text_splitter.split_text(text))
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        vector_store = FAISS.from_texts(chunks, embeddings)
        return vector_store

    def search_relevant_documents(self, question, k=5):
        """Busca documentos relevantes para a pergunta"""
        if not self.vector_store:
            return []
        
        docs = self.vector_store.similarity_search(question, k=k)
        return docs

    def generate_ai_response(self, question, context, conversation_history=[]):
        """Gera resposta usando Gemini AI com contexto específico"""
        
        # Prepara o histórico de conversa
        history_text = ""
        if conversation_history:
            history_text = "\nHistórico recente:\n"
            for msg in conversation_history[-4:]:  # Últimas 4 mensagens
                history_text += f"{msg['role']}: {msg['content']}\n"
        
        prompt = f"""
        VOCÊ É: Um especialista em legislação tributária brasileira, trabalhando para a FGV.
        
        CONTEXTO LEGAL DISPONÍVEL:
        {context}
        
        {history_text}
        
        PERGUNTA ATUAL: {question}
        
        INSTRUÇÕES ESPECÍFICAS:
        
        1. **SE A PERGUNTA FOR SOBRE TRIBUTAÇÃO:**
           - Baseie-se STRITAMENTE no contexto fornecido
           - Cite artigos, leis e dispositivos específicos quando possível
           - Seja técnico, preciso e atual
           - Formate a resposta de forma clara com tópicos se necessário
        
        2. **SE A PERGUNTA NÃO ENCONTRAR BASE NO CONTEXTO:**
           - Identifique que a informação específica não está nos documentos carregados
           - Ofereça uma explicação geral baseada em conhecimentos tributários
           - Sugira onde o usuário poderia encontrar essa informação
           - Seja honesto sobre as limitações
        
        3. **SE A PERGUNTA FOR FORA DO CONTEXTO TRIBUTÁRIO:**
           - Eduque gentilmente o usuário sobre o escopo do chatbot
           - Ofereça redirecionamento para questões tributárias
           - Mantenha-se profissional e útil
        
        4. **FORMATO DA RESPOSTA:**
           - Seja direto e objetivo
           - Use marcadores para listas
           - Destaque termos importantes em **negrito**
           - Inclua referências quando aplicável
        
        RESPOSTA:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Erro na geração da resposta: {str(e)}"

def initialize_system():
    """Inicializa o sistema completo"""
    st.title("🤖 Tax Chatbot FGV - Especialista em Tributação")
    st.markdown("---")
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = TaxAIChatbot()
        st.session_state.initialized = False
        st.session_state.conversation_history = []
    
    chatbot = st.session_state.chatbot
    
    # Inicialização do sistema
    if not st.session_state.initialized:
        with st.expander("🔧 Inicialização do Sistema", expanded=True):
            st.info("🔄 Iniciando sistema de IA tributária...")
            
            # Configura Gemini
            if not chatbot.setup_gemini():
                st.error("❌ Falha na configuração da IA")
                return None
            
            # Carrega documentos
            with st.spinner("📂 Carregando documentos tributários..."):
                documents = chatbot.load_and_process_documents()
                
                if not documents:
                    st.error("🚫 Não foi possível carregar documentos")
                    return None
                
                st.success(f"📚 {len(documents)} documentos carregados")
            
            # Cria vector store
            with st.spinner("🧠 Criando base de conhecimento..."):
                chatbot.vector_store = chatbot.create_vector_store(documents)
                st.session_state.initialized = True
                st.success("✅ Sistema de IA inicializado com sucesso!")
    
    return chatbot

def main():
    """Função principal"""
    
    chatbot = initialize_system()
    
    if chatbot is None:
        st.error("""
        ❌ **Sistema não pode ser inicializado**
        
        **Verifique:**
        1. API Key do Gemini configurada
        2. Pasta 'documents' com PDFs válidos
        3. Conexão com internet
        """)
        return
    
    # Sidebar
    st.sidebar.title("⚙️ Configurações")
    st.sidebar.success("✅ IA Ativa - Gemini Pro")
    
    # Controles de busca
    st.sidebar.subheader("🔍 Configurações de Busca")
    search_depth = st.sidebar.slider("Profundidade da busca", 3, 8, 5)
    temperature = st.sidebar.slider("Criatividade da resposta", 0.1, 1.0, 0.3)
    
    # Área de chat
    st.header("💬 Consultoria Tributária")
    
    # Histórico de conversa
    if st.session_state.conversation_history:
        st.subheader("📝 Conversa Recente")
        for msg in st.session_state.conversation_history[-6:]:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.write(msg["content"])
    
    # Input da pergunta
    question = st.chat_input("Digite sua pergunta sobre tributação...")
    
    if question:
        # Adiciona pergunta ao histórico
        st.session_state.conversation_history.append({
            "role": "user", 
            "content": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Exibe pergunta do usuário
        with st.chat_message("user"):
            st.write(question)
        
        # Processa a resposta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando legislação..."):
                # Busca documentos relevantes
                relevant_docs = chatbot.search_relevant_documents(question, k=search_depth)
                
                if relevant_docs:
                    context = "\n\n".join([f"📄 Documento {i+1}:\n{doc.page_content}" 
                                         for i, doc in enumerate(relevant_docs)])
                    
                    st.info(f"📚 Encontradas {len(relevant_docs)} fontes relevantes")
                else:
                    context = "Nenhum documento específico encontrado para esta consulta."
                    st.warning("⚠️ Consultando conhecimento geral de tributação")
                
                # Gera resposta com IA
                with st.spinner("🧠 Gerando resposta especializada..."):
                    response = chatbot.generate_ai_response(
                        question, 
                        context, 
                        st.session_state.conversation_history
                    )
                
                # Exibe resposta
                st.success("✅ Resposta baseada em legislação tributária")
                st.write(response)
                
                # Mostrar fontes (expandível)
                with st.expander("📋 Fontes Consultadas"):
                    for i, doc in enumerate(relevant_docs):
                        st.markdown(f"**Fonte {i+1}:**")
                        st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                        st.markdown("---")
        
        # Adiciona resposta ao histórico
        st.session_state.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
    
    # Área de informações
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 Dicas de Uso")
    st.sidebar.info("""
    **Exemplos de perguntas:**
    - "Qual a alíquota do IRPF para 2024?"
    - "Explique o Simples Nacional"
    - "Prazos para declaração do IR"
    - "Diferença entre lucro real e presumido"
    """)
    
    # Estatísticas
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Estatísticas")
    st.sidebar.text(f"💬 Mensagens: {len(st.session_state.conversation_history)}")
    st.sidebar.text(f"📚 Documentos: {len([f for f in os.listdir('documents') if f.endswith('.pdf')])}")

if __name__ == "__main__":
    main()
