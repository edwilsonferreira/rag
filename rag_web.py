# rag_web.py

import streamlit as st
from rag_core import RAGCore
import logging
import os
import src.config as config # Importa as configurações globais
from datetime import datetime # Para timestamps

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(page_title="Pesquisa Inteligente com RAG & Ollama", layout="wide")

@st.cache_resource(show_spinner="Inicializando o Sistema RAG e processando documentos... Aguarde!")
def load_rag_core_cached():
    data_folder_path = config.DEFAULT_DATA_FOLDER
    if not os.path.exists(data_folder_path) or not os.listdir(data_folder_path):
        st.error(f"A pasta '{data_folder_path}' (definida em config.py) "
                 "está vazia ou não existe. Por favor, crie-a e adicione seus arquivos PDF.")
        return None
    try:
        core = RAGCore(data_folder=data_folder_path) # Usa defaults de config.py para modelos
        # ... (verificações de processamento de documentos como antes) ...
        if not core.text_chunks_corpus and (not hasattr(core, 'processed_pdf_files') or not core.processed_pdf_files):
            st.warning("Nenhum documento PDF foi encontrado ou processado com sucesso.")
        elif hasattr(core, 'processed_pdf_files') and core.processed_pdf_files and not core.text_chunks_corpus:
             st.warning(f"Documentos PDF encontrados, mas nenhum chunk de texto foi gerado.")
        return core
    except Exception as e:
        st.error(f"Erro crítico ao inicializar o RAGCore: {e}")
        logging.error(f"Erro crítico ao inicializar o RAGCore: {e}", exc_info=True)
        return None

rag_system = load_rag_core_cached()

st.title("📚 Pesquisa Inteligente em Documentos com RAG e Ollama")

if not rag_system:
    st.error("O Sistema RAG não pôde ser inicializado. Verifique as mensagens e os logs.")
    st.markdown(f"Verifique a pasta `{config.DEFAULT_DATA_FOLDER}` e o servidor Ollama.")
else:
    st.markdown("""
    Bem-vindo ao sistema de pesquisa inteligente!
    **Como usar:**
    1. Certifique-se de que seus PDFs estão na pasta `data` e foram processados.
    2. Digite sua pergunta abaixo.
    """)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Exibe o histórico do chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            display_content = ""
            if config.SHOW_CHAT_TIMESTAMPS and "timestamp" in message:
                display_content += f"*{message['timestamp']}*\n\n"
            display_content += message["content"]
            st.markdown(display_content)

    user_query = st.chat_input("Digite sua pergunta aqui...")

    if user_query:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": user_query,
            "timestamp": current_time_str # Adiciona timestamp
        })
        # Exibe a mensagem do usuário imediatamente
        with st.chat_message("user"):
            display_content = ""
            if config.SHOW_CHAT_TIMESTAMPS:
                display_content += f"*{current_time_str}*\n\n"
            display_content += user_query
            st.markdown(display_content)

        with st.spinner("Buscando informações e gerando resposta..."):
            try:
                answer = rag_system.answer_query(user_query)
                assistant_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "timestamp": assistant_time_str # Adiciona timestamp
                })
                # Exibe a resposta do assistente (o st.rerun abaixo vai atualizar, mas podemos mostrar imediatamente)
                # Com o st.rerun() ao final, esta exibição imediata pode não ser necessária ou causar um flash
                # with st.chat_message("assistant"):
                #     display_content_assistant = ""
                #     if config.SHOW_CHAT_TIMESTAMPS:
                #         display_content_assistant += f"*{assistant_time_str}*\n\n"
                #     display_content_assistant += answer
                #     st.markdown(display_content_assistant)
                st.rerun() # Força o recarregamento para exibir a nova mensagem do assistente a partir do loop de histórico

            except Exception as e:
                error_message = f"Ocorreu um erro: {e}"
                st.error(error_message)
                logging.error(f"Erro na consulta '{user_query}': {e}", exc_info=True)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Erro ao processar: {e}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.rerun()


# --- Barra Lateral (Sidebar) ---
st.sidebar.header("Sobre o Sistema")
st.sidebar.info("Sistema RAG com processamento local de PDFs e LLM via Ollama.")

if rag_system:
    if hasattr(rag_system, 'configured_ollama_model'):
        st.sidebar.markdown(f"**Modelo LLM (Ollama):** `{rag_system.configured_ollama_model}`")
    else:
        st.sidebar.markdown(f"**Modelo LLM (Padrão):** `{config.DEFAULT_OLLAMA_MODEL}`")

    embedding_model_name_display = config.DEFAULT_EMBEDDING_MODEL # Padrão
    if hasattr(rag_system, 'configured_embedding_model_name'):
        embedding_model_name_display = rag_system.configured_embedding_model_name
    st.sidebar.markdown(f"**Modelo de Embedding:** `{embedding_model_name_display}`")

    if hasattr(rag_system, 'processed_pdf_files'):
        st.sidebar.markdown("**Arquivos PDF Processados:**")
        if rag_system.processed_pdf_files:
            for pdf_name in rag_system.processed_pdf_files:
                st.sidebar.markdown(f"  - `{pdf_name}`")
        else:
            st.sidebar.markdown("  `Nenhum PDF processado.`")
    else:
        st.sidebar.markdown("**Arquivos PDF Processados:** `(N/A)`")

    if hasattr(rag_system, 'text_chunks_corpus'):
        st.sidebar.markdown(f"**Chunks Indexados:** `{len(rag_system.text_chunks_corpus)}`")
    else:
        st.sidebar.markdown("**Chunks Indexados:** `0`")
else:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Modelo LLM (Padrão):** `{config.DEFAULT_OLLAMA_MODEL}`")
    st.sidebar.markdown(f"**Modelo de Embedding (Padrão):** `{config.DEFAULT_EMBEDDING_MODEL}`")
    st.sidebar.markdown("**Arquivos PDF Processados:** `(Sistema não inicializado)`")
    st.sidebar.markdown("**Chunks Indexados:** `(Sistema não inicializado)`")

if st.sidebar.button("Limpar Histórico do Chat"):
    st.session_state.messages = []
    st.rerun()