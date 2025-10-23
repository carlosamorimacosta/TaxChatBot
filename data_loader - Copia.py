import os
import glob
from typing import List

try:
    # Tentar imports da versão mais recente
    from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
except ImportError:
    # Fallback para versões mais antigas
    try:
        from langchain.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import FAISS
        from langchain.schema import Document
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("📦 Execute: pip install langchain-community faiss-cpu")

def load_documents() -> List[Document]:
    """
    Carrega todos os documentos PDF e MD da pasta docs/
    """
    documents = []
    docs_path = "docs"
    
    # Criar pasta docs se não existir
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"📁 Pasta '{docs_path}' criada. Adicione seus arquivos PDF e MD lá!")
        return documents
    
    # Carregar arquivos PDF
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    for pdf_file in pdf_files:
        try:
            print(f"📄 Processando PDF: {os.path.basename(pdf_file)}")
            loader = PyPDFLoader(pdf_file)
            pdf_docs = loader.load()
            documents.extend(pdf_docs)
            print(f"✅ PDF processado: {len(pdf_docs)} páginas")
        except Exception as e:
            print(f"❌ Erro ao processar {pdf_file}: {e}")
    
    # Carregar arquivos Markdown
    md_files = glob.glob(os.path.join(docs_path, "*.md"))
    for md_file in md_files:
        try:
            print(f"📝 Processando MD: {os.path.basename(md_file)}")
            loader = UnstructuredMarkdownLoader(md_file)
            md_docs = loader.load()
            documents.extend(md_docs)
            print(f"✅ MD processado: {len(md_docs)} seções")
        except Exception as e:
            print(f"❌ Erro ao processar {md_file}: {e}")
    
    print(f"📊 Total de documentos carregados: {len(documents)}")
    return documents

def split_documents(documents: List[Document]) -> List[Document]:
    """
    Divide os documentos em chunks menores para melhor processamento
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Documentos divididos em {len(chunks)} chunks")
    return chunks

def create_vector_store(documents: List[Document] = None) -> FAISS:
    """
    Cria ou carrega o banco vetorial FAISS
    """
    faiss_path = "faiss_index"
    
    # Se não foram passados documentos, tenta carregar o banco existente
    if documents is None:
        if os.path.exists(faiss_path):
            print("🔄 Carregando banco vetorial existente...")
            return load_vector_store()
        else:
            print("❌ Nenhum banco vetorial encontrado. Carregue documentos primeiro.")
            return None
    
    # Processar documentos
    chunks = split_documents(documents)
    
    if not chunks:
        print("⚠️ Nenhum chunk para processar.")
        return None
    
    # Criar embeddings
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except Exception as e:
        print(f"❌ Erro ao criar embeddings: {e}")
        return None
    
    # Criar banco vetorial FAISS
    print("🏗️ Criando banco vetorial FAISS...")
    try:
        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings
        )
        
        # Salvar o banco
        vector_store.save_local(faiss_path)
        print(f"💾 Banco vetorial salvo em '{faiss_path}' com {len(chunks)} chunks")
        
        return vector_store
    except Exception as e:
        print(f"❌ Erro ao criar banco vetorial: {e}")
        return None

def load_vector_store():
    """
    Carrega um banco vetorial existente
    """
    faiss_path = "faiss_index"
    
    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"Banco vetorial não encontrado em '{faiss_path}'")
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        vector_store = FAISS.load_local(
            faiss_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        print(f"📂 Banco vetorial carregado: {vector_store.index.ntotal} documentos")
        return vector_store
    except Exception as e:
        print(f"❌ Erro ao carregar banco vetorial: {e}")
        return None

def get_document_count() -> int:
    """
    Retorna o número de documentos no banco vetorial
    """
    try:
        vector_store = load_vector_store()
        if vector_store:
            return vector_store.index.ntotal
        return 0
    except:
        return 0

# Teste do módulo
if __name__ == "__main__":
    print("🧪 Testando data_loader...")
    docs = load_documents()
    if docs:
        vector_store = create_vector_store(docs)
        if vector_store:
            print("✅ Data loader testado com sucesso!")
        else:
            print("❌ Falha ao criar vector store")
    else:
        print("ℹ️ Nenhum documento encontrado para teste.")