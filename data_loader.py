import os
import glob
import streamlit as st
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdfplumber

# Classe Document própria
class Document:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Document(page_content='{self.page_content[:60]}...', metadata={self.metadata})"


# -----------------------------
# ⚡ Função de cache (para evitar reprocessamento)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_documents():
    """
    Carrega todos os PDFs da pasta 'documents/' e armazena cache
    para evitar reprocessar a cada pergunta.
    Também faz chunking e gera resumo por documento.
    """
    print("🔧 Iniciando carregamento de documentos PDF...")
    documents = []
    docs_path = "documents"

    # Criar pasta se não existir
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"📁 Pasta '{docs_path}' criada.")
        return documents

    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    print(f"📄 PDFs encontrados: {len(pdf_files)}")

    if not pdf_files:
        print("❌ Nenhum PDF encontrado em 'documents'.")
        return documents

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # tamanho máximo de tokens por chunk
        chunk_overlap=200,
        length_function=len,
    )

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"📖 Processando: {filename}")

        try:
            # Ler o texto de cada PDF
            all_text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    all_text += page.extract_text() or ""

            if not all_text.strip():
                print(f"⚠️ Nenhum texto encontrado em {filename}.")
                continue

            # Dividir em chunks
            chunks = text_splitter.split_text(all_text)
            print(f"✂️ {filename}: {len(chunks)} chunks gerados.")

            # Criar Document para cada chunk
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk.strip(),
                    metadata={
                        "source": pdf_file,
                        "filename": filename,
                        "chunk": i + 1,
                        "total_chunks": len(chunks),
                    },
                )
                documents.append(doc)

        except Exception as e:
            print(f"❌ Erro ao processar {filename}: {e}")

    print(f"📊 Total de chunks/documentos carregados: {len(documents)}")
    return documents
def summarize_documents(docs, llm):
    summaries = []
    for doc in docs:
        summary = llm.invoke(f"Resuma brevemente o documento: {doc.page_content[:2000]}")
        summaries.append({"file": doc.metadata.get("filename"), "summary": summary.content})
    return summaries
    
    if st.button("Gerar resumos"):
        summaries = summarize_documents(documents, llm)
    st.json(summaries)



# -----------------------------
# ⚙️ Funções de vetor e armazenamento
# -----------------------------
@st.cache_resource(show_spinner=False)
def create_vector_store(documents=None):
    """
    Simula criação de vetores e mantém cache persistente.
    """
    print("🔧 create_vector_store: Função simplificada com cache")

    if not documents:
        print("⚠️ Nenhum documento fornecido para criar vector store")
        return None

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def create_vector_store(documents):
        print("🔧 Criando vector store REAL com ChromaDB...")
    
        embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
    
        vector_store = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding_function=embedder,
            persist_directory="db"   # <--- PASTA DO CHROMA
        )
    
        vector_store.persist()
        print("✅ Vector store criado e persistido em /db")
    
        return vector_store



def load_vector_store():
    print("💾 Carregando vector store do ChromaDB...")

    embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    if not os.path.exists("db"):
        print("⚠️ Nenhum vector store encontrado, crie um novo.")
        return None

    vector_store = Chroma(
        persist_directory="db",
        embedding_function=embedder
    )

    print("✅ Vector store carregado do disco.")
    return vector_store



def get_document_count():
    """
    Retorna o número de PDFs disponíveis
    """
    docs_path = "documents"
    if os.path.exists(docs_path):
        pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
        return len(pdf_files)
    return 0


# -----------------------------
# 🧪 Teste local do módulo
# -----------------------------
if __name__ == "__main__":
    print("🧪 Testando data_loader com chunking e cache...")
    print("=" * 60)

    doc_count = get_document_count()
    print(f"📁 PDFs na pasta 'documents': {doc_count}")

    docs = load_documents()
    print(f"📚 Documentos/chunks carregados: {len(docs)}")

    if docs:
        store = create_vector_store(docs)
        if store:
            print("✅ Vector store criado com sucesso!")

    print("🎯 Teste concluído!")
