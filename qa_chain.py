import streamlit as st
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import os


def create_qa_chain(vector_store, chosen_model, gemini_api_key):
    """Cria uma RetrievalQA chain usando Gemini (via LangChain) e o modelo já escolhido no app.py."""
    try:
        if not vector_store:
            st.error("❌ Base vetorial não encontrada.")
            return None

        # Prompt alinhado com o estilo do seu TaxBot
        prompt_template = """
        Você é um especialista em legislação tributária brasileira (IRPF, reforma 2023–2025).
        Responda APENAS com base no CONTEXTO fornecido.

        Se a informação não estiver nos documentos, responda:
        "A resposta não está nos documentos carregados."

        -------------------------
        CONTEXTO:
        {context}
        -------------------------

        PERGUNTA:
        {question}

        Resposta:
        """

        PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=prompt_template
        )

        # Gemini via LangChain — usa o modelo detectado no setup_gemini()
        llm = ChatGoogleGenerativeAI(
            model=chosen_model,             # modelo que você descobriu dinamicamente no setup_gemini()
            google_api_key=gemini_api_key,  # usa a mesma GEMINI_API_KEY do app.py
            temperature=0.2,
            max_output_tokens=2048,
            convert_system_message_to_human=True
        )

        # Criação da chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

        return qa_chain

    except Exception as e:
        st.error(f"Erro ao criar Q&A chain com Gemini: {e}")
        return None
