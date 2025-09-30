# Sistema de Pesquisa RAG com Suporte Duplo para LLMs (Gemini + Ollama)

**Nota Importante:** O código-fonte base para o sistema descrito neste guia foi gerado com o valioso apoio da inteligência artificial Gemini, desenvolvida pelo Google. As funcionalidades e estruturas foram então iterativamente refinadas e adaptadas para os requisitos específicos deste projeto de pesquisa.

## Visão Geral do Projeto

Este projeto implementa um sistema de Geração Aumentada por Recuperação (RAG) que permite aos usuários fazer perguntas em linguagem natural sobre um conjunto de documentos PDF e Markdown. O sistema utiliza **ChromaDB** para **armazenamento persistente** de chunks de texto e seus embeddings, resultando em inicializações significativamente mais rápidas após o primeiro processamento. 

**🆕 NOVIDADE:** O sistema agora oferece **suporte duplo para LLMs**, permitindo escolher entre:
- **Google Gemini** (via API - requer chave de API)
- **Ollama Local** (executado localmente - privacidade total)

As respostas são geradas pelo LLM selecionado, com contexto relevante extraído dos documentos. A interface do usuário é fornecida através de uma aplicação web Streamlit com detecção automática do provedor ativo.

O objetivo é fornecer uma ferramenta de pesquisa semântica poderosa e flexível que possa ser executada localmente, garantindo a privacidade dos dados e permitindo a customização dos modelos utilizados.

## 🚀 Funcionalidades Principais

### 🧠 **Suporte Duplo para LLMs (NOVO!)**
* **Google Gemini:** Integração via API (modelo gemini-2.5-flash)
* **Ollama Local:** Para máxima privacidade (modelos llama3.2:1b, llama3:latest, etc.)
* **Switching Dinâmico:** Alternar entre provedores via `config.py`
* **Interface Adaptativa:** Detecção automática do provedor ativo

### 🛡️ **Segurança Integrada (MELHORADO!)**
* **Diretiva de Segurança Flexível:** Proteção contra engenharia social mantendo funcionalidade
* **Instruções Protegidas:** Sistema imune a tentativas de vazamento de configurações internas
* **Resposta Inteligente:** Permite explicações detalhadas de procedimentos documentados

### 🌐 **Sistema de Conhecimento Externo (NOVO!)**
* **Wikipedia Integration:** Complementa informações locais com conhecimento educacional
* **Base Conceitual:** Definições automáticas para termos técnicos não cobertos
* **Ativação Inteligente:** Usa conhecimento externo apenas quando informações locais são insuficientes
* **Controle Granular:** Configuração detalhada via `EXTERNAL_KNOWLEDGE_CONFIG`

### 📊 **Sistema de Logging Aprimorado (NOVO!)**
* **Métricas de Qualidade:** Análise automática da relevância dos chunks recuperados
* **Avisos Inteligentes:** Alertas quando relevância está baixa com sugestões de melhoria
* **Rastreamento Completo:** Log detalhado do fluxo de processamento para debugging
* **Fallback Estruturado:** Respostas organizadas quando informações estão incompletas

### 📚 **Processamento de Documentos**
* **Múltiplos Formatos (NOVO!):** Suporte a arquivos PDF (.pdf), Markdown (.md, .markdown)
* **Processamento de PDFs:** Extrai texto e tabelas de arquivos PDF com PyMuPDF
* **Processamento de Markdown:** Suporte nativo a arquivos .md e .markdown com encoding UTF-8
* **Persistência com ChromaDB:** Chunks de texto e seus embeddings são armazenados no ChromaDB, evitando reprocessamento
* **Processamento Inteligente:** Detecção automática de documentos novos/modificados com atualização incremental
* **Geração de Embeddings:** Utiliza modelos `SentenceTransformers` (all-MiniLM-L6-v2)
* **Busca Vetorial Eficiente:** ChromaDB gerencia indexação e busca semântica unificada

### 💻 **Interfaces Múltiplas**
* **Interface Web Interativa:** Streamlit com sidebar informativo
* **Interface de Terminal:** Script `rag_terminal.py` para uso via CLI
* **Consultas em Lote:** Script `rag_batch_query.py` para processamento automatizado
* **Configuração Centralizada:** Via `src/rag_app/config.py` e arquivo `.env`
* **Timestamps no Chat:** Opcional para tracking de conversas

## 🛠️ Tecnologias Utilizadas

### 🧠 **Modelos de Linguagem**
* **Google Gemini:** API do Google para LLM em nuvem (gemini-2.5-flash)
* **Ollama:** Para servir LLMs localmente (llama3.2:1b, llama3:latest, etc.)

### 🔧 **Framework e Interface**
* **Python:** Linguagem de programação principal (versão 3.9+ recomendada)
* **Streamlit:** Para a interface web interativa
* **python-dotenv:** Para gerenciamento seguro de variáveis de ambiente

### 🗄️ **Armazenamento e Processamento**
* **ChromaDB:** Para armazenamento persistente e busca de embeddings
* **SentenceTransformers:** Para geração de embeddings de texto (all-MiniLM-L6-v2)
* **PyMuPDF (Fitz):** Para extração de texto e tabelas de PDFs
* **Processamento de Markdown:** Suporte nativo com encoding UTF-8 e fallback latin-1
* **NumPy:** Para operações numéricas e manipulação de arrays

## 🏗️ Arquitetura do Sistema

O diagrama abaixo ilustra os principais componentes do sistema RAG, suas interações e o fluxo de dados, desde o processamento inicial dos documentos PDF até a geração da resposta para a consulta do usuário. Ele destaca como as entradas são processadas, onde os dados são armazenados (ChromaDB), e como os diferentes scripts e modelos interagem.

![Diagrama do Sistema RAG](assets/diagrama_rag_sistema.svg)

## 📂 Estrutura do Projeto

A estrutura de diretórios e arquivos esperada para o projeto é:

seu_projeto_rag/  
├── src/  
│   └── rag_app/             # Pacote Python principal  
│       ├── init.py  
│       ├── config.py  
│       ├── rag_core.py          # Core melhorado com conhecimento externo
│       ├── external_knowledge.py # Sistema de conhecimento externo (NOVO!)
│       ├── rag_web.py  
│       ├── rag_terminal.py  
│       └── rag_batch_query.py  
├── data/                     # Documentos de entrada: PDFs (.pdf) e Markdown (.md, .markdown)  
├── chroma_db_store/          # Banco de dados ChromaDB (relativo à raiz do projeto)  
├── assets/                   # Ativos como diagramas  
│   └── diagrama_rag_sistema.svg  
├── processed_files_status.json # Rastreia PDFs processados (relativo à raiz do projeto)  
├── requirements.txt          # Dependências Python
├── .env                      # Variáveis de ambiente (chaves de API)
├── DIRETIVA_SEGURANCA.md    # Documentação da diretiva de segurança
└── README.md                 # Este arquivo  
  

## 🔧 Configuração de Provedor LLM

O sistema suporta dois provedores de LLM que podem ser alternados via configuração:

### 🌐 **Google Gemini (Recomendado para Produção)**
```python
# Em src/rag_app/config.py
LLM_PROVIDER: str = "gemini"
```

**Configuração necessária:**
1. Obter chave de API: https://makersuite.google.com/app/apikey
2. Criar arquivo `.env` na raiz do projeto:
   ```
   GOOGLE_API_KEY=sua_chave_aqui
   ```
3. **Vantagens:** Alta qualidade, sem setup local, sempre disponível
4. **Desvantagens:** Requer internet, custo por uso, dados enviados para Google

### 🏠 **Ollama Local (Recomendado para Privacidade)**
```python
# Em src/rag_app/config.py
LLM_PROVIDER: str = "ollama"
```

**Configuração necessária:**
1. Instalar Ollama: https://ollama.com
2. Baixar modelo: `ollama pull llama3.2:1b` (recomendado para sistemas com pouca RAM)
3. **Vantagens:** Privacidade total, sem custos, funciona offline
4. **Desvantagens:** Requer hardware local, setup mais complexo

### 🔄 **Alternando entre Provedores**
Basta modificar `LLM_PROVIDER` em `config.py` e reiniciar a aplicação. A interface detecta automaticamente o provedor ativo.

## ⚙️ Configuração e Execução do Sistema

Siga estes passos detalhados para configurar e executar o projeto.

### 1. Requisitos do Sistema
(Conforme detalhado anteriormente: Python 3.10/3.11, Ollama, Pip, Git, Hardware adequado)

### 2. Preparação do Ambiente

1.  **Instalar Python.**
2.  **Clonar o Repositório (se aplicável).**
3.  **Criar e Ativar um Ambiente Virtual:**
    Na pasta raiz do projeto (`seu_projeto_rag/`):
    ```bash
    python -m venv .venv
    ```
    Para ativar:
    * **Linux/macOS:** `source .venv/bin/activate`
    * **Windows (CMD):** `.venv\Scripts\activate.bat`
    * **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

### 3. Configuração do Ollama
(Instalar Ollama, baixar modelos LLM como `ollama pull llama3:latest`).

### 4. Instalação das Dependências Python
Com o ambiente virtual ativo, na pasta raiz do projeto:
```bash
pip install -r requirements.txt
```
(O arquivo requirements.txt deve listar pymupdf, sentence-transformers, ollama, numpy, streamlit, chromadb).

### 5. Configuração do Projeto (src/rag_app/config.py)

O arquivo src/rag_app/config.py é o centro de controle para os parâmetros do sistema. Ajuste-o conforme suas necessidades. Os caminhos como DEFAULT_DATA_FOLDER, CHROMA_DB_PATH, PROCESSED_FILES_STATUS_JSON são relativos ao diretório de onde os scripts são executados (geralmente a raiz do projeto ao usar os comandos de execução recomendados).

Python
#### 5.1 src/rag_app/config.py (principais parâmetros)
from typing import List # Necessário para EXIT_COMMANDS

#### 5.2 Flags de Depuração e Comportamento
PRINT_DEBUG_CHUNKS: bool = True       # True para imprimir chunks recuperados no console.
SHOW_CHAT_TIMESTAMPS: bool = True     # True para exibir data/hora no chat.
ALWAYS_INCLUDE_PAGE_IN_ANSWER: bool = False # True para instruir o LLM a SEMPRE tentar citar a fonte/página.

#### 5.3 Comandos para finalizar loops interativos (ex: rag_terminal)
EXIT_COMMANDS: List[str] = [
    "sair", "saia", "exit", "quit", "q",
    "parar", "pare", "stop",
    "finalizar", "finalize", "fim", "end",
    "fechar", "close",
    "terminar", "terminate", "bye"
]

#### 5.4 Modelos Padrão
DEFAULT_OLLAMA_MODEL: str = "llama3:latest"
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

#### 5.5 Caminhos e Nomes de Coleção/Status
DEFAULT_DATA_FOLDER: str = "data"
CHROMA_DB_PATH: str = "./chroma_db_store" 
CHROMA_COLLECTION_NAME: str = "rag_documents"
PROCESSED_FILES_STATUS_JSON: str = "processed_files_status.json"

##### 5.6 Parâmetros de Chunking e Recuperação
DEFAULT_CHUNK_SIZE: int = 768
DEFAULT_CHUNK_OVERLAP: int = 100
DEFAULT_RETRIEVAL_K: int = 5

#### 5.7 Configurações do Provedor LLM (NOVO!):

**LLM_PROVIDER: str = "gemini"**  
Define qual provedor usar: `"gemini"` (Google Gemini API) ou `"ollama"` (Ollama local)

**Configurações do Google Gemini:**
- `GEMINI_MODEL: str = "gemini-2.5-flash"` - Modelo Gemini a usar
- `GOOGLE_API_KEY: str` - Carregado automaticamente do arquivo `.env`
- `GEMINI_TEMPERATURE: float = 0.7` - Criatividade das respostas (0.0-1.0)
- `GEMINI_MAX_TOKENS: int = 4096` - Limite de tokens por resposta

**Configurações do Ollama:**
- `DEFAULT_OLLAMA_MODEL: str = "llama3.2:1b"` - Modelo Ollama (otimizado para baixa RAM)
- `OLLAMA_HOST: str = "http://192.168.64.4:11434"` - Endpoint do servidor Ollama

#### 5.8 Diretiva de Segurança (MELHORADO!):

**SECURITY_DIRECTIVE: str**  
Instruções de segurança incorporadas automaticamente em todos os prompts para proteger contra:
- Tentativas de extração de instruções internas
- Engenharia social e injeção de prompts
- Vazamento de configurações do sistema
- **NOVO:** Permite explicações detalhadas de procedimentos e cálculos presentes nos documentos

#### 5.9 Sistema de Conhecimento Externo (NOVO!):

**ALLOW_EXTERNAL_KNOWLEDGE: bool = True**  
Controla se o sistema pode consultar fontes externas além dos documentos carregados.

**EXTERNAL_KNOWLEDGE_CONFIG: dict**  
Configurações detalhadas para uso de conhecimento externo:
- `min_chunks_threshold: int = 2` - Mínimo de chunks locais para NÃO usar externo
- `confidence_threshold: float = 0.3` - Score mínimo para considerar chunks locais suficientes
- `max_external_results: int = 3` - Máximo de resultados externos a incluir
- `concept_keywords: list` - Palavras-chave que ativam busca por conceitos
- `enable_wikipedia: bool = True` - Ativa/desativa integração com Wikipedia
- `enable_educational_concepts: bool = True` - Ativa base de conceitos educacionais

#### 5.10 Sistema de Logging e Qualidade (NOVO!):

**Métricas Automáticas:**
- Análise da distância média dos chunks recuperados
- Avisos quando relevância está abaixo do limiar configurado
- Sugestões automáticas para reformulação de perguntas
- Log detalhado do fluxo de decisão do sistema

#### 5.11 Outros Parâmetros:

**ALWAYS_INCLUDE_PAGE_IN_ANSWER: bool:**
Se True, instrui o LLM a sempre citar fonte e página nas respostas.

**EXIT_COMMANDS: List[str]:**
Comandos para encerrar loops interativos (terminal).


### 6. Preparando Dados de Entrada

Crie a pasta `data/` na raiz do projeto e adicione seus documentos nos formatos suportados:

#### 📄 **Formatos de Documento Suportados**

**🆕 SUPORTE MÚLTIPLO:** O sistema agora processa automaticamente diferentes tipos de arquivo:

| Formato | Extensões | Características | Processamento |
|---------|-----------|-----------------|---------------|
| **PDF** | `.pdf` | Texto, tabelas, múltiplas páginas | PyMuPDF (Fitz) - Extração completa |
| **Markdown** | `.md`, `.markdown` | Texto formatado, seções, tabelas | Processamento nativo UTF-8 |

**Exemplo de estrutura:**

```text
data/
├── documento1.pdf        # ✅ Será processado
├── manual.md            # ✅ Será processado  
├── README.markdown      # ✅ Será processado
├── texto.txt           # ❌ Não suportado
└── arquivo.docx        # ❌ Não suportado
```

**💡 Exemplo de uso com Markdown:**

Suponha que você tenha um arquivo `data/guia.md`:

```markdown
# Guia do Sistema

## Configuração Inicial
Para configurar o sistema, siga os seguintes passos:

1. Configure as variáveis de ambiente
2. Instale as dependências 
3. Execute o primeiro processamento

## Troubleshooting
- Erro X: Solução Y
- Erro Z: Solução W
```

**Resultado do processamento:**
- ✅ Arquivo detectado automaticamente como Markdown
- ✅ Conteúdo processado preservando estrutura
- ✅ Texto dividido em chunks semânticos
- ✅ Embeddings gerados e armazenados no ChromaDB
- ✅ Busca funcionando: "como configurar o sistema?" → encontra seção relevante

**Características do processamento:**
- **PDFs:** Extração de texto por página + tabelas quando disponíveis
- **Markdown:** Leitura direta com preservação da formatação
- **Detecção automática:** Sistema identifica automaticamente o tipo de arquivo
- **Processamento incremental:** Apenas arquivos novos/modificados são reprocessados
- **Encoding inteligente:** UTF-8 com fallback automático para latin-1

### 7. Executando os Componentes do Sistema

Importante: Todos os comandos a seguir devem ser executados a partir da pasta raiz do seu projeto (seu_projeto_rag/), com o ambiente virtual ativo e o servidor Ollama em execução.

### 7.1 Interface Web com Streamlit (rag_web.py) - Recomendado

Este script inicia a interface gráfica interativa no seu navegador com detecção automática do provedor LLM ativo.

**Para Gemini:**
```bash
streamlit run src/rag_app/rag_web.py
```

**Para Ollama:**
```bash
streamlit run src/rag_app/rag_web.py --server.port 8502
```

**Funcionalidades da Interface:**
- 💬 **Chat interativo** com histórico de conversas
- 🔍 **Sidebar informativo** mostra provedor LLM ativo, estatísticas do ChromaDB
- 📊 **Métricas em tempo real** (chunks indexados, modelo ativo, etc.)
- 🔄 **Detecção automática** do provedor configurado (Gemini/Ollama)

Após a execução, acesse o endereço fornecido no terminal.

### 7.2 Interface de Terminal Interativa (rag_terminal.py)
Permite interagir com o sistema RAG diretamente pelo terminal.

```bash
python -m src.rag_app.rag_terminal
```   
 Siga as instruções no terminal para fazer perguntas. Digite sair para encerrar.

Processamento de Perguntas em Lote (rag_batch_query.py):
Executa múltiplas perguntas de um arquivo de texto e opcionalmente salva as respostas.

```bash
python -m src.rag_app.rag_batch_query <ARQUIVO_DE_ENTRADA> -o <ARQUIVO_DE_SAIDA_OPCIONAL>
```  
<ARQUIVO_DE_ENTRADA>: Caminho para seu arquivo .txt com uma pergunta por linha.
<ARQUIVO_DE_SAIDA_OPCIONAL>: Caminho para um arquivo .txt onde as perguntas e respostas serão salvas. Exemplo:
```bash
python -m src.rag_app.rag_batch_query data/lista_de_perguntas.txt -o resultados/respostas_em_lote.txt
```  
 Teste Direto do RAGCore (rag_core.py) - Para Desenvolvimento/Depuração:
O arquivo rag_core.py contém um bloco if __name__ == '__main__': que permite executar algumas consultas de teste predefinidas diretamente no console. Isso é útil para verificar a lógica central do RAG rapidamente.

```bash
python -m src.rag_app.rag_core
```  
 As perguntas de teste definidas dentro do rag_core.py serão executadas, e as saídas (incluindo chunks de depuração, se PRINT_DEBUG_CHUNKS estiver True em config.py) serão exibidas no console.

Comportamento de Inicialização (para todas as formas de execução):

Primeira Execução / Novos PDFs: O sistema processará os PDFs da pasta data/. Chunks e embeddings serão gerados e salvos no diretório CHROMA_DB_PATH. O arquivo PROCESSED_FILES_STATUS_JSON será criado/atualizado. Esta etapa inicial pode ser demorada.
Execuções Subsequentes: O sistema se conectará ao ChromaDB existente e usará o PROCESSED_FILES_STATUS_JSON para verificar o estado dos arquivos. Apenas PDFs novos ou modificados serão reprocessados. Isso torna a inicialização muito mais rápida.
### 8. Como Usar a Interface Web

(Conforme descrito anteriormente: interaja com o chat, consulte a barra lateral para informações do sistema).

## � Exemplos de Uso Prático

### Cenário 1: Configuração Rápida com Google Gemini
```bash
# 1. Configurar chave de API
echo "GOOGLE_API_KEY=sua_chave_aqui" > .env

# 2. Configurar provedor em config.py
# LLM_PROVIDER: str = "gemini"

# 3. Executar interface web
streamlit run src/rag_app/rag_web.py
```

### Cenário 2: Setup Local com Ollama (Apple Container)
```bash
# 1. Instalar e configurar Ollama
# Consulte: comandos_apple_container_ollama.txt

# 2. Configurar provedor em config.py  
# LLM_PROVIDER: str = "ollama"

# 3. Executar interface web
streamlit run src/rag_app/rag_web.py --server.port 8502
```

### Cenário 3: Processamento em Lote
```bash
# 1. Criar arquivo de perguntas
echo "Qual é a data da inscrição?" > perguntas.txt
echo "Quais são os requisitos?" >> perguntas.txt

# 2. Executar processamento
python -m src.rag_app.rag_batch_query perguntas.txt -o respostas.txt
```

### Cenário 4: Teste do Sistema Melhorado (NOVO!)
```bash
# 1. Criar script de teste rápido
cat > test_pergunta.py << 'EOF'
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from rag_app.rag_core import RAGCore

rag = RAGCore()
pergunta = "Como calcular a renda per capita?"
print(f"Pergunta: {pergunta}")
print("="*50)
resposta = rag.answer_query(pergunta)
print(resposta)
EOF

# 2. Executar teste
python test_pergunta.py
```

**🔍 O que o sistema faz automaticamente:**
- ✅ Analisa qualidade dos chunks encontrados
- ✅ Avisa se relevância está baixa
- ✅ Complementa com conhecimento externo quando necessário
- ✅ Fornece respostas estruturadas e detalhadas
- ✅ Cita fontes e páginas quando disponível

## 📋 Checklist de Configuração

### ✅ Para Google Gemini:
- [ ] Chave de API obtida em https://makersuite.google.com/app/apikey
- [ ] Arquivo `.env` criado com `GOOGLE_API_KEY`
- [ ] `LLM_PROVIDER = "gemini"` em `config.py`
- [ ] Conexão com internet disponível

### ✅ Para Ollama Local:
- [ ] Ollama instalado e executando
- [ ] Modelo baixado (`ollama pull llama3.2:1b`)
- [ ] `LLM_PROVIDER = "ollama"` em `config.py`  
- [ ] `OLLAMA_HOST` configurado corretamente
- [ ] Hardware adequado (mínimo 2GB RAM)

### ✅ Para Sistema de Conhecimento Externo:
- [ ] `ALLOW_EXTERNAL_KNOWLEDGE = True` em `config.py`
- [ ] Conexão com internet para Wikipedia (opcional)
- [ ] Configuração de `EXTERNAL_KNOWLEDGE_CONFIG` ajustada
- [ ] Verificar logs para uso de conhecimento externo

### ✅ Geral:
- [ ] Python 3.9+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Pasta `data/` criada com PDFs
- [ ] Ambiente virtual ativo

## 🛠️ Solução de Problemas Comuns

### 🔴 Erro: "Chave de API não encontrada"
**Solução:** Verificar arquivo `.env` e variável `GOOGLE_API_KEY`
```bash
# Verificar se .env existe e tem conteúdo
cat .env
# Deve mostrar: GOOGLE_API_KEY=sua_chave_aqui
```

### 🔴 Erro: "Ollama não está executando"
**Solução:** Verificar status do container/serviço
```bash
# Para Apple Container Runtime
container list
# Para instalação nativa  
ollama list
```

### 🔴 Erro: "Modelo não encontrado"
**Solução:** Baixar modelo necessário
```bash
# Modelos recomendados por uso de RAM:
ollama pull llama3.2:1b    # ~1.3GB RAM
ollama pull llama3:latest  # ~4.6GB RAM
```

### 🔴 Interface web não carrega
**Solução:** Verificar porta e configurações
```bash
# Tentar porta alternativa
streamlit run src/rag_app/rag_web.py --server.port 8503

# Verificar logs do terminal para erros específicos
```

### 🔴 ChromaDB inconsistente  
**Solução:** Reset completo do banco de dados
```bash
# ATENÇÃO: Isso apaga todos os chunks processados
rm -rf chroma_db_store/
rm -f processed_files_status.json
# Reiniciar aplicação para reprocessamento completo
```

🔄 Manutenção
(Conforme descrito anteriormente: backups do chroma_db_store/ e processed_files_status.json, reprocessamento, atualização de modelos e dependências).
Lembre-se que ao remover um PDF da pasta data/, o sistema deve limpar seus dados do ChromaDB e do arquivo de status na próxima inicialização.

## 🆕 Novidades desta Versão

### v2.1 - Suporte a Múltiplos Formatos de Documento

**🎯 Funcionalidades Principais Adicionadas:**

1. **🆕 Suporte a Arquivos Markdown**
   - Processamento nativo de arquivos `.md` e `.markdown`
   - Encoding UTF-8 com fallback automático para latin-1
   - Preservação da estrutura e formatação do Markdown
   - Integração transparente com o sistema de busca semântica

2. **📄 Arquitetura Multi-Formato**
   - Detecção automática do tipo de arquivo (PDF, Markdown)
   - Processamento modular por tipo de documento
   - Métodos específicos: `_process_pdf_file()` e `_process_markdown_file()`
   - Sistema unificado de chunking e embeddings

3. **🔍 Busca Semântica Aprimorada**
   - Base de conhecimento unificada para PDFs e Markdown
   - Resultados de busca combinando ambos os formatos
   - Metadados preservados para identificação da fonte
   - Performance otimizada para múltiplos tipos de documento

### v2.0 - Suporte Duplo para LLMs + Segurança Avançada

**🎯 Funcionalidades Anteriores:**

1. **Suporte Duplo para LLMs**
   - Google Gemini (API) + Ollama (Local)
   - Switching dinâmico via configuração
   - Interface adaptativa com detecção automática

2. **Sistema de Segurança Integrado**
   - Diretiva de segurança automática em todos os prompts
   - Proteção contra engenharia social e extração de instruções
   - Sistema imune a tentativas de vazamento de configurações

3. **Gerenciamento de Configuração Avançado**
   - Arquivo `.env` para chaves de API seguras
   - Configuração centralizada em `config.py`
   - Suporte a múltiplos modelos e provedores

4. **Interface Aprimorada**
   - Sidebar informativo com estatísticas em tempo real
   - Detecção automática do provedor LLM ativo
   - Melhor experiência de usuário

5. **Documentação Completa**
   - Guia de comandos para Apple Container Runtime
   - Troubleshooting detalhado para ambos provedores
   - Exemplos práticos de configuração

**🔧 Melhorias Técnicas v2.2:**
- ✅ **Sistema de Conhecimento Externo:** Integração Wikipedia + base conceitual própria
- ✅ **Diretiva de Segurança Flexível:** Proteção mantendo funcionalidade completa
- ✅ **Logging Inteligente:** Métricas de qualidade e avisos automáticos
- ✅ **Sistema de Fallback:** Respostas estruturadas para informações incompletas
- ✅ **Detecção de Relevância:** Análise automática da qualidade dos chunks
- ✅ **Resposta Adaptativa:** Complementa conhecimento local com externo quando necessário

**🔧 Melhorias Técnicas v2.1:**
- ✅ Arquitetura multi-formato com processamento modular
- ✅ Sistema de detecção automática de tipos de arquivo
- ✅ Métodos específicos para cada formato de documento
- ✅ Otimização do chunking para diferentes tipos de conteúdo
- ✅ Base de conhecimento unificada com metadados preservados

**🔧 Melhorias Técnicas v2.0:**
- ✅ Refatoração da arquitetura para suporte modular a LLMs
- ✅ Implementação de padrões de segurança enterprise
- ✅ Otimização para modelos menores (llama3.2:1b para baixa RAM)
- ✅ Melhoria na detecção e tratamento de erros

## 🆕 Novidades da Versão 2.2

### 🎯 **Problema Resolvido: Respostas Inadequadas**

**Situação Anterior:** O sistema recusava responder perguntas legítimas sobre documentos:
```
❌ "Perdão, mas não podemos discutir como calcular a renda bruta mensal"
```

**Situação Atual:** O sistema fornece respostas completas e úteis:
```
✅ "Como você deseja saber como calcular a renda bruta mensal para verificar 
   se você se enquadra nas cotas de baixa renda, vou explicar passo a passo.
   
   Conforme o documento [Fonte: processed_document], para calcular a renda 
   bruta mensal, você precisa verificar se sua renda é igual ou inferior 
   ao salário mínimo per capita..."
```

### 🔧 **Implementações Técnicas**

#### **1. Sistema de Conhecimento Externo**
- **Arquivo:** `src/rag_app/external_knowledge.py` (NOVO)
- **Funcionalidade:** Complementa informações locais com Wikipedia e base conceitual
- **Ativação:** Automática quando chunks locais são insuficientes
- **Exemplo de uso:** Definição de "renda per capita" quando não explícita no documento

#### **2. Diretiva de Segurança Flexível**
- **Localização:** `SECURITY_DIRECTIVE` em `config.py`
- **Melhoria:** Permite explicações detalhadas mantendo proteção
- **Resultado:** Sistema responde perguntas sobre procedimentos documentados

#### **3. Sistema de Qualidade e Logging**
- **Funcionalidade:** Análise automática da relevância dos chunks
- **Avisos:** Alertas quando relevância está baixa (distância > 0.8)
- **Sugestões:** Orientações automáticas para reformular perguntas

#### **4. Fallback Estruturado**
- **Comportamento:** Respostas organizadas quando informações são parciais
- **Inclui:** Sugestões práticas e orientações para o usuário

### 📊 **Exemplos Práticos de Melhorias**

#### **Antes vs Depois:**

| Pergunta | Resposta Anterior (v2.1) | Resposta Atual (v2.2) |
|----------|-------------------------|----------------------|
| "Como calcular renda?" | ❌ Recusa responder | ✅ Explica passo a passo com base nos docs |
| "O que é renda per capita?" | ❌ Informação limitada | ✅ Definição completa + fonte do documento |
| "Quais documentos preciso?" | ✅ Lista documentos | ✅ Lista + explica como usar cada um |

#### **Logs de Qualidade:**
```
2025-09-30 11:40:43,394 - INFO - Recuperados 5 chunks via ChromaDB
2025-09-30 11:40:43,394 - INFO - Qualidade dos chunks: distância média=0.8842
2025-09-30 11:40:43,394 - WARNING - Chunks com baixa relevância (dist. média: 0.8842)
                                    - considere reformular a pergunta
```

#### **Conhecimento Externo Ativo:**
```
2025-09-30 13:28:29,280 - INFO - Pergunta conceitual detectada: o que significa
2025-09-30 13:28:29,281 - INFO - Adicionando conhecimento externo para query: 
                                  'O que significa renda bruta mensal per capita?...'
```

## 💡 Roadmap Futuro

### v2.3 (Em Planejamento)
- [ ] Suporte a mais formatos: DOCX, TXT, HTML, RTF
- [ ] Processamento de imagens em PDFs com OCR
- [ ] Suporte a tabelas complexas em Markdown
- [ ] Interface de configuração via web para formatos
- [ ] Expansão do sistema de conhecimento externo (mais APIs)
- [ ] Machine Learning para otimização automática de thresholds

### v2.4 (Planejado)
- [ ] Suporte a mais provedores LLM (Claude, OpenAI)
- [ ] Sistema de plugins para novos formatos
- [ ] Cache inteligente por tipo de documento
- [ ] API REST para integração externa
- [ ] Multi-tenancy e controle de acesso
- [ ] Deployment containerizado (Docker)

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commite suas mudanças (`git commit -m 'Add nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues:** Reporte bugs e solicite features via GitHub Issues
- **Documentação:** Consulte os arquivos `.md` na raiz do projeto
- **Configuração:** Verifique `DIRETIVA_SEGURANCA.md` para detalhes de segurança

## 📄 Licença

MIT License - A definir.  
