import streamlit as st
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import os

def create_qa_chain(vector_store, openai_api_key):
    """Cria chain de Q&A sem tiktoken"""
    try:
        if not vector_store:
            return None
            
        # Template de prompt em português
        prompt_template = """
        Você é um assistente especializado em reforma do IRPF (Imposto de Renda Pessoa Física) brasileiro.
        Use o contexto abaixo para responder à pergunta de forma clara e precisa.
        
        Contexto:
        {context}
        
        Pergunta: {question}
        
        Resposta:
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Criar chain de Q&A
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(
                openai_api_key=openai_api_key,
                temperature=0.1,
                model_name="gpt-3.5-turbo-instruct"
            ),
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        return qa_chain
        
    except Exception as e:
        st.error(f"Erro ao criar chain de Q&A: {e}")
        return None
        
