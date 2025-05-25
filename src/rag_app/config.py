# src/rag_app/config.py

# --- Configurações Globais e Flags de Depuração ---

# Flag para controlar a impressão de chunks recuperados para depuração
PRINT_DEBUG_CHUNKS: bool = False

# Flag para controlar a exibição de data e hora nas mensagens do chat
SHOW_CHAT_TIMESTAMPS: bool = True

# Modelos padrão a serem utilizados
DEFAULT_OLLAMA_MODEL: str = "llama3:latest"
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Pasta padrão para os dados (arquivos PDF)
# Este caminho será interpretado relativo ao diretório de onde o script principal é executado
# (geralmente a raiz do projeto).
DEFAULT_DATA_FOLDER: str = "data"

# Caminho para o banco de dados ChromaDB persistente
# Este caminho também será relativo ao diretório de execução.
CHROMA_DB_PATH: str = "./chroma_db_store"
CHROMA_COLLECTION_NAME: str = "rag_documents"

# Arquivo para rastrear o estado dos arquivos PDF processados
PROCESSED_FILES_STATUS_JSON: str = "processed_files_status.json"

# Parâmetros padrão para chunking
DEFAULT_CHUNK_SIZE: int = 768
DEFAULT_CHUNK_OVERLAP: int = 100

# Parâmetro k padrão para recuperação de chunks
DEFAULT_RETRIEVAL_K: int = 5