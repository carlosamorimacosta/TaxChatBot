import os
import glob

# Classe Document própria para evitar dependências externas
class Document:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Document(page_content='{self.page_content[:50]}...', metadata={self.metadata})"


def load_documents():
    """
    Carrega todos os documentos PDF da pasta documents/
    Foca apenas nos PDFs baixados no notebook
    """
    print("🔧 Iniciando carregamento de documentos PDF...")
    documents = []
    docs_path = "documents"  # MUDADO: de "docs" para "documents"
    
    # Criar pasta documents se não existir
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"📁 Pasta '{docs_path}' criada.")
        print("💡 Adicione os PDFs baixados no notebook nesta pasta!")
        return documents
    
    # Buscar APENAS arquivos PDF (ignorar MD e outros)
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    print(f"📄 PDFs encontrados na pasta 'documents': {len(pdf_files)}")  # MUDADO
    
    # Listar os arquivos encontrados
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   {i}. {os.path.basename(pdf_file)}")
    
    # Se não há PDFs, retornar lista vazia
    if not pdf_files:
        print("❌ Nenhum arquivo PDF encontrado na pasta 'documents'")  # MUDADO
        print("💡 Faça o download dos PDFs no notebook e salve na pasta 'documents'")  # MUDADO
        return documents
    
    # Simular carregamento dos PDFs (versão simplificada)
    for pdf_file in pdf_files:
        try:
            filename = os.path.basename(pdf_file)
            print(f"📖 Processando: {filename}")
            
            # Criar documento simulado com conteúdo básico
            doc = Document(
                page_content=f"Conteúdo do documento fiscal: {filename}. Este é um placeholder até implementarmos o carregamento real de PDF.",
                metadata={
                    "source": pdf_file,
                    "filename": filename,
                    "page": 1,
                    "file_type": "pdf"
                }
            )
            documents.append(doc)
            print(f"   ✅ {filename} - Carregado (simulado)")
            
        except Exception as e:
            print(f"❌ Erro ao processar {pdf_file}: {e}")
    
    print(f"📊 Total de documentos carregados: {len(documents)}")
    return documents


def create_vector_store(documents=None):
    """
    Versão simplificada do criador de vetores
    """
    print("🔧 create_vector_store: Função simplificada")
    
    if not documents:
        print("⚠️ Nenhum documento fornecido para criar vector store")
        return None
    
    print(f"📚 Documentos recebidos para vetorização: {len(documents)}")
    
    # Simular criação do banco vetorial
    print("🔄 Simulando criação do banco vetorial...")
    print("💡 Na versão final, os documentos serão convertidos em embeddings")
    
    # Retornar um objeto simulado
    class MockVectorStore:
        def __init__(self, doc_count):
            self.doc_count = doc_count
        
        def similarity_search(self, query, k=3):
            print(f"🔍 Simulando busca por: '{query}'")
            return []
    
    vector_store = MockVectorStore(len(documents))
    print(f"✅ Vector store simulado criado com {len(documents)} documentos")
    
    return vector_store


def load_vector_store():
    """
    Versão simplificada - carregar vector store existente
    """
    print("🔧 load_vector_store: Função simplificada")
    print("💡 Na versão final, carregará o banco vetorial salvo")
    return None


def get_document_count():
    """
    Retorna o número de documentos disponíveis
    """
    docs_path = "documents"  # MUDADO: de "docs" para "documents"
    if os.path.exists(docs_path):
        pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
        return len(pdf_files)
    return 0


# Teste do módulo
if __name__ == "__main__":
    print("🧪 Testando data_loader para PDFs do notebook...")
    print("=" * 50)
    
    # Testar contagem de documentos
    doc_count = get_document_count()
    print(f"📁 PDFs na pasta 'documents': {doc_count}")  # MUDADO
    
    # Testar carregamento
    documents = load_documents()
    print(f"📚 Documentos carregados: {len(documents)}")
    
    # Testar criação de vector store
    if documents:
        vector_store = create_vector_store(documents)
        if vector_store:
            print("✅ Vector store criado com sucesso!")
    
    print("🎯 Teste concluído!")
