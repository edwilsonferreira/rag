# Sistema de Pesquisa RAG com Ollama e Streamlit

Este projeto implementa um sistema de Geração Aumentada por Recuperação (RAG) que permite aos usuários fazer perguntas em linguagem natural sobre um conjunto de documentos PDF. As respostas são geradas por um Modelo de Linguagem Grande (LLM) hospedado localmente via Ollama, com o contexto relevante extraído dos documentos PDF. A interface do usuário é construída com Streamlit.

**Nota Importante:** O código-fonte base para este sistema foi desenvolvido com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

## 🚀 Funcionalidades Principais

* **Processamento de PDFs:** Extrai texto de arquivos PDF localizados em uma pasta `data/`.
* **Geração de Embeddings:** Utiliza modelos `SentenceTransformers` para criar representações vetoriais (embeddings) dos trechos de texto.
* **Indexação e Busca Vetorial:** Emprega FAISS para indexar os embeddings e realizar buscas de similaridade eficientes.
* **Integração com Ollama:** Conecta-se a um servidor Ollama local para utilizar diversos LLMs (ex: Llama 3, Mistral) para a geração de respostas.
* **Interface Web Interativa:** Interface de usuário amigável construída com Streamlit para submeter perguntas e visualizar respostas.
* **Configurável:** Parâmetros como modelos de embedding e LLM, comportamento de chunking, e depuração podem ser ajustados através de um arquivo `config.py`.
* **Timestamps no Chat:** Opção para exibir data e hora nas mensagens da interface web e do terminal interativo.

## 🛠️ Tecnologias Utilizadas

* **Python:** Linguagem de programação principal.
* **Ollama:** Para servir LLMs localmente.
* **Streamlit:** Para a interface web.
* **SentenceTransformers:** Para geração de embeddings de texto.
* **FAISS:** Para busca de similaridade em vetores.
* **PyMuPDF (Fitz):** Para extração de texto de PDFs.
* **NumPy:** Para operações numéricas.

## ⚙️ Configuração e Instalação

Siga estes passos para configurar e executar o projeto localmente.

### Pré-requisitos

1.  **Python:** Versão 3.10 ou 3.11 recomendada.
2.  **Git:** Para clonar o repositório (se aplicável) e gerenciar o código.
3.  **Ollama:** Servidor Ollama instalado e em execução.
    * Instale a partir de [ollama.com](https://ollama.com/).
    * Baixe o modelo LLM que você pretende usar (ver `config.py` para o padrão). Exemplo:
        ```bash
        ollama pull llama3:latest
        ```
        Verifique os modelos baixados com `ollama list`.

### Passos de Instalação

1.  **Clone o Repositório (se estiver acessando via Git):**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO_AQUI>
    cd <NOME_DA_PASTA_DO_REPOSITORIO>
    ```
    Se você já tem os arquivos localmente, pule este passo e navegue até a pasta do projeto.

2.  **Crie e Ative um Ambiente Virtual:**
    É altamente recomendado usar um ambiente virtual.
    ```bash
    python -m venv .venv
    # Linux/macOS
    source .venv/bin/activate
    # Windows
    # .venv\Scripts\activate
    ```

3.  **Instale as Dependências:**
    Com o ambiente virtual ativo, instale os pacotes listados em `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### Configuração do Projeto

1.  **Arquivo `config.py`:**
    Este arquivo centraliza as configurações principais do sistema. Ajuste os seguintes parâmetros conforme necessário:
    * `PRINT_DEBUG_CHUNKS`: `True` ou `False` para imprimir os chunks recuperados no console.
    * `SHOW_CHAT_TIMESTAMPS`: `True` ou `False` para exibir data/hora no chat.
    * `DEFAULT_OLLAMA_MODEL`: Nome do modelo LLM a ser usado pelo Ollama (ex: `"llama3:70b"`, `"mistral:latest"`).
    * `DEFAULT_EMBEDDING_MODEL`: Nome do modelo SentenceTransformer (ex: `"all-mpnet-base-v2"`).
    * `DEFAULT_DATA_FOLDER`: Nome da pasta para os PDFs (padrão: `"data"`).
    * `DEFAULT_CHUNK_SIZE`, `DEFAULT_CHUNK_OVERLAP`: Parâmetros para divisão do texto.
    * `DEFAULT_RETRIEVAL_K`: Número de chunks a serem recuperados.

2.  **Dados de Entrada (PDFs):**
    * Crie uma pasta chamada `data` (ou o nome definido em `DEFAULT_DATA_FOLDER` no `config.py`) na raiz do projeto.
    * Coloque todos os arquivos PDF que você deseja que o sistema processe dentro desta pasta.
    * **Nota:** O sistema funciona melhor com PDFs que contêm texto selecionável. Arquivos PDF baseados em imagem (scans) sem uma camada de OCR não fornecerão texto.

## ▶️ Executando a Aplicação

1.  Certifique-se de que o servidor Ollama está em execução.
2.  Com seu ambiente virtual ativo e na pasta raiz do projeto, execute:
    ```bash
    streamlit run rag_web.py
    ```
3.  A aplicação web será aberta automaticamente no seu navegador padrão (geralmente em `http://localhost:8501`).
    * Na primeira execução, pode levar algum tempo para o modelo de embedding ser baixado e os documentos serem processados.

## 📖 Como Usar

1.  Após a inicialização, a interface web estará pronta.
2.  Na barra lateral, você pode ver informações sobre o sistema, como os modelos em uso e os arquivos PDF processados.
3.  Digite sua pergunta na caixa de chat na parte inferior da página e pressione Enter.
4.  O sistema buscará informações relevantes nos seus PDFs e usará o LLM para gerar uma resposta.
5.  Opcionalmente, ative `PRINT_DEBUG_CHUNKS = True` em `config.py` e monitore o console (onde você executou `streamlit run ...`) para ver os chunks de texto que foram recuperados para sua pergunta, o que é útil para depuração e otimização.

## 💡 Possíveis Melhorias (TODO)

* Implementar estratégias de chunking mais avançadas (ex: semântica, baseada em layout).
* Adicionar suporte para outros formatos de documento além de PDF.
* Opção para salvar/carregar o índice FAISS para evitar reprocessamento.
* Interface para gerenciar/selecionar modelos Ollama e de embedding diretamente na UI.
* Mecanismo de feedback do usuário sobre a qualidade das respostas.

## 📄 Licença

A definir.