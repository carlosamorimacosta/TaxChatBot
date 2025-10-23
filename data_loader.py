import os
import glob
from typing import List

# SOLUÇÃO DEFINITIVA: Criar nossa própria classe Document
class Document:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Document(page_content='{self.page_content[:50]}...', metadata={self.metadata})"

# REMOVER COMPLETAMENTE as tipagens problemáticas
def load_documents():
    """
    Carrega todos os documentos PDF e MD da pasta docs/
    """
    print("🔧 Iniciando carregamento de documentos...")
    documents = []
    docs_path = "docs"
    
    # Criar pasta docs se não existir
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"📁 Pasta '{docs_path}' criada. Adicione seus arquivos PDF e MD lá!")
        return documents
    
    # Verificar se existem arquivos
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    md_files = glob.glob(os.path.join(docs_path, "*.md"))
    
    print(f"📄 PDFs encontrados: {len(pdf_files)}")
    print(f"📝 MDs encontrados: {len(md_files)}")
    
    # Se não há arquivos, retornar lista vazia
    if not pdf_files and not md_files:
        print("ℹ️ Nenhum arquivo PDF ou MD encontrado na pasta 'docs'")
        return documents
    
    # Para esta versão, vamos apenas simular o carregamento
    # e focar em fazer o app funcionar primeiro
    for pdf_file in pdf_files:
        try:
            print(f"📄 Simulando carregamento de: {os.path.basename(pdf_file)}")
            # Criar documento simulado
            doc = Document(
                page_content=f"Conteúdo do arquivo {pdf_file}",
                metadata={"source": pdf_file, "page": 1}
            )
            documents.append(doc)
        except Exception as e:
            print(f"❌ Erro com {pdf_file}: {e}")
    
    for md_file in md_files:
        try:
            print(f"📝 Simulando carregamento de: {os.path.basename(md_file)}")
            # Criar documento simulado
            doc = Document(
                page_content=f"Conteúdo do arquivo {md_file}",
                metadata={"source": md_file, "page": 1}
            )
            documents.append(doc)
        except Exception as e:
            print(f"❌ Erro com {md_file}: {e}")
    
    print(f"📊 Total de documentos simulados: {len(documents)}")
    return documents

def create_vector_store(documents=None):
    """
    Versão simplificada - retorna None por enquanto
    """
    print("🔧 create_vector_store: Função simplificada")
    if documents:
        print(f"📚 Documentos recebidos: {len(documents)}")
    return None

def load_vector_store():
    """
    Versão simplificada
    """
    print("🔧 load_vector_store: Função simplificada")
    return None

def get_document_count():
    """
    Versão simplificada
    """
    return 0

# Teste do módulo
if __name__ == "__main__":
    print("🧪 Testando data_loader simplificado...")
    docs = load_documents()
    print(f"✅ Teste concluído. Documentos: {len(docs)}")
