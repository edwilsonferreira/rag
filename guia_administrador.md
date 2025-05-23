# Guia do Administrador: Sistema RAG com Ollama e Streamlit

**Nota Importante:** O código-fonte base para o sistema descrito neste guia foi gerado com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

**Data do Documento:** 23 de Maio de 2025

## 1. Introdução

Este documento fornece um guia completo para administradores de sistema sobre como configurar, instalar, executar e manter o sistema de Geração Aumentada por Recuperação (RAG). O sistema é projetado para processar documentos PDF, indexar seu conteúdo e permitir que os usuários façam perguntas em linguagem natural, recebendo respostas geradas por um Modelo de Linguagem Grande (LLM) localmente hospedado via Ollama, com contexto recuperado dos documentos. A interface do usuário é fornecida através de uma aplicação web Streamlit.

## 2. Requisitos do Sistema

### 2.1. Software
* **Python:** Versão 3.10 ou 3.11 (recomendado para melhor compatibilidade com as bibliotecas). Evite versões muito recentes como 3.13+ até que o suporte das bibliotecas esteja totalmente maduro.
* **Ollama:** Servidor Ollama instalado e em execução. (Disponível em [ollama.com](https://ollama.com/))
* **Pip:** Gerenciador de pacotes Python (geralmente vem com a instalação do Python).
* **Sistema Operacional:** Linux, macOS ou Windows (com WSL2 para melhor experiência com Ollama, se preferível).

### 2.2. Hardware (Recomendações Mínimas)
* **RAM:**
    * Mínimo de 8GB para modelos LLM e de embedding menores.
    * 16GB+ recomendado para modelos LLM maiores (ex: `llama3:8b`, `mistral:7b`) e processamento de mais documentos.
    * 32GB+ para modelos LLM significativamente maiores (ex: `llama3:70b`, `mixtral`).
* **CPU:** Processador moderno multi-core.
* **GPU (Opcional, mas Recomendado para Ollama):**
    * Placa NVIDIA com drivers CUDA para aceleração de LLMs via Ollama (melhora significativamente o desempenho).
    * Alternativamente, Ollama pode rodar em CPU, mas será mais lento.
    * A biblioteca FAISS usada para busca vetorial está configurada para CPU (`faiss-cpu`).
* **Espaço em Disco:**
    * Suficiente para os PDFs de entrada.
    * Espaço para os modelos LLM baixados pelo Ollama (podem variar de GBs a dezenas de GBs).
    * Espaço para modelos de embedding (centenas de MBs a GBs).
    * Espaço para o índice FAISS (depende do número de chunks).

## 3. Estrutura do Projeto

Certifique-se de que o software está organizado com a seguinte estrutura de diretórios e arquivos:

seu_projeto_rag/
├── data/                 # Pasta para armazenar os arquivos PDF de entrada
│   └── exemplo.pdf
│   └── outro_documento.pdf
├── config.py             # Arquivo de configuração global
├── rag_core.py           # Lógica principal do sistema RAG
├── rag_web.py            # Interface web com Streamlit
└── requirements.txt      # Lista de dependências Python


## 4. Preparação do Ambiente

### 4.1. Instalar Python
Se o Python (versão 3.10 ou 3.11) não estiver instalado, baixe-o em [python.org](https://www.python.org/downloads/) e siga as instruções de instalação para o seu sistema operacional. Certifique-se de adicionar o Python ao PATH do sistema durante a instalação.

### 4.2. Criar um Ambiente Virtual
É altamente recomendável usar um ambiente virtual para isolar as dependências do projeto.

1.  Navegue até a pasta raiz do projeto (`seu_projeto_rag/`) no seu terminal.
2.  Crie um ambiente virtual (vamos chamá-lo de `.venv`):
    ```bash
    python -m venv .venv
    ```
    (No Windows, pode ser `py -m venv .venv`)

### 4.3. Ativar o Ambiente Virtual
* **Linux/macOS:**
    ```bash
    source .venv/bin/activate
    ```
* **Windows (Command Prompt):**
    ```bash
    .venv\Scripts\activate.bat
    ```
* **Windows (PowerShell):**
    ```bash
    .venv\Scripts\Activate.ps1
    ```
    Você pode precisar ajustar a política de execução no PowerShell:
    ```bash
    Set-ExecutionPolicy Unrestricted -Scope Process
    ```
    Seu prompt de terminal deve mudar para indicar que o ambiente virtual está ativo (ex: `(.venv) seu_prompt$`).

## 5. Configuração do Ollama

### 5.1. Instalar Ollama
Siga as instruções de instalação para o seu sistema operacional em [ollama.com](https://ollama.com/).

### 5.2. Baixar Modelos LLM
O sistema é configurado para usar um modelo LLM padrão definido em `config.py` (ex: `llama3:latest`). Você precisa baixar este modelo (e quaisquer outros que deseje usar) através do Ollama.

Abra um novo terminal (ou use o atual, fora do ambiente virtual se preferir, pois o comando `ollama` é global) e execute:
```bash
ollama pull <nome_do_modelo_ollama>
```
Por exemplo, para o padrão llama3:latest:

```bash
ollama pull llama3:latest
```
Para verificar os modelos baixados:

```bash
ollama list
```
### 5.3. Garantir que o Servidor Ollama Esteja em Execução

O servidor Ollama geralmente inicia automaticamente após a instalação e roda em segundo plano. Se a aplicação Python não conseguir se conectar, verifique se o serviço Ollama está ativo. Em alguns sistemas, pode ser necessário iniciá-lo manualmente.

## 6. Instalação do Software (Dependências Python)
Com o ambiente virtual ativo, instale as dependências Python listadas no arquivo requirements.txt.

### 6.1. Arquivo requirements.txt

Este arquivo deve conter as seguintes bibliotecas (ou as versões especificadas pelo desenvolvedor):

pymupdf
sentence-transformers
faiss-cpu
ollama
numpy
streamlit

### 6.2. Comando de Instalação

Navegue até a pasta raiz do projeto (seu_projeto_rag/) no terminal (com o ambiente virtual ativo) e execute:

```bash
pip install -r requirements.txt
```

Isso instalará todas as bibliotecas necessárias e suas dependências.

Principais dependências:

pymupdf: Para extração de texto de arquivos PDF.
sentence-transformers: Para gerar embeddings de texto.
faiss-cpu: Para criar e pesquisar em um índice vetorial eficiente (versão CPU).
ollama: Cliente Python para interagir com o servidor Ollama.
numpy: Para operações numéricas, dependência de FAISS e SentenceTransformers.
streamlit: Para criar e servir a interface web do usuário.

## 7. Configuração do Sistema (config.py)
O arquivo config.py centraliza as configurações globais do sistema. Modifique este arquivo para ajustar o comportamento padrão:

```
# config.py

# Flag para controlar a impressão de chunks recuperados para depuração
PRINT_DEBUG_CHUNKS: bool = True  # Mude para False para desabilitar logs de chunks no console

# Flag para controlar a exibição de data e hora nas mensagens do chat
SHOW_CHAT_TIMESTAMPS: bool = True # Defina como False para ocultar timestamps

# Modelos padrão
DEFAULT_OLLAMA_MODEL: str = "llama3:latest"
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Pasta padrão para os dados (arquivos PDF)
DEFAULT_DATA_FOLDER: str = "data"

# Parâmetros padrão para chunking
DEFAULT_CHUNK_SIZE: int = 768
DEFAULT_CHUNK_OVERLAP: int = 100

# Parâmetro k padrão para recuperação de chunks
DEFAULT_RETRIEVAL_K: int = 5
Opções de Configuração:

PRINT_DEBUG_CHUNKS: Se True, os chunks de texto recuperados para cada consulta serão impressos no console onde o Streamlit está rodando. Útil para depuração.
SHOW_CHAT_TIMESTAMPS: Se True, as interfaces de chat (web e terminal) exibirão a data e hora de cada mensagem.
DEFAULT_OLLAMA_MODEL: O nome do modelo LLM que o Ollama deve usar (ex: "llama3:latest", "mistral:latest"). Certifique-se de que este modelo foi baixado via ollama pull.
DEFAULT_EMBEDDING_MODEL: O nome do modelo da biblioteca SentenceTransformers usado para gerar embeddings (ex: "all-MiniLM-L6-v2", "all-mpnet-base-v2").
DEFAULT_DATA_FOLDER: O nome da subpasta onde os arquivos PDF de entrada devem ser colocados.
DEFAULT_CHUNK_SIZE: O tamanho alvo (aproximado em caracteres) para cada chunk de texto.
DEFAULT_CHUNK_OVERLAP: O tamanho da sobreposição (aproximado em caracteres) entre chunks consecutivos.
DEFAULT_RETRIEVAL_K: O número de chunks de texto mais relevantes a serem recuperados para cada consulta.
```

## 8. Preparando Dados de Entrada
Crie a pasta data (ou o nome especificado em DEFAULT_DATA_FOLDER no config.py) dentro da pasta raiz do projeto (seu_projeto_rag/).
Copie todos os arquivos PDF que você deseja que o sistema processe para dentro desta pasta data/.
Qualidade dos PDFs: O sistema funciona melhor com PDFs que contêm texto digital (selecionável). PDFs que são apenas imagens escaneadas (sem uma camada de OCR - Reconhecimento Óptico de Caracteres) não produzirão texto para indexação, a menos que uma etapa de OCR externa seja aplicada previamente. O sistema atual não inclui OCR.

## 9. Executando o Sistema
Com o ambiente preparado, Ollama rodando, dependências instaladas, config.py ajustado e PDFs na pasta data:

Certifique-se de que seu ambiente virtual está ativo.
Navegue até a pasta raiz do projeto (seu_projeto_rag/) no terminal.
Execute o seguinte comando para iniciar a interface web Streamlit:

```bash
streamlit run rag_web.py
```

Ou, para a interface de terminal (se ainda estiver sendo utilizada):

```bash
python rag_terminal.py
```
- Primeira Execução:
Pode levar algum tempo, pois o modelo de embedding será baixado (se for a primeira vez que é usado).
Os documentos PDF na pasta data/ serão processados, os embeddings serão gerados e o índice FAISS será construído. Isso também pode levar tempo dependendo do número e tamanho dos PDFs.
A interface Streamlit mostrará uma mensagem "Inicializando o Sistema RAG..." durante este processo.

- Acessando a Interface Web:
Após a inicialização, o Streamlit geralmente abrirá automaticamente a interface em seu navegador web padrão.
Caso não abra, o terminal exibirá URLs locais (ex: Local URL: http://localhost:8501) que você pode abrir manualmente em seu navegador.

## 10. Solução de Problemas Comuns
- Erro "Ollama server not running" ou Conexão Recusada:
Verifique se o serviço/aplicação Ollama está realmente em execução no seu sistema.
Modelo LLM/Embedding Não Encontrado:
Para Ollama: Use ollama list para verificar os modelos baixados. Use ollama pull <nome_modelo> se necessário.
Para SentenceTransformer: Verifique a conexão com a internet para o download inicial do modelo. Verifique se há erros de digitação no nome do modelo em config.py.

- Nenhum Arquivo PDF Processado ou "Informação não disponível em RAGCore":
Verifique se os arquivos PDF estão na pasta data/ correta.
Verifique se os PDFs contêm texto extraível.
Confirme se as modificações em rag_core.py para o atributo processed_pdf_files foram aplicadas e salvas corretamente.
Reinicie completamente a aplicação Streamlit (Ctrl+C e streamlit run rag_web.py novamente) para limpar qualquer cache de objetos desatualizados.

- Respostas de Baixa Qualidade:
Consulte as sugestões no guia de desenvolvimento ou na documentação do projeto sobre como melhorar a qualidade (ajuste de chunking, modelos de embedding, modelo LLM, prompt, parâmetro k).
Ative PRINT_DEBUG_CHUNKS = True em config.py para inspecionar os chunks recuperados.
Erros de asyncio ou RuntimeError: no running event loop (especialmente com Python 3.12+):
Considere usar uma versão do Python mais estabelecida como 3.10 ou 3.11, pois bibliotecas como Streamlit podem ter melhor compatibilidade.

## 11. Manutenção
Atualizando Modelos:
Ollama LLMs: Use ```ollama pull <nome_modelo>:latest``` para obter a versão mais recente de um modelo.
Modelos de Embedding: Se você mudar DEFAULT_EMBEDDING_MODEL em config.py, o sistema RAG irá (ao reiniciar) reprocessar os embeddings na próxima vez que for inicializado, pois o RAGCore é recriado.

- Adicionando/Removendo PDFs:
Se você adicionar, remover ou modificar arquivos PDF na pasta data/, você precisará reiniciar a aplicação Streamlit (ou a aplicação de terminal). Isso fará com que o RAGCore seja recriado e reprocesse todos os documentos na pasta data/, atualizando o índice.

- Atualizando Dependências:
Periodicamente, você pode querer atualizar as bibliotecas Python para as versões mais recentes:
```bash
pip install --upgrade -r requirements.txt
```
Faça isso com cautela e teste após as atualizações, pois novas versões podem introduzir alterações incompatíveis.
