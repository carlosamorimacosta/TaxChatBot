import os
from data_loader import load_vector_store

class TaxQAChain:
    def __init__(self):
        self.vector_store = None
        self.qa_chain = None
        self.is_initialized = False
        
    def initialize(self):
        """
        Inicializa a cadeia de QA com o banco vetorial
        """
        try:
            # Carregar banco vetorial
            self.vector_store = load_vector_store()
            
            if self.vector_store is None:
                print("❌ Vector store não disponível")
                return False
            
            print("✅ QA Chain inicializada com sucesso!")
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar QA Chain: {e}")
            return False
    
    def ask_question(self, question: str) -> dict:
        """
        Faz uma pergunta ao sistema
        """
        if not self.is_initialized:
            if not self.initialize():
                return {
                    "answer": "Sistema não inicializado. Por favor, carregue e processe documentos primeiro.",
                    "sources": []
                }
        
        try:
            print(f"🤔 Pergunta: {question}")
            
            # Buscar documentos similares
            relevant_docs = self.vector_store.similarity_search(question, k=3)
            
            # Construir resposta baseada nos documentos
            if relevant_docs:
                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                # Resposta simulada - em produção integraria com OpenAI
                answer = f"📊 **Baseado na documentação carregada:**\n\n"
                answer += f"Encontrei {len(relevant_docs)} documento(s) relevantes sobre '{question}'.\n\n"
                answer += "**Próximos passos:** Integre com API OpenAI para respostas completas.\n\n"
                answer += "**Documentos encontrados:**\n"
                for i, doc in enumerate(relevant_docs, 1):
                    source = doc.metadata.get('source', 'Desconhecido')
                    page = doc.metadata.get('page', 'N/A')
                    answer += f"{i}. {os.path.basename(source)} (Página {page})\n"
            else:
                answer = "❌ Não encontrei informações relevantes nos documentos carregados para responder sua pergunta."
            
            # Formatar fontes
            sources = [
                {
                    "source": doc.metadata.get("source", "Desconhecido"),
                    "page": doc.metadata.get("page", "N/A"),
                    "content": doc.page_content[:200] + "..."
                }
                for doc in relevant_docs
            ]
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar pergunta: {e}")
            return {
                "answer": f"Erro ao processar sua pergunta: {str(e)}",
                "sources": []
            }

# Instância global
tax_qa = TaxQAChain()

def create_qa_chain():
    """
    Função para criar e retornar a cadeia de QA
    """
    return tax_qa

def get_qa_chain():
    """
    Retorna a instância da cadeia de QA
    """
    return tax_qa

# Teste do módulo
if __name__ == "__main__":
    print("🧪 Testando QA Chain...")
    qa_chain = create_qa_chain()
    
    if qa_chain.initialize():
        test_question = "O que é imposto de renda?"
        result = qa_chain.ask_question(test_question)
        print(f"\n📝 Resposta: {result['answer']}")
        print(f"📚 Fontes: {len(result['sources'])} documentos")
    else:
        print("❌ QA Chain não pôde ser inicializada")