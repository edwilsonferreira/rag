
# Guia do Administrador: Sistema RAG com Ollama, Streamlit e ChromaDB

**Nota Importante:** O código-fonte base para o sistema descrito neste guia foi gerado com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

**Data do Documento:** 24 de Maio de 2025

## 1. Introdução

Este documento fornece um guia completo para administradores de sistema sobre como configurar, instalar, executar e manter o sistema de Geração Aumentada por Recuperação (RAG). O sistema é projetado para processar documentos PDF, indexar seu conteúdo de forma **persistente usando ChromaDB**, e permitir que os usuários façam perguntas em linguagem natural. As respostas são geradas por um Modelo de Linguagem Grande (LLM) localmente hospedado via Ollama, com contexto recuperado dos documentos. A interface do usuário é fornecida através de uma aplicação web Streamlit. A persistência de dados garante inicializações mais rápidas após o primeiro processamento.

## 2. Requisitos do Sistema

### 2.1. Software
* **Python:** Versão 3.10 ou 3.11 (recomendado).
* **Ollama:** Servidor Ollama instalado e em execução ([ollama.com](https://ollama.com/)).
* **Pip:** Gerenciador de pacotes Python.
* **Sistema Operacional:** Linux, macOS ou Windows (WSL2 recomendado para Ollama no Windows).

### 2.2. Hardware (Recomendações Mínimas)
* **RAM:** 8GB (mínimo), 16GB+ (recomendado para modelos maiores).
* **CPU:** Processador moderno multi-core.
* **GPU (Opcional para Ollama):** Placa NVIDIA com drivers CUDA para melhor desempenho.
* **Espaço em Disco:** Suficiente para PDFs, modelos LLM/Embedding, e o banco de dados ChromaDB (pasta `chroma_db_store/`).

## 3. Estrutura do Projeto

A estrutura de diretórios esperada é:

seu_projeto_rag/
├── data/                     # Pasta para armazenar os arquivos PDF de entrada
│   └── exemplo.pdf
├── chroma_db_store/          # Pasta onde o ChromaDB armazena seus dados (criada automaticamente)
├── config.py                 # Arquivo de configuração global
├── rag_core.py               # Lógica principal do sistema RAG
├── rag_web.py                # Interface web com Streamlit
├── rag_batch_query.py        # Script para consultas em lote (se usado)
├── processed_files_status.json # Arquivo que rastreia o estado dos PDFs processados (criado automaticamente)
└── requirements.txt          # Lista de dependências Python


## 4. Preparação do Ambiente

### 4.1. Instalar Python
Instale Python 3.10 ou 3.11 de [python.org](https://www.python.org/downloads/), garantindo que seja adicionado ao PATH.

### 4.2. Criar e Ativar Ambiente Virtual
Na pasta raiz do projeto:
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
5. Configuração do Ollama
Conforme detalhado na versão anterior do guia (instalar, baixar modelos como ollama pull llama3:latest, garantir que está rodando).

6. Instalação do Software (Dependências Python)
6.1. Arquivo requirements.txt

O arquivo requirements.txt deve incluir:

Plaintext
pymupdf
sentence-transformers
ollama
numpy
streamlit
chromadb
Nota: faiss-cpu foi substituído por chromadb para persistência e busca vetorial.

6.2. Comando de Instalação

Com o ambiente virtual ativo:

Bash
pip install -r requirements.txt
7. Configuração do Sistema (config.py)
O arquivo config.py centraliza as configurações. As principais relacionadas à persistência são:

Python
# config.py (trecho relevante)

# ... (PRINT_DEBUG_CHUNKS, SHOW_CHAT_TIMESTAMPS, modelos, etc.)

# Pasta padrão para os dados (arquivos PDF)
DEFAULT_DATA_FOLDER: str = "data"

# Caminho para o banco de dados ChromaDB persistente
CHROMA_DB_PATH: str = "./chroma_db_store"
# Nome da coleção dentro do ChromaDB
CHROMA_COLLECTION_NAME: str = "rag_documents"

# Arquivo para rastrear o estado dos arquivos PDF processados
PROCESSED_FILES_STATUS_JSON: str = "processed_files_status.json"

# Parâmetros padrão para chunking
DEFAULT_CHUNK_SIZE: int = 768
DEFAULT_CHUNK_OVERLAP: int = 100

# Parâmetro k padrão para recuperação de chunks
DEFAULT_RETRIEVAL_K: int = 5
Ajuste esses caminhos e nomes conforme necessário. CHROMA_DB_PATH é onde os dados do ChromaDB serão armazenados fisicamente. PROCESSED_FILES_STATUS_JSON rastreia quais PDFs foram processados e seu estado (data de modificação, tamanho) para evitar reprocessamento desnecessário.

8. Preparando Dados de Entrada
Crie a pasta data (ou o nome configurado em DEFAULT_DATA_FOLDER).
Adicione seus arquivos PDF a esta pasta.
O sistema detectará automaticamente arquivos novos ou modificados nesta pasta na próxima inicialização.
9. Executando o Sistema
Garanta que o Ollama está rodando e o ambiente virtual está ativo.
Na pasta raiz do projeto, execute:
Bash
streamlit run rag_web.py
Comportamento de Inicialização:
Primeira Execução (ou após limpar chroma_db_store/ e processed_files_status.json): O sistema processará todos os PDFs da pasta data/. Chunks e embeddings serão gerados e salvos no diretório CHROMA_DB_PATH. O arquivo processed_files_status.json será criado/atualizado. Esta etapa pode ser demorada.
Execuções Subsequentes: O sistema se conectará ao ChromaDB existente e carregará o status dos arquivos. Apenas PDFs novos ou modificados (com base na data de modificação e tamanho) na pasta data/ serão processados e adicionados/atualizados no ChromaDB. Isso torna a inicialização muito mais rápida.
10. Solução de Problemas Comuns
Erros de Permissão com chroma_db_store/: Garanta que a aplicação tem permissão de escrita no local especificado por CHROMA_DB_PATH.
Banco de Dados Corrompido ou Estado Inconsistente: Se suspeitar de problemas com o ChromaDB ou processed_files_status.json:
Pare a aplicação.
Faça backup e delete o diretório chroma_db_store/.
Delete o arquivo processed_files_status.json.
Reinicie a aplicação. Isso forçará um reprocessamento completo de todos os PDFs.
"Nenhum chunk de texto foi indexado no ChromaDB" (mesmo com PDFs na pasta data):
Verifique os logs do terminal durante a inicialização do RAGCore para mensagens de erro sobre extração de texto ou chunking.
Certifique-se de que os PDFs contêm texto extraível.
Experimente ajustar DEFAULT_CHUNK_SIZE e DEFAULT_CHUNK_OVERLAP em config.py.
11. Manutenção
Backup: Inclua o diretório CHROMA_DB_PATH (ex: chroma_db_store/) e o arquivo PROCESSED_FILES_STATUS_JSON nos seus backups regulares do projeto.
Reprocessamento Completo: Para forçar o sistema a reprocessar todos os PDFs e reconstruir o banco de dados do zero, delete o diretório CHROMA_DB_PATH e o arquivo PROCESSED_FILES_STATUS_JSON antes de iniciar a aplicação.
Remoção de PDFs: Se você remover um PDF da pasta data/, na próxima inicialização, o sistema RAG deve identificar isso, remover suas entradas do processed_files_status.json e deletar seus chunks correspondentes do ChromaDB.
Atualizando Dependências e Modelos: Conforme descrito na versão anterior do guia.
