import streamlit as st
import os
from data_loader import load_documents, create_vector_store, load_vector_store, get_document_count
from tax_calculator import monthly_reduction
from tax_calculator import annual_reduction
from tax_calculator import dividend_withholding
from tax_calculator import irpfm_due

# -----------------------------
# 🎨 Configuração da página
# -----------------------------
st.set_page_config(
    page_title="TaxBot - Assistente Fiscal",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 🏷️ Título e introdução
# -----------------------------
st.title("🤖 TaxBot - Assistente Fiscal Inteligente")
st.markdown("Analisando documentos fiscais baixados no notebook 📚")

# -----------------------------
# 💾 Inicialização do estado
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents_processed" not in st.session_state:
    st.session_state.documents_processed = False

# -----------------------------
# 🧭 Sidebar - Controle e status
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Upload de arquivos PDF
    uploaded_files = st.file_uploader(
        "📎 Fazer upload de PDFs fiscais",
        type=['pdf'],
        accept_multiple_files=True,
        help="Faça upload dos PDFs baixados no notebook"
    )
    
    if uploaded_files:
        os.makedirs("docs", exist_ok=True)
        for uploaded_file in uploaded_files:
            file_path = os.path.join("docs", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"✅ {len(uploaded_files)} PDF(s) salvo(s) na pasta 'docs'!")
    
    # Botão para processar documentos
    if st.button("🔄 Processar Documentos PDF"):
        with st.spinner("Carregando e processando PDFs..."):
            try:
                documents = load_documents()
                if documents:
                    st.session_state.documents_processed = True
                    st.success(f"✅ {len(documents)} documentos PDF processados!")
                    
                    # Exibir lista de documentos carregados
                    with st.expander("📋 Ver documentos carregados"):
                        for doc in documents:
                            st.write(f"**Arquivo:** {doc.metadata.get('filename', 'N/A')}")
                            st.write(f"**Página:** {doc.metadata.get('page', 'N/A')}")
                            st.markdown("---")
                else:
                    st.warning("⚠️ Nenhum PDF encontrado para processar.")
            except Exception as e:
                st.error(f"❌ Erro ao processar documentos: {e}")
    
    # Informações do sistema
    st.markdown("---")
    st.header("📊 Status do Sistema")
    
    doc_count = get_document_count()
    st.write(f"📁 PDFs na pasta 'docs': {doc_count}")
    st.write(f"🔧 Processado: {'✅' if st.session_state.documents_processed else '❌'}")
    
    # Botão para limpar chat
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# 💬 Área principal do chat
# -----------------------------
st.header("💬 Chat com Documentos Fiscais")

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
if prompt := st.chat_input("Pergunte sobre os documentos fiscais..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Geração de resposta
    with st.chat_message("assistant"):
        if st.session_state.documents_processed:
            resposta = (
                f"**Analisando sua pergunta sobre:** '{prompt}'\n\n"
                "📚 **Documentos disponíveis para consulta:**\n"
                "- Lei 7.713/88 e alterações\n"
                "- Projetos de lei sobre IR\n"
                "- Estudos sobre impactos tributários\n"
                "- Análises de progressividade fiscal\n\n"
                "💡 *Sistema em desenvolvimento — Em breve respostas precisas baseadas nos PDFs.*"
            )
        else:
            resposta = (
                "❌ **Por favor, processe os documentos PDF primeiro!**\n\n"
                "1. Faça upload dos PDFs baixados no notebook\n"
                "2. Clique em **'Processar Documentos PDF'**\n"
                "3. Depois faça suas perguntas sobre o conteúdo"
            )
        
        st.markdown(resposta)
        st.session_state.messages.append({"role": "assistant", "content": resposta})

#------------------------------
# Calculadora de IRPF
#------------------------------
st.header("🧾 Calculadora rápida - Reforma IRPF 2025")

with st.expander("📥 Entradas para cálculo (mensal/anual/dividendos)"):
    rend_mensal = st.number_input("Rendimento tributável mensal (R$)", min_value=0.0, value=8000.0, step=100.0)
    rend_anual = st.number_input("Rendimentos tributáveis anuais (R$)", min_value=0.0, value=96000.0, step=1000.0)
    irpf_apurado_anual = st.number_input("IRPF já apurado na declaração anual (R$)", min_value=0.0, value=5000.0, step=100.0)

    # Simplicidade: dividendos por mês input como lista simples (csv)
    div_csv = st.text_input("Dividendos por mês (R$) - CSV 12 valores, ex: 0,0,60000,...", value="0,"*11 + "0")
    if st.button("🔢 Calcular carga e descontos"):
        try:
            months = [float(x.strip()) for x in div_csv.split(",")]
            months_dict = {i+1: months[i] if i < len(months) else 0.0 for i in range(12)}
        except Exception:
            st.error("Formato CSV inválido. Coloque 12 valores separados por vírgula.")
            months_dict = {i+1: 0.0 for i in range(12)}

        # cálculos
        redu_mensal = monthly_reduction(rend_mensal)
        redu_anual = annual_reduction(rend_anual)
        retained_total, ret_detail = dividend_withholding(months_dict)

        irpfm_result = irpfm_due(
            annual_total_rend=rend_anual + sum(months_dict.values()),  # aproximação: inclui dividendos
            annual_irpf_apurado=irpf_apurado_anual,
            retained_on_dividends_annual=retained_total,
            redutor_info={
                "montante_dividendos": sum(months_dict.values()),
                # os seguintes campos seriam calculados se você integrar demonstrações da PJ
                "aliquota_efetiva_pj": 0.165,  
                "aliquota_efetiva_irpfm": 0.0,
                "aliquota_nominal_sum": 0.34
            }
        )

        st.subheader("📉 Resultados")
        st.write(f"- Redução mensal aplicada (R$): **{redu_mensal:,.2f}**. (limite = imposto pela tabela progressiva)")
        st.write(f"- Redução anual aplicada (R$): **{redu_anual:,.2f}**.")
        st.write(f"- Retenção na fonte sobre dividendos (total anual, R$): **{retained_total:,.2f}**.")
        st.write("Detalhe retenções por mês:", ret_detail)
        st.write("IRPFM (simulação):")
        st.json(irpfm_result)

# -----------------------------
# 📎 Rodapé
# -----------------------------
st.markdown("---")
st.markdown("💡 **Instruções:** Faça upload dos PDFs baixados no notebook e clique em 'Processar Documentos PDF' para começar!")
