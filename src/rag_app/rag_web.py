# src/rag_app/rag_web.py

import sys
import os

# --- Início da Modificação para Resolver ImportError/ModuleNotFoundError com Streamlit ---
# Adiciona o diretório 'src' (pai de 'rag_app') ao sys.path.
# Isso permite que 'rag_app' seja encontrado como um pacote de nível superior
# quando este script (rag_web.py) é executado diretamente pelo Streamlit.

_current_file_path = os.path.abspath(__file__) # Caminho para src/rag_app/rag_web.py
_rag_app_dir = os.path.dirname(_current_file_path) # Caminho para src/rag_app/
_src_dir = os.path.dirname(_rag_app_dir) # Caminho para src/

# Adiciona 'src' ao início do sys.path se ainda não estiver lá
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
# --- Fim da Modificação ---

# Agora, com 'src' no sys.path, podemos usar importações absolutas a partir de 'rag_app'
from rag_app.rag_core import RAGCore
from rag_app import config

import streamlit as st # Streamlit é uma dependência externa, importação normal
import logging         # Biblioteca padrão
from datetime import datetime # Biblioteca padrão
# 'os' já foi importado acima

# Configuração de logging
logger = logging.getLogger(__name__)
if not logger.handlers: # Evita adicionar handlers múltiplos se o módulo for importado/recarregado
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Título da página do navegador e layout
st.set_page_config(page_title="Pesquisa Inteligente com RAG & AI", layout="wide")

@st.cache_resource(show_spinner="Inicializando o Sistema RAG e processando documentos... Aguarde!")
def load_rag_core_cached():
    """
    Carrega e inicializa a instância do RAGCore.
    Esta função será cacheada pelo Streamlit.
    Os caminhos em config.py são relativos ao CWD (geralmente a raiz do projeto).
    """
    data_folder_path = config.DEFAULT_DATA_FOLDER 
    if not os.path.exists(data_folder_path) or not os.listdir(data_folder_path):
        st.error(f"A pasta de dados '{data_folder_path}' (definida em config.py como DEFAULT_DATA_FOLDER e "
                 f"esperada na raiz do projeto se você executou o comando Streamlit da raiz) "
                 "está vazia ou não existe. Por favor, crie-a e adicione seus arquivos PDF.")
        return None 

    try:
        # RAGCore usará os defaults de config.py para os modelos se não especificados aqui
        core = RAGCore(data_folder=data_folder_path) 
        
        processed_files_exist = hasattr(core, 'processed_pdf_files') and core.processed_pdf_files
        chunks_in_db = hasattr(core, 'collection') and core.collection and core.collection.count() > 0

        if not chunks_in_db and not processed_files_exist:
            st.warning("Nenhum documento PDF foi encontrado na pasta de dados ou processado com sucesso para o ChromaDB.")
        elif processed_files_exist and not chunks_in_db:
             st.warning(f"Documentos PDF foram identificados ({len(core.processed_pdf_files)}), mas nenhum chunk de texto foi efetivamente indexado no ChromaDB. "
                        "Verifique o conteúdo dos seus PDFs (precisam de texto extraível) e os logs detalhados do RAGCore no terminal para erros de processamento ou chunking.")
        elif not processed_files_exist and chunks_in_db:
            st.warning("Foram encontrados chunks no banco de dados, mas a lista de arquivos PDF processados está vazia. "
                       "Isso pode indicar uma inconsistência. Considere forçar um reprocessamento (deletando "
                       f"'{config.PROCESSED_FILES_STATUS_JSON}' e a pasta '{config.CHROMA_DB_PATH}').")
        
        return core
    except Exception as e:
        st.error(f"Erro crítico ao inicializar o RAGCore: {e}")
        logger.error(f"Erro crítico ao inicializar o RAGCore: {e}", exc_info=True)
        return None

# Carrega o sistema RAG
rag_system = load_rag_core_cached()

# --- Interface do Usuário com Streamlit ---

st.title("📚 Pesquisa Inteligente em Documentos com RAG e AI")

if not rag_system:
    st.error("O Sistema RAG não pôde ser inicializado. Verifique as mensagens acima e os logs no terminal.")
    st.markdown(f"Por favor, certifique-se de que a pasta `{config.DEFAULT_DATA_FOLDER}` (relativa à raiz do projeto) contém arquivos PDF válidos, que o servidor Ollama está acessível, e que não houve erros durante o processamento dos documentos.")
else:
    # Determina a descrição do provedor LLM
    llm_description = ""
    if config.LLM_PROVIDER == "gemini":
        llm_description = f"Google Gemini (modelo {config.GEMINI_MODEL}) via API"
    elif config.LLM_PROVIDER == "ollama":
        llm_description = f"Ollama local (modelo {config.DEFAULT_OLLAMA_MODEL})"
    else:
        llm_description = f"provedor {config.LLM_PROVIDER}"
    
    st.markdown(f"""
    Bem-vindo ao sistema de pesquisa inteligente! Este sistema utiliza a técnica RAG (Retrieval Augmented Generation)
    para buscar informações relevantes em seus documentos PDF e gerar respostas utilizando **{llm_description}**.

    **Como usar:**
    1. Certifique-se de que seus arquivos PDF estão na pasta `data` e foram processados (verifique a barra lateral).
    2. Digite sua pergunta no campo de chat abaixo.
    3. Pressione Enter para obter a resposta.
    
    **Provedor LLM atual:** `{config.LLM_PROVIDER.upper()}` (configurado em `config.py`)
    """)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

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
            "role": "user", "content": user_query, "timestamp": current_time_str 
        })
        with st.chat_message("user"): # Exibe imediatamente a pergunta do usuário
            display_content_user = ""
            if config.SHOW_CHAT_TIMESTAMPS:
                display_content_user += f"*{current_time_str}*\n\n"
            display_content_user += user_query
            st.markdown(display_content_user)

        with st.spinner("Buscando informações e gerando resposta... Por favor, aguarde."):
            try:
                answer = rag_system.answer_query(user_query)
                assistant_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant", "content": answer, "timestamp": assistant_time_str
                })
                st.rerun() # Força o recarregamento para exibir a nova mensagem do assistente
            except Exception as e:
                error_message = f"Ocorreu um erro ao processar sua pergunta: {e}"
                st.error(error_message)
                logger.error(f"Erro ao processar consulta '{user_query}': {e}", exc_info=True)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"Desculpe, ocorreu um erro ao processar sua solicitação.", # Mensagem mais genérica para o usuário
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.rerun()

# --- Barra Lateral (Sidebar) ---
st.sidebar.header("ℹ️ Sobre o Sistema")
st.sidebar.info(
    "Este é um sistema de exemplo demonstrando RAG (Retrieval Augmented Generation) "
    "com processamento local de PDFs e suporte a múltiplos provedores LLM "
    "(Ollama local e Google Gemini), com persistência de dados via ChromaDB."
)

if rag_system: 
    # Exibe informações do provedor LLM configurado
    st.sidebar.markdown(f"**Provedor LLM:** `{config.LLM_PROVIDER.upper()}`")
    
    if config.LLM_PROVIDER == "gemini":
        st.sidebar.markdown(f"**Modelo Gemini:** `{config.GEMINI_MODEL}`")
        st.sidebar.markdown(f"**Temperatura:** `{config.GEMINI_TEMPERATURE}`")
        st.sidebar.markdown(f"**Max Tokens:** `{config.GEMINI_MAX_TOKENS}`")
    elif config.LLM_PROVIDER == "ollama":
        if hasattr(rag_system, 'configured_ollama_model') and rag_system.configured_ollama_model:
            st.sidebar.markdown(f"**Modelo Ollama:** `{rag_system.configured_ollama_model}`")
        else: 
            st.sidebar.markdown(f"**Modelo Ollama:** `{config.DEFAULT_OLLAMA_MODEL}`")
        st.sidebar.markdown(f"**Host Ollama:** `{config.OLLAMA_HOST}`")
    else:
        st.sidebar.markdown(f"**Provedor:** `{config.LLM_PROVIDER}` (configuração personalizada)")

    embedding_model_name_display = config.DEFAULT_EMBEDDING_MODEL 
    if hasattr(rag_system, 'configured_embedding_model_name') and rag_system.configured_embedding_model_name:
        embedding_model_name_display = rag_system.configured_embedding_model_name
    st.sidebar.markdown(f"**Modelo de Embedding:** `{embedding_model_name_display}`")

    st.sidebar.markdown("---") 
    st.sidebar.markdown("**📄 Arquivos PDF Processados:**")
    if hasattr(rag_system, 'processed_pdf_files'):
        if rag_system.processed_pdf_files:
            for pdf_name in rag_system.processed_pdf_files:
                st.sidebar.markdown(f"  - `{pdf_name}`")
        else:
            st.sidebar.markdown("  `Nenhum PDF processado ou encontrado.`")
    else: 
        st.sidebar.markdown("  `(Informação de arquivos não disponível)`")

    st.sidebar.markdown("**🧩 Chunks Indexados (ChromaDB):**")
    if hasattr(rag_system, 'collection') and rag_system.collection:
        try:
            db_count = rag_system.collection.count()
            st.sidebar.markdown(f"  `{db_count}`")
        except Exception as e_chroma_count: # Captura erro se a coleção não estiver acessível
            logger.error(f"Erro ao obter contagem da coleção ChromaDB: {e_chroma_count}")
            st.sidebar.markdown("  `Erro ao contar`")
    else: 
        st.sidebar.markdown("  `0 (Coleção não disponível)`")
else: 
    st.sidebar.markdown("---")
    st.sidebar.warning("Sistema RAG não inicializado.")
    st.sidebar.markdown(f"**Provedor LLM (Config):** `{config.LLM_PROVIDER.upper()}`")
    
    if config.LLM_PROVIDER == "gemini":
        st.sidebar.markdown(f"**Modelo Gemini (Config):** `{config.GEMINI_MODEL}`")
    elif config.LLM_PROVIDER == "ollama":
        st.sidebar.markdown(f"**Modelo Ollama (Config):** `{config.DEFAULT_OLLAMA_MODEL}`")
    else:
        st.sidebar.markdown(f"**Provedor:** `{config.LLM_PROVIDER}` (configuração personalizada)")
    
    st.sidebar.markdown(f"**Modelo de Embedding (Config):** `{config.DEFAULT_EMBEDDING_MODEL}`")
    st.sidebar.markdown("**Arquivos PDF Processados:** `(Sistema não inicializado)`")
    st.sidebar.markdown("**Chunks Indexados (ChromaDB):** `(Sistema não inicializado)`")

if st.sidebar.button("🗑️ Limpar Histórico do Chat"):
    st.session_state.messages = []
    st.rerun()