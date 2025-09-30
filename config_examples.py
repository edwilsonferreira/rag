# config_examples.py
# Exemplos de configuração para diferentes cenários

# ================================================================================
# EXEMPLO 1: Usando Google Gemini com variável de ambiente
# ================================================================================
"""
1. Configure a variável de ambiente:
   export GOOGLE_API_KEY="sua_chave_de_api_aqui"

2. No arquivo src/rag_app/config.py, configure:
   LLM_PROVIDER = "gemini"
   GOOGLE_API_KEY = ""  # Deixe vazio para usar variável de ambiente
   GEMINI_MODEL = "gemini-1.5-pro"

3. Instale a dependência:
   pip install google-generativeai
"""

# ================================================================================
# EXEMPLO 2: Usando Google Gemini com chave direta (NÃO recomendado para produção)
# ================================================================================
"""
No arquivo src/rag_app/config.py, configure:
LLM_PROVIDER = "gemini"
GOOGLE_API_KEY = "AIzaSy..."  # Sua chave de API diretamente
GEMINI_MODEL = "gemini-1.5-flash"  # Modelo mais rápido e barato
"""

# ================================================================================
# EXEMPLO 3: Usando Ollama local (configuração atual)
# ================================================================================
"""
No arquivo src/rag_app/config.py, configure:
LLM_PROVIDER = "ollama"
DEFAULT_OLLAMA_MODEL = "llama3:latest"
OLLAMA_HOST = "http://192.168.64.2:11434"  # ou "http://localhost:11434" para Ollama local
"""

# ================================================================================
# EXEMPLO 4: Alternando entre provedores facilmente
# ================================================================================
"""
Para alternar rapidamente entre provedores, você pode criar diferentes perfis:

# Perfil Desenvolvimento (Gemini)
LLM_PROVIDER = "gemini"
GEMINI_MODEL = "gemini-1.5-flash"  # Mais rápido para testes

# Perfil Produção (Ollama local)
LLM_PROVIDER = "ollama"
DEFAULT_OLLAMA_MODEL = "llama3:latest"
"""

# ================================================================================
# MODELOS DISPONÍVEIS
# ================================================================================

# Modelos Gemini disponíveis:
GEMINI_MODELS = [
    "gemini-1.5-pro",      # Mais avançado, melhor qualidade
    "gemini-1.5-flash",    # Mais rápido, mais barato
    "gemini-pro",          # Modelo anterior
]

# Modelos Ollama comuns:
OLLAMA_MODELS = [
    "llama3:latest",       # Llama 3 (8B parâmetros)
    "llama3:70b",         # Llama 3 (70B parâmetros) - Requer mais recursos
    "mistral:latest",      # Mistral AI
    "codellama:latest",    # Especializado em código
    "phi3:latest",         # Microsoft Phi-3
]

print("Consulte os exemplos acima para configurar seu provedor de LLM preferido!")