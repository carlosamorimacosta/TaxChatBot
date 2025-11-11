import streamlit as st
import PyPDF2
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Carregar variáveis locais (para testes locais)
from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai

load_dotenv()

# 🔑 Corrigido — carrega da variável de ambiente OU usa fallback direto
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyD1HL4mv_8qaQel20_k8x0iPYGrIee7yMk")

# Configura o Gemini apenas com a chave válida
genai.configure(api_key=GEMINI_API_KEY)

# Configuração da página
st.set_page_config(
    page_title="Taxbot FGV - Especialista Tributário",
    page_icon="🤖",
    layout="wide"
)

# Configuração do Gemini 
GEMINI_API_KEY = "AIzaSyD1HL4mv_8qaQel20_k8x0iPYGrIee7yMk"  

class TaxAIChatbot:
    def __init__(self):
        self.documents_path = "documents"
        self.vector_store = None
        self.setup_gemini()
    
    def setup_gemini(self):
        """Configura a API do Gemini com fallback automático para versões mais recentes."""
        try:
            genai.configure(api_key=GEMINI_API_KEY)

            # Lista os modelos disponíveis na conta
            available_models = [m.name for m in genai.list_models()]

            # Preferência: tenta o modelo mais novo e rápido
            if "models/gemini-2.5-flash" in available_models:
                chosen_model = "models/gemini-2.5-flash"
            elif "models/gemini-2.5-pro" in available_models:
                chosen_model = "models/gemini-2.5-pro"
            elif "models/gemini-pro-latest" in available_models:
                chosen_model = "models/gemini-pro-latest"
            else:
                # Fallback de segurança
                chosen_model = available_models[0] if available_models else "models/gemini-pro"

            # Cria o modelo
            self.model = genai.GenerativeModel(
                model_name=chosen_model,
                generation_config={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )

            # ✅ Patch de compatibilidade temporário (corrige o erro 'generate_content_stream')
            if not hasattr(self.model, "generate_content_stream"):
                def _no_stream(*args, **kwargs):
                    return self.model.generate_content(*args, **kwargs)
                self.model.generate_content_stream = _no_stream

            print(f"✅ Gemini configurado com modelo rápido ({chosen_model})")
            return True

        except Exception as e:
            st.error(f"Erro na configuração do Gemini: {e}")
            return False



    # 🔹 Cache de extração de texto (evita reprocessar PDFs)
    @st.cache_data
    def extract_text_from_pdf_cached(pdf_path):
        """Extrai texto de um PDF e mantém resultado em cache"""
        import pdfplumber, PyPDF2
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        return text

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
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder="./models"
        )

        
        vector_store = Chroma.from_texts(chunks, embeddings)
        return vector_store

    def search_relevant_documents(self, question, k=5):
        """Busca documentos relevantes para a pergunta"""
        if not self.vector_store:
            return []
        
        docs = self.vector_store.similarity_search(question, k=k)
        return docs

    def generate_ai_response(self, question, context, conversation_history=[]):
        """Gera resposta usando Gemini AI com contexto e tratamento de bloqueios"""

        # Reforço automático para perguntas curtas
        if len(question.strip()) < 10:
            question = (
                f"O usuário perguntou: '{question}'. "
                "Explique o possível significado tributário dessa questão."
            )

        # Histórico da conversa
        history_text = ""
        if conversation_history:
            history_text = "\nHistórico recente:\n"
            for msg in conversation_history[-4:]:
                history_text += f"{msg['role']}: {msg['content']}\n"

        # Prompt estruturado
        prompt = f"""
Você é um especialista em **legislação tributária brasileira**, representando a FGV.

CONTEXTO LEGAL DISPONÍVEL:
{context}

{history_text}

PERGUNTA ATUAL: {question}

INSTRUÇÕES:
- Responda de forma técnica, precisa e objetiva.
- Cite dispositivos legais relevantes.
- Se a resposta não estiver no contexto, diga isso claramente e dê uma explicação geral com base na legislação tributária.
- Não emita opiniões pessoais, apenas informações jurídicas e normativas.
- Sempre mantenha tom profissional e neutro.
"""

        try:
            # Verifica se o modelo está configurado
            if not hasattr(self, "model") or self.model is None:
                st.error("❌ Modelo Gemini não configurado.")
                return "Erro: modelo não configurado."

            # Chama o modelo Gemini
            response = self.model.generate_content(prompt)

            # 🔎 Verifica se veio texto direto
            if hasattr(response, "text") and response.text:
                return response.text.strip()

            # 🧩 Caso o modelo use 'candidates'
            if hasattr(response, "candidates") and len(response.candidates) > 0:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, "finish_reason", None)

                # ✅ Caso normal — resposta presente
                if candidate.content and hasattr(candidate.content.parts[0], "text"):
                    return candidate.content.parts[0].text.strip()

                # ⚠️ Caso bloqueado por safety (finish_reason == 2)
                if str(finish_reason) == "2":
                    st.warning("⚠️ Resposta bloqueada pelo filtro de segurança. Reenviando com prompt seguro...")
                    safe_prompt = (
                        f"Responda de forma neutra e informativa, sem emitir julgamentos ou conselhos. "
                        f"Apenas explique o conceito tributário de forma didática. Pergunta: {question}"
                    )
                    safe_response = self.model.generate_content(safe_prompt)
                    if hasattr(safe_response, "text") and safe_response.text:
                        return safe_response.text.strip()
                    elif hasattr(safe_response, "candidates") and len(safe_response.candidates) > 0:
                        parts = safe_response.candidates[0].content.parts
                        if parts and hasattr(parts[0], "text"):
                            return parts[0].text.strip()
                    return "⚠️ O modelo não pôde responder por razões de segurança."

            # 🧱 Caso nenhuma resposta válida tenha sido retornada
            return "⚠️ O modelo não retornou conteúdo legível."

        except Exception as e:
            st.error(f"⚠️ Erro ao processar resposta do modelo: {e}")
            return f"Erro interno: {e}"




def initialize_system():
    """Inicializa o sistema completo"""
    st.title("🤖 TaxBot FGV - Especialista na Reforma do IRPF")
    # 🔷 Painel de boas-vindas
    st.markdown("""
    <div style="text-align: center; padding: 20px; border-radius: 15px; background-color: #111827; color: #f0f0f0;">
        <h2>🤖 <b>Bem-vindo ao TaxBot FGV</b></h2>
        <p style="font-size: 16px;">
            Seu assistente de <b>consultoria tributária inteligente</b>, desenvolvido para responder com base na 
            <b>legislação brasileira atualizada</b>.
        </p>
        <p style="font-size: 15px; color: #9ca3af;">
            📘 Carregue documentos tributários e consulte dúvidas sobre IRPF, Simples Nacional, Lucro Real e muito mais.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)  # espaçamento visual

# 🔹 Botão de inicialização
if st.button("🚀 Iniciar Sistema de IA Tributária"):
    st.session_state.start_system = True


    # 🔹 Novo: botão de inicialização
    if st.button("🚀 Iniciar Sistema de IA Tributária"):
        st.session_state.start_system = True

    if not st.session_state.get("start_system", False):
        st.info("Clique em **🚀 Iniciar Sistema de IA Tributária** para começar.")
        st.stop()
    
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
            progress = st.progress(0, text="📂 Carregando documentos tributários...")
            with st.spinner("Carregando PDFs..."):
                documents = chatbot.load_and_process_documents()
            progress.progress(40, text="🧠 Criando base de conhecimento...")
                
            if not documents:
                    st.error("🚫 Não foi possível carregar documentos")
                    return None
                
            st.success(f"📚 {len(documents)} documentos carregados")
            
            # Cria vector store
            with st.spinner("🧠 Criando base de conhecimento..."):
                chatbot.vector_store = chatbot.create_vector_store(documents)
                st.session_state.initialized = True
                st.success("✅ Sistema de IA inicializado com sucesso!")

            progress.progress(100, text="✅ Sistema pronto!")
 
    
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
