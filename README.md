# Sistema de Pesquisa RAG com Ollama, Streamlit e ChromaDB

Este projeto implementa um sistema de Geração Aumentada por Recuperação (RAG) que permite aos usuários fazer perguntas em linguagem natural sobre um conjunto de documentos PDF. O sistema agora utiliza **ChromaDB** para **armazenamento persistente** de chunks de texto e seus embeddings, resultando em inicializações significativamente mais rápidas após o primeiro processamento. As respostas são geradas por um Modelo de Linguagem Grande (LLM) hospedado localmente via Ollama, com o contexto relevante extraído dos documentos. A interface do usuário é construída com Streamlit.

**Nota Importante:** O código-fonte base para este sistema foi desenvolvido com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

## 🚀 Funcionalidades Principais

* **Processamento de PDFs:** Extrai texto de arquivos PDF localizados em uma pasta `data/`.
* **Persistência com ChromaDB:** Chunks de texto e seus embeddings são armazenados no ChromaDB, evitando reprocessamento em cada inicialização.
* **Processamento Inteligente:** Verifica arquivos PDF novos ou modificados e atualiza o banco de dados incrementalmente.
* **Geração de Embeddings:** Utiliza modelos `SentenceTransformers` para criar representações vetoriais dos trechos de texto.
* **Busca Vetorial Eficiente:** ChromaDB gerencia a indexação e busca de similaridade.
* **Integração com Ollama:** Conecta-se a um servidor Ollama local para utilizar LLMs para a geração de respostas.
* **Interface Web Interativa:** Interface amigável construída com Streamlit.
* **Configurável:** Parâmetros como modelos, caminhos, comportamento de chunking e depuração são ajustados via `config.py`.
* **Timestamps no Chat:** Opção para exibir data e hora nas mensagens.

## 🛠️ Tecnologias Utilizadas

* **Python:** Linguagem de programação principal.
* **Ollama:** Para servir LLMs localmente.
* **Streamlit:** Para a interface web.
* **ChromaDB:** Para armazenamento persistente e busca de embeddings e documentos.
* **SentenceTransformers:** Para geração de embeddings de texto.
* **PyMuPDF (Fitz):** Para extração de texto de PDFs.
* **NumPy:** Para operações numéricas.

## ⚙️ Configuração e Instalação

Siga estes passos para configurar e executar o projeto localmente.

### Pré-requisitos

1.  **Python:** Versão 3.10 ou 3.11 recomendada.
2.  **Git:** Para clonar o repositório.
3.  **Ollama:** Servidor Ollama instalado e em execução.
    * Instale a partir de [ollama.com](https://ollama.com/).
    * Baixe o modelo LLM desejado (ver `config.py`). Exemplo: `ollama pull llama3:latest`.

### Passos de Instalação

1.  **Clone o Repositório (se aplicável):**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO_AQUI>
    cd <NOME_DA_PASTA_DO_REPOSITORIO>
    ```

2.  **Crie e Ative um Ambiente Virtual:**
    ```bash
    python -m venv .venv
    # Linux/macOS: source .venv/bin/activate
    # Windows: .venv\Scripts\activate
    ```

3.  **Instale as Dependências:**
    O arquivo `requirements.txt` deve conter:
    ```txt
    pymupdf
    sentence-transformers
    ollama
    numpy
    streamlit
    chromadb
    ```
    Com o ambiente virtual ativo, instale:
    ```bash
    pip install -r requirements.txt
    ```

### Configuração do Projeto

1.  **Arquivo `config.py`:**
    Ajuste os parâmetros neste arquivo conforme necessário:
    * `PRINT_DEBUG_CHUNKS`, `SHOW_CHAT_TIMESTAMPS`
    * `DEFAULT_OLLAMA_MODEL`, `DEFAULT_EMBEDDING_MODEL`
    * `DEFAULT_DATA_FOLDER` (padrão: `"data"`)
    * `CHROMA_DB_PATH` (padrão: `"./chroma_db_store"`): Local onde o banco de dados vetorial será salvo.
    * `CHROMA_COLLECTION_NAME` (padrão: `"rag_documents"`)
    * `PROCESSED_FILES_STATUS_JSON` (padrão: `"processed_files_status.json"`): Arquivo que rastreia o estado dos PDFs.
    * `DEFAULT_CHUNK_SIZE`, `DEFAULT_CHUNK_OVERLAP`, `DEFAULT_RETRIEVAL_K`.

2.  **Dados de Entrada (PDFs):**
    * Crie uma pasta chamada `data` (ou o nome definido em `DEFAULT_DATA_FOLDER`) na raiz do projeto.
    * Coloque seus arquivos PDF dentro desta pasta.

## ▶️ Executando a Aplicação

1.  Certifique-se de que o servidor Ollama está em execução.
2.  Com seu ambiente virtual ativo e na pasta raiz do projeto, execute:
    ```bash
    streamlit run rag_web.py
    ```
3.  Acesse a interface em seu navegador (geralmente `http://localhost:8501`).
    * **Primeira Execução:** Levará mais tempo, pois os PDFs serão processados, e os dados serão salvos no ChromaDB (na pasta definida por `CHROMA_DB_PATH`).
    * **Execuções Subsequentes:** Serão significativamente mais rápidas, pois os dados processados serão carregados do ChromaDB. Apenas PDFs novos ou modificados na pasta `data/` serão reprocessados.

## 📖 Como Usar

1.  Após a inicialização, interaja com o chat na interface web.
2.  Consulte a barra lateral para informações sobre os modelos e arquivos processados.
3.  Para depuração da relevância dos chunks, ative `PRINT_DEBUG_CHUNKS = True` em `config.py` e observe o console.

## 💡 Possíveis Melhorias (TODO)

* Implementar estratégias de chunking mais avançadas.
* Adicionar suporte para outros formatos de documento.
* Interface para gerenciar modelos e reindexação de dados.
* Mecanismo de feedback do usuário.

## 📄 Licença

A definir.