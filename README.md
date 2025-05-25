# Sistema de Pesquisa RAG com Ollama, Streamlit e ChromaDB

**Nota Importante:** O código-fonte base para o sistema descrito neste guia foi gerado com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

## Visão Geral do Projeto

Este projeto implementa um sistema de Geração Aumentada por Recuperação (RAG) que permite aos usuários fazer perguntas em linguagem natural sobre um conjunto de documentos PDF. O sistema utiliza **ChromaDB** para **armazenamento persistente** de chunks de texto e seus embeddings, resultando em inicializações significativamente mais rápidas após o primeiro processamento. As respostas são geradas por um Modelo de Linguagem Grande (LLM) hospedado localmente via Ollama, com o contexto relevante extraído dos documentos. A interface do usuário é fornecida através de uma aplicação web Streamlit.

O objetivo é fornecer uma ferramenta de pesquisa semântica poderosa e flexível que possa ser executada localmente, garantindo a privacidade dos dados e permitindo a customização dos modelos utilizados.

## 🚀 Funcionalidades Principais

* **Processamento de PDFs:** Extrai texto de arquivos PDF localizados em uma pasta `data/`.
* **Persistência com ChromaDB:** Chunks de texto e seus embeddings são armazenados no ChromaDB, evitando reprocessamento em cada inicialização.
* **Processamento Inteligente:** Verifica arquivos PDF novos ou modificados (com base na data de modificação e tamanho) e atualiza o banco de dados incrementalmente. Arquivos PDF removidos da pasta de dados têm seus respectivos chunks deletados do ChromaDB.
* **Geração de Embeddings:** Utiliza modelos `SentenceTransformers` para criar representações vetoriais (embeddings) dos trechos de texto.
* **Busca Vetorial Eficiente:** ChromaDB gerencia a indexação e busca de similaridade.
* **Integração com Ollama:** Conecta-se a um servidor Ollama local para utilizar diversos LLMs (ex: Llama 3, Mistral) para a geração de respostas.
* **Interface Web Interativa:** Interface de usuário amigável construída com Streamlit para submeter perguntas e visualizar respostas.
* **Interface de Terminal (Opcional):** Um script `rag_terminal.py` para interação via linha de comando também está disponível.
* **Consultas em Lote:** Script `rag_batch_query.py` para processar múltiplas perguntas de um arquivo texto.
* **Configurável:** Parâmetros como modelos de embedding e LLM, caminhos de armazenamento, comportamento de chunking, e flags de depuração podem ser ajustados centralmente através de um arquivo `config.py`.
* **Timestamps no Chat:** Opção para exibir data e hora nas mensagens das interfaces de chat.

## 🛠️ Tecnologias Utilizadas

* **Python:** Linguagem de programação principal (versão 3.10 ou 3.11 recomendada).
* **Ollama:** Para servir LLMs localmente.
* **Streamlit:** Para a interface web.
* **ChromaDB:** Para armazenamento persistente e busca de embeddings e documentos.
* **SentenceTransformers:** Para geração de embeddings de texto.
* **PyMuPDF (Fitz):** Para extração de texto de PDFs.
* **NumPy:** Para operações numéricas.

## 🏗️ Arquitetura do Sistema

O diagrama abaixo ilustra os principais componentes do sistema RAG, suas interações e o fluxo de dados, desde o processamento inicial dos documentos PDF até a geração da resposta para a consulta do usuário. Ele destaca como as entradas são processadas, onde os dados são armazenados (ChromaDB), e como os diferentes scripts e modelos interagem.

![Diagrama do Sistema RAG](assets/diagrama_rag_sistema.svg)

## 📂 Estrutura do Projeto

A estrutura de diretórios e arquivos esperada para o projeto é: