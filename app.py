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
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBR0HGB-psvreNN16boqWLRki4quGGp1Es")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "AIzaSyBR0HGB-psvreNN16boqWLRki4quGGp1Es")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "050533600bafd48d3")

# === 🌐 Integração com Busca na Web (Google Custom Search) ===
import requests

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

def buscar_na_web(query, num_results=3):
    """Busca na web usando Google Programmable Search Engine."""
    url = (
        f"https://www.googleapis.com/customsearch/v1?"
        f"key={GOOGLE_SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
    )
    try:
        resp = requests.get(url)
        data = resp.json()
        results = []
        if "items" in data:
            for item in data["items"][:num_results]:
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"{snippet}\n🔗 {link}")
        return "\n\n".join(results)
    except Exception as e:
        return f"⚠️ Erro na busca online: {e}"

# Configura o Gemini apenas com a chave válida
genai.configure(api_key=GEMINI_API_KEY)

# Configuração da página
st.set_page_config(
    page_title="Taxbot FGV - Especialista Tributário",
    page_icon="🤖",
    layout="wide"
)

# Configuração do Gemini 
GEMINI_API_KEY = "AIzaSyBR0HGB-psvreNN16boqWLRki4quGGp1Es"  

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
        """Extrai texto de arquivos PDF com tratamento para tabelas e limpeza de formatação"""
        import pdfplumber
        import PyPDF2
        import re
        text = ""
    
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extrai texto normal
                    page_text = page.extract_text() or ""
    
                    # Extrai tabelas (se houver)
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Junta células com espaço e linhas com \n
                            table_text = "\n".join([
                                " | ".join([str(cell) if cell is not None else "" for cell in row])
                                for row in table if any(row)
                            ])
                            page_text += "\n\n[TABELA DETECTADA]\n" + table_text + "\n"
    
                    # Limpeza de formatação
                    page_text = re.sub(r'\s+', ' ', page_text)  # remove quebras de linha e espaços extras
                    page_text = page_text.replace("‐", "-")      # substitui traços especiais
    
                    if len(page_text.strip()) > 20:
                        text += page_text.strip() + "\n\n"
    
        except Exception as e:
            st.warning(f"⚠️ Falha com pdfplumber ({os.path.basename(pdf_path)}): {e}")
            # Fallback leve com PyPDF2
            try:
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += re.sub(r'\s+', ' ', page_text) + "\n"
            except Exception as e2:
                st.error(f"❌ Erro ao extrair texto com PyPDF2: {e2}")
                return ""
    
        return text.strip()

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
        persist_dir = "./chroma_db"
        os.makedirs(persist_dir, exist_ok=True)
    
        # ✅ Se já existe uma base persistida, apenas recarrega
        if os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
            try:
                st.info("🔁 Recarregando base vetorial existente...")
                embeddings = load_embeddings()
                vector_store = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
                st.success("✅ Base vetorial recarregada com sucesso!")
                return vector_store
            except Exception as e:
                st.warning(f"Falha ao recarregar base existente: {e}")
    
        # Se chegou aqui, é porque precisa criar do zero
        if not documents:
            st.error("Nenhum documento para indexar.")
            return None
    
        # ✅ Combina todos os textos
        texts = [doc['content'] for doc in documents if len(doc['content'].strip()) > 50]
    
        # ✅ Divide os textos em blocos
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", ".", "!", "?", ";", ":", "\n", " "],
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len
        )

        chunks = []
        for text in texts:
            pieces = text_splitter.split_text(text)
            chunks.extend(pieces)
    
        st.write(f"🧩 {len(chunks)} blocos de texto criados para embeddings.")
    
        # ✅ Cria embeddings e base vetorial
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L12-v2",
                cache_folder="./models"
            )
    
            persist_dir = "./chroma_db"
            os.makedirs(persist_dir, exist_ok=True)


            vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=embeddings,
                persist_directory=persist_dir
            )
            vector_store.persist()
            st.success("✅ Base vetorial criada e salva com sucesso!")
            return vector_store
    
        except Exception as e:
            st.error(f"❌ Erro ao criar embeddings: {e}")
            return None


    def search_relevant_documents(self, question, k=5):
        """Busca documentos relevantes para a pergunta"""
        if not self.vector_store:
            st.error("❌ Base vetorial não inicializada.")
            return []
    
        try:
            results = self.vector_store.similarity_search(question, k=k)
            if not results:
                st.warning("⚠️ Nenhum trecho relevante encontrado.")
            else:
                st.info(f"📄 {len(results)} trechos relevantes localizados.")
            return results
        except Exception as e:
            st.error(f"Erro na busca semântica: {e}")
            return []

    def rerank_results(self, question, results, embeddings):
        """Reordena resultados usando cosine similarity entre query e textos retornados."""
        try:
            # extrai textos dos resultados (ajuste conforme estrutura do objeto retornado pelo Chroma)
            doc_texts = []
            for r in results:
                # se for objeto com page_content (langchain), ou simples string
                if hasattr(r, "page_content"):
                    doc_texts.append(r.page_content)
                elif isinstance(r, dict) and "page_content" in r:
                    doc_texts.append(r["page_content"])
                elif isinstance(r, str):
                    doc_texts.append(r)
                else:
                    # tenta acessar .metadata / .content
                    doc_texts.append(str(r))

            # calcula vetores
            # HuggingFaceEmbeddings pode ter embed_query ou embed_documents
            if hasattr(embeddings, "embed_query"):
                q_vec = embeddings.embed_query(question)
                doc_vecs = embeddings.embed_documents(doc_texts)
            else:
                # fallback genérico
                doc_vecs = embeddings.embed_documents(doc_texts)
                # para q_vec usamos embed_documents em lista de 1
                q_vec = embeddings.embed_documents([question])[0]

            # cosine similarity (manual)
            import numpy as np
            from numpy.linalg import norm

            sims = []
            for dv in doc_vecs:
                dv_arr = np.array(dv, dtype=float)
                q_arr = np.array(q_vec, dtype=float)
                denom = (norm(dv_arr) * norm(q_arr))
                sim = float(np.dot(q_arr, dv_arr) / denom) if denom != 0 else 0.0
                sims.append(sim)

            # ordenar índices decrescentes
            idx_sorted = list(sorted(range(len(sims)), key=lambda i: sims[i], reverse=True))
            reranked = [results[i] for i in idx_sorted]
            return reranked

        except Exception as e:
            st.warning(f"Rerank falhou: {e}")
            return results

        def web_search(self, query, max_results=3):
            """Busca rápida na web para complementar informações."""
            import requests
    
            GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
            SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
    
            if not GOOGLE_SEARCH_API_KEY or not SEARCH_ENGINE_ID:
                return "⚠️ Busca web não configurada."
    
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": SEARCH_ENGINE_ID,
                "q": query,
                "num": max_results,
                "hl": "pt-BR"
            }
    
            try:
                res = requests.get(url, params=params, timeout=10)
                res.raise_for_status()
                data = res.json()
                results = []
                for item in data.get("items", []):
                    title = item.get("title")
                    snippet = item.get("snippet")
                    link = item.get("link")
                    results.append(f"**{title}**\n{snippet}\n🔗 {link}")
                return "\n\n".join(results)
            except Exception as e:
                return f"⚠️ Erro ao buscar na web: {e}"




    def generate_ai_response(self, question, context, conversation_history=[]):
        """Gera resposta usando Gemini AI com contexto, fallback seguro e busca na web se necessário"""

        # Reforço automático para perguntas curtas
        if not question or len(question.strip()) < 10:
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

        # 🔍 Busca opcional na internet se a pergunta for sobre algo recente
        if any(term in question.lower() for term in ["2024", "2025", "atual", "reforma", "nova lei", "mudança", "últimas"]):
            try:
                st.info("🌐 Buscando informações atualizadas na internet...")
                web_results = self.web_search(question)
                if web_results and "⚠️" not in web_results:
                    context += f"\n\n📡 INFORMAÇÕES ATUALIZADAS (WEB):\n{web_results}"
                else:
                    st.warning("Nenhum resultado recente encontrado na web.")
            except Exception as e:
                st.warning(f"Falha na busca web: {e}")

        # 🔐 Segurança e robustez — garante que o modelo existe
        if not hasattr(self, "model") or self.model is None:
            st.error("❌ O modelo Gemini não foi inicializado corretamente.")
            return "Erro: o modelo Gemini não está configurado. Verifique sua API Key e reinicie o sistema."
    
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
- Não emita opiniões pessoais.
- Mantenha tom profissional e neutro.
"""

        # 🧠 Geração segura da resposta
        try:
            response = self.model.generate_content(prompt)

            if response is None:
                return "⚠️ Nenhuma resposta foi retornada pela IA."

            # 🔎 Caso tenha o atributo direto .text
            if hasattr(response, "text") and response.text:
                return response.text.strip()

            # 🧩 Caso a resposta venha via 'candidates'
            if hasattr(response, "candidates") and len(response.candidates) > 0:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, "finish_reason", None)

                # ✅ Caso normal
                if (
                    hasattr(candidate, "content")
                    and hasattr(candidate.content, "parts")
                    and len(candidate.content.parts) > 0
                    and hasattr(candidate.content.parts[0], "text")
                ):
                    return candidate.content.parts[0].text.strip()

                # ⚠️ Caso bloqueado pelo filtro de segurança
                if str(finish_reason) == "2":
                    st.warning("⚠️ Resposta bloqueada pelo filtro de segurança. Reenviando com prompt seguro...")
                    safe_prompt = (
                        f"Responda de forma neutra e informativa, sem emitir julgamentos. "
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

    #animação
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #2563eb;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: 600;
        transition: 0.3s;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #1e40af;
        transform: scale(1.03);
        box-shadow: 0 0 10px rgba(37, 99, 235, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

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
                st.markdown(
                    f"""
                    <div style="
                        font-family: 'Segoe UI', Roboto, sans-serif;
                        font-size: 16px;
                        line-height: 1.6;
                        color: #f8f8f8;
                        background-color: #111827;
                        padding: 16px;
                        border-radius: 10px;
                        white-space: pre-wrap;
                    ">
                        {response.replace('\n', '<br>')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                
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
