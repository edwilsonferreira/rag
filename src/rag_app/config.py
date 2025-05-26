# src/rag_app/config.py

from typing import List # Adicionar esta importação

# --- Configurações Globais e Flags de Depuração ---
PRINT_DEBUG_CHUNKS: bool = True
SHOW_CHAT_TIMESTAMPS: bool = True
ALWAYS_INCLUDE_PAGE_IN_ANSWER: bool = True 

# --- NOVA LISTA DE COMANDOS DE SAÍDA ---
# Palavras-chave para finalizar a execução dos loops interativos.
# Serão comparadas em minúsculas.
EXIT_COMMANDS: List[str] = [
    "sair", "saia", "exit", "quit", "q",
    "parar", "pare", "stop",
    "finalizar", "finalize", "fim", "end",
    "fechar", "close",
    "terminar", "terminate", "bye"
]

# Modelos padrão a serem utilizados
DEFAULT_OLLAMA_MODEL: str = "llama3:latest"
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Pasta padrão para os dados (arquivos PDF)
DEFAULT_DATA_FOLDER: str = "data"

# Caminho para o banco de dados ChromaDB persistente
CHROMA_DB_PATH: str = "./chroma_db_store"
CHROMA_COLLECTION_NAME: str = "rag_documents"

# Arquivo para rastrear o estado dos arquivos PDF processados
PROCESSED_FILES_STATUS_JSON: str = "processed_files_status.json"

# Parâmetros padrão para chunking
DEFAULT_CHUNK_SIZE: int = 768
DEFAULT_CHUNK_OVERLAP: int = 100

# Parâmetro k padrão para recuperação de chunks
DEFAULT_RETRIEVAL_K: int = 5