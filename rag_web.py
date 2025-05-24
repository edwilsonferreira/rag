# rag_web.py

import streamlit as st
from rag_core import RAGCore
import logging
import os
import config # Importa as configurações globais
from datetime import datetime # Para timestamps

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Título da página do navegador e layout
st.set_page_config(page_title="Pesquisa Inteligente com RAG & Ollama", layout="wide")

@st.cache_resource(show_spinner="Inicializando o Sistema RAG e processando documentos... Aguarde!")
def load_rag_core_cached():
    """
    Carrega e inicializa a instância do RAGCore.
    Esta função será cacheada pelo Streamlit.
    """
    data_folder_path = config.DEFAULT_DATA_FOLDER
    if not os.path.exists(data_folder_path) or not os.listdir(data_folder_path):
        st.error(f"A pasta '{data_folder_path}' (definida em config.py como DEFAULT_DATA_FOLDER) "
                 "está vazia ou não existe. Por favor, crie-a e adicione seus arquivos PDF.")
        return None 

    try:
        # RAGCore usará os defaults de config.py para os modelos se não especificados aqui
        core = RAGCore(data_folder=data_folder_path) 
        
        # Verifica o estado após a inicialização do RAGCore
        processed_files_exist = hasattr(core, 'processed_pdf_files') and core.processed_pdf_files
        # Verifica se a coleção foi criada e se tem itens
        chunks_in_db = hasattr(core, 'collection') and core.collection and core.collection.count() > 0

        if not chunks_in_db and not processed_files_exist:
            st.warning("Nenhum documento PDF foi encontrado na pasta de dados ou processado com sucesso para o ChromaDB.")
        elif processed_files_exist and not chunks_in_db:
             # Esta é a condição que gerou o aviso para você anteriormente.
             # Significa que RAGCore identificou PDFs, mas nada foi parar no ChromaDB.
             st.warning(f"Documentos PDF foram identificados ({len(core.processed_pdf_files)}), mas nenhum chunk de texto foi efetivamente indexado no ChromaDB. "
                        "Verifique o conteúdo dos seus PDFs (precisam de texto extraível) e os logs detalhados do RAGCore no terminal para erros de processamento ou chunking.")
        elif not processed_files_exist and chunks_in_db:
            # Caso estranho: chunks no DB mas nenhum arquivo PDF listado como processado. Pode indicar inconsistência no estado.
            st.warning("Foram encontrados chunks no banco de dados, mas a lista de arquivos PDF processados está vazia. "
                       "Considere forçar um reprocessamento (deletando 'processed_files_status.json' e a pasta 'chroma_db_store').")
        
        return core
    except Exception as e:
        st.error(f"Erro crítico ao inicializar o RAGCore: {e}")
        logger.error(f"Erro crítico ao inicializar o RAGCore: {e}", exc_info=True)
        return None

# Carrega o sistema RAG
rag_system = load_rag_core_cached()

# --- Interface do Usuário com Streamlit ---

st.title("📚 Pesquisa Inteligente em Documentos com RAG e Ollama")

if not rag_system:
    st.error("O Sistema RAG não pôde ser inicializado. Verifique as mensagens acima e os logs no terminal.")
    st.markdown(f"Por favor, certifique-se de que a pasta `{config.DEFAULT_DATA_FOLDER}` contém arquivos PDF válidos, que o servidor Ollama está acessível, e que não houve erros durante o processamento dos documentos.")
else:
    st.markdown("""
    Bem-vindo ao sistema de pesquisa inteligente! Este sistema utiliza a técnica RAG (Retrieval Augmented Generation)
    para buscar informações relevantes em seus documentos PDF e gerar respostas utilizando um Large Language Model (LLM)
    hospedado localmente via Ollama.

    **Como usar:**
    1. Certifique-se de que seus arquivos PDF estão na pasta `data` e foram processados (verifique a barra lateral).
    2. Digite sua pergunta no campo de chat abaixo.
    3. Pressione Enter para obter a resposta.
    """)

    # Inicializa o estado da sessão para o histórico do chat, se não existir
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Exibe o histórico do chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            display_content = ""
            if config.SHOW_CHAT_TIMESTAMPS and "timestamp" in message:
                display_content += f"*{message['timestamp']}*\n\n" # Timestamp em itálico, seguido de nova linha
            display_content += message["content"]
            st.markdown(display_content)

    # Campo de entrada para a pergunta do usuário
    user_query = st.chat_input("Digite sua pergunta aqui...")

    if user_query:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": user_query,
            "timestamp": current_time_str 
        })
        # Exibe a mensagem do usuário imediatamente
        with st.chat_message("user"):
            display_content_user = ""
            if config.SHOW_CHAT_TIMESTAMPS:
                display_content_user += f"*{current_time_str}*\n\n"
            display_content_user += user_query
            st.markdown(display_content_user)

        # Processa a resposta
        with st.spinner("Buscando informações e gerando resposta... Por favor, aguarde."):
            try:
                answer = rag_system.answer_query(user_query)
                assistant_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "timestamp": assistant_time_str
                })
                st.rerun() # Força o recarregamento para exibir a nova mensagem do assistente a partir do loop de histórico
            except Exception as e:
                error_message = f"Ocorreu um erro ao processar sua pergunta: {e}"
                st.error(error_message)
                logger.error(f"Erro ao processar consulta '{user_query}': {e}", exc_info=True)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.rerun()

# --- Barra Lateral (Sidebar) ---
st.sidebar.header("ℹ️ Sobre o Sistema") # Adicionado ícone
st.sidebar.info(
    "Este é um sistema de exemplo demonstrando RAG (Retrieval Augmented Generation) "
    "com processamento local de PDFs e um LLM via Ollama."
)

if rag_system: # Exibe informações do sistema apenas se o RAGCore foi carregado
    if hasattr(rag_system, 'configured_ollama_model') and rag_system.configured_ollama_model:
        st.sidebar.markdown(f"**Modelo LLM (Ollama):** `{rag_system.configured_ollama_model}`")
    else: 
        st.sidebar.markdown(f"**Modelo LLM (Padrão Config):** `{config.DEFAULT_OLLAMA_MODEL}`")

    embedding_model_name_display = config.DEFAULT_EMBEDDING_MODEL 
    if hasattr(rag_system, 'configured_embedding_model_name') and rag_system.configured_embedding_model_name:
        embedding_model_name_display = rag_system.configured_embedding_model_name
    st.sidebar.markdown(f"**Modelo de Embedding:** `{embedding_model_name_display}`")

    st.sidebar.markdown("---") # Separador
    st.sidebar.markdown("**📄 Arquivos PDF Processados:**")
    if hasattr(rag_system, 'processed_pdf_files'):
        if rag_system.processed_pdf_files:
            for pdf_name in rag_system.processed_pdf_files:
                st.sidebar.markdown(f"  - `{pdf_name}`")
        else:
            st.sidebar.markdown("  `Nenhum PDF processado ou encontrado.`")
    else: # Caso o atributo não exista em RAGCore (pouco provável com a classe atual)
        st.sidebar.markdown("  `(Informação de arquivos não disponível)`")

    st.sidebar.markdown("**🧩 Chunks Indexados (ChromaDB):**")
    if hasattr(rag_system, 'collection') and rag_system.collection:
        db_count = rag_system.collection.count()
        st.sidebar.markdown(f"  `{db_count}`")
    else: # Caso não haja coleção ou RAGCore não carregou
        st.sidebar.markdown("  `0`")

else: # Se rag_system não foi carregado (erro na inicialização)
    st.sidebar.markdown("---")
    st.sidebar.warning("Sistema RAG não inicializado.")
    st.sidebar.markdown(f"**Modelo LLM (Padrão Config):** `{config.DEFAULT_OLLAMA_MODEL}`")
    st.sidebar.markdown(f"**Modelo de Embedding (Padrão Config):** `{config.DEFAULT_EMBEDDING_MODEL}`")
    st.sidebar.markdown("**Arquivos PDF Processados:** `(Sistema não inicializado)`")
    st.sidebar.markdown("**Chunks Indexados (ChromaDB):** `(Sistema não inicializado)`")

# Botão para limpar o histórico do chat
if st.sidebar.button("🗑️ Limpar Histórico do Chat"):
    st.session_state.messages = []
    st.rerun()