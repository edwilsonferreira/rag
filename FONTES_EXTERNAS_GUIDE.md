# Teste da Funcionalidade de Fontes Externas

## Como Usar a Nova Configuração

### 1. **Configuração no arquivo `config.py`**

```python
# --- Configurações de Fontes Externas ---
# Controla se o LLM pode consultar conhecimento externo além dos documentos fornecidos
ALLOW_EXTERNAL_KNOWLEDGE: bool = False  # True para ativar, False para desativar
```

### 2. **Estados de Funcionamento**

#### 🔒 **ALLOW_EXTERNAL_KNOWLEDGE = False (Padrão/Seguro)**
- LLM responde **APENAS** baseado nos documentos fornecidos
- Para perguntas sem contexto suficiente: "Não encontrei informações específicas nos documentos"
- **Máxima segurança** e confiabilidade
- **Recomendado para ambiente de produção**

#### 🔓 **ALLOW_EXTERNAL_KNOWLEDGE = True (Expandido)**
- LLM pode usar conhecimento geral **complementar**
- Apenas para perguntas conceituais ("o que significa", "o que é", etc.)
- **Nunca** para perguntas específicas do contexto (IFMT, edital, datas)
- Respostas incluem disclaimers automáticos sobre consultar fontes oficiais

### 3. **Exemplos Práticos**

#### Pergunta: "O que significa ter cursado integralmente o ensino fundamental em escola pública?"

**Com ALLOW_EXTERNAL_KNOWLEDGE = False:**
```
Não encontrei informações específicas nos documentos fornecidos para responder a esta pergunta.
```

**Com ALLOW_EXTERNAL_KNOWLEDGE = True:**
```
📋 **Baseado nos documentos fornecidos:** [informações específicas do edital, se houver]

💡 **Contexto geral:** "Cursar integralmente o ensino fundamental em escola pública" significa ter estudado todos os anos do ensino fundamental (do 1º ao 9º ano) exclusivamente em instituições públicas de ensino, sem ter frequentado escola particular durante nenhum período deste ciclo educacional.

⚠️ **IMPORTANTE:** Esta resposta inclui conhecimento geral complementar. 
Sempre consulte os documentos oficiais para informações específicas e atualizadas.
```

### 4. **Critérios de Segurança Implementados**

#### ✅ **Permitido usar fontes externas quando:**
- Query contém palavras conceituais: "o que é", "o que significa", "defina"
- Poucos chunks encontrados (< 2 chunks)
- **NÃO** menciona contextos específicos

#### ❌ **NUNCA usar fontes externas quando:**
- Query menciona: "IFMT", "edital", "este documento", "prazo", "data"
- Chunks suficientes encontrados (≥ 2 chunks)
- ALLOW_EXTERNAL_KNOWLEDGE = False

### 5. **Configurações Avançadas**

```python
EXTERNAL_KNOWLEDGE_CONFIG = {
    # Critérios para considerar uso de fontes externas
    "min_chunks_threshold": 2,          # Mínimo de chunks locais para NÃO usar externo
    "confidence_threshold": 0.3,        # Score mínimo para considerar chunks locais
    
    # Tipos de perguntas que podem usar fontes externas
    "conceptual_keywords": [
        "o que é", "o que significa", "defina", "conceito de", 
        "significado de", "definição de", "explique"
    ],
    
    # Palavras-chave que IMPEDEM uso de fontes externas
    "specific_context_keywords": [
        "ifmt", "edital", "este documento", "neste caso", "nesta situação",
        "conforme", "segundo o", "de acordo com", "prazo", "data", "cronograma"
    ],
    
    # Configurações de debug
    "log_external_usage": True,         # Log quando usar fontes externas
    "show_source_indicators": True      # Mostrar indicadores de fonte na resposta
}
```

### 6. **Comandos para Teste**

#### Testar com fontes externas DESABILITADAS (seguro):
```bash
# 1. Verificar configuração atual
python -c "from src.rag_app.config import ALLOW_EXTERNAL_KNOWLEDGE; print(f'Fontes externas: {ALLOW_EXTERNAL_KNOWLEDGE}')"

# 2. Testar pergunta conceitual
echo "O que significa ter cursado integralmente o ensino fundamental em escola pública?" | python -m src.rag_app.rag_terminal
```

#### Testar com fontes externas HABILITADAS (expandido):
```bash
# 1. Modificar config.py: ALLOW_EXTERNAL_KNOWLEDGE = True
# 2. Testar mesma pergunta conceitual
echo "O que significa ter cursado integralmente o ensino fundamental em escola pública?" | python -m src.rag_app.rag_terminal
```

### 7. **Logs de Debug**

Com `"log_external_usage": True`, o sistema registra as decisões:

```
INFO - External knowledge decision for query 'O que significa ter cursado integralmente...': {
  'chunks_count': 1, 
  'is_conceptual': True, 
  'has_specific_context': False, 
  'will_use_external': True
}
```

### 8. **Recomendações de Uso**

#### 🏢 **Ambiente de Produção/Institucional:**
- `ALLOW_EXTERNAL_KNOWLEDGE = False`
- Máxima confiabilidade
- Apenas documentos oficiais

#### 🧪 **Ambiente de Desenvolvimento/Teste:**
- `ALLOW_EXTERNAL_KNOWLEDGE = True`
- Melhor experiência do usuário
- Respostas mais educativas com disclaimers

#### ⚖️ **Ambiente Híbrido:**
- Configuração dinâmica baseada no tipo de usuário
- Administradores: fontes externas habilitadas
- Usuários finais: fontes externas desabilitadas

## ✅ Implementação Concluída

A funcionalidade está **totalmente implementada** e **pronta para uso**, com:

- ✅ Configuração centralizada em `config.py`
- ✅ Lógica de decisão inteligente
- ✅ Disclaimers automáticos
- ✅ Logs de debug
- ✅ Múltiplos critérios de segurança
- ✅ Compatibilidade com ambos LLMs (Gemini + Ollama)