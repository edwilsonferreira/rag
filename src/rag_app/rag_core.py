# src/rag_app/rag_core.py

import os
from sentence_transformers import SentenceTransformer
import numpy as np
import ollama
import logging
from typing import List, Dict, Any
import json
import time

from . import config
import chromadb

# Importação do sistema de conhecimento externo
try:
    from .external_knowledge import ExternalKnowledgeProvider
    EXTERNAL_KNOWLEDGE_AVAILABLE = True
except ImportError:
    ExternalKnowledgeProvider = None
    EXTERNAL_KNOWLEDGE_AVAILABLE = False

# Importações condicionais para Gemini
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    GenerationConfig = None

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RAGCore:
    # ... (__init__ e todos os outros métodos que não _load_or_process_documents
    #      permanecem OS MESMOS da última versão completa que você tem) ...

    def __init__(self,
                 data_folder: str = config.DEFAULT_DATA_FOLDER,
                 model_name: str = config.DEFAULT_EMBEDDING_MODEL,
                 ollama_model: str = config.DEFAULT_OLLAMA_MODEL):
        self.data_folder = data_folder
        self.configured_ollama_model = ollama_model
        self.configured_embedding_model_name = model_name
        self.processed_pdf_files = []
        
        # Inicializa o provedor LLM baseado na configuração
        self._initialize_llm_provider()
        
        # Inicializa o sistema de conhecimento externo
        if config.ALLOW_EXTERNAL_KNOWLEDGE and EXTERNAL_KNOWLEDGE_AVAILABLE:
            self.external_provider = ExternalKnowledgeProvider()
            logger.info("Sistema de conhecimento externo inicializado")
        else:
            self.external_provider = None
            if config.ALLOW_EXTERNAL_KNOWLEDGE:
                logger.warning("Conhecimento externo habilitado mas módulo não disponível")
        
        logger.info(f"Usando modelo de embedding: {self.configured_embedding_model_name}")
        try:
            self.embedding_model_st = SentenceTransformer(self.configured_embedding_model_name)
            logger.info(f"Modelo SentenceTransformer '{self.configured_embedding_model_name}' carregado.")
        except Exception as e:
            logger.error(f"Erro crítico ao carregar o modelo SentenceTransformer '{self.configured_embedding_model_name}': {e}", exc_info=True)
            raise
        logger.info(f"Inicializando ChromaDB em: {config.CHROMA_DB_PATH} com coleção: {config.CHROMA_COLLECTION_NAME}")
        try:
            self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
            self.collection = self.chroma_client.get_or_create_collection(name=config.CHROMA_COLLECTION_NAME)
            logger.info(f"Conectado/Criado coleção ChromaDB: '{config.CHROMA_COLLECTION_NAME}'.")
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {e}", exc_info=True)
            raise
        self._ensure_data_folder()
        self._load_or_process_documents()

    def _initialize_llm_provider(self):
        """Inicializa o provedor LLM baseado na configuração."""
        if config.LLM_PROVIDER == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError(
                    "Google Generative AI não está instalado. "
                    "Execute: pip install google-generativeai"
                )
            
            # Configura a API do Google Gemini
            api_key = config.GOOGLE_API_KEY or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError(
                    "Chave da API do Google não encontrada. "
                    "Defina GOOGLE_API_KEY como variável de ambiente ou em config.py"
                )
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)
            logger.info(f"Google Gemini inicializado com modelo: {config.GEMINI_MODEL}")
            
        elif config.LLM_PROVIDER == "ollama":
            logger.info(f"Ollama configurado com modelo: {self.configured_ollama_model}")
            
        else:
            raise ValueError(f"Provedor LLM desconhecido: {config.LLM_PROVIDER}")
            
        self.llm_provider = config.LLM_PROVIDER

    def _ensure_data_folder(self):
        if not os.path.exists(self.data_folder):
            logger.warning(f"Pasta de dados '{self.data_folder}' não encontrada. Criando...")
            os.makedirs(self.data_folder)
            logger.info(f"Pasta '{self.data_folder}' criada.")

    def _load_processed_files_status(self) -> Dict[str, Dict[str, Any]]:
        try:
            if os.path.exists(config.PROCESSED_FILES_STATUS_JSON):
                with open(config.PROCESSED_FILES_STATUS_JSON, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Não foi possível carregar status: {e}. Reprocessando tudo.")
            return {}

    def _save_processed_files_status(self, status: Dict[str, Dict[str, Any]]):
        try:
            with open(config.PROCESSED_FILES_STATUS_JSON, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=4)
            logger.info(f"Status dos arquivos processados salvo.")
        except Exception as e:
            logger.error(f"Erro ao salvar status: {e}", exc_info=True)

    def _markdown_from_table(self, table_data: List[List[str]]) -> str:
        if not table_data: return ""
        header = [str(h).replace('\n', ' ').strip() if h is not None else '' for h in table_data[0]]
        align = [":---" for _ in header]
        rows = [[str(cell).replace('\n', ' ').strip() if cell is not None else '' for cell in row] for row in table_data]
        md_lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
        for row in rows[1:]:
            if len(row) != len(header): continue
            md_lines.append("| " + " | ".join(row) + " |")
        return "\n".join(md_lines)

    def _chunk_text(self, text: str, chunk_size: int = config.DEFAULT_CHUNK_SIZE, overlap: int = config.DEFAULT_CHUNK_OVERLAP) -> List[str]:
        words = text.split()
        if not words: return []
        chunks_list = []
        current_chunk_words = []
        current_length = 0
        approx_overlap_word_count = max(0, int(overlap / 6)) if overlap > 0 else 0
        idx = 0
        while idx < len(words):
            word = words[idx]
            word_len_to_add = len(word) + (1 if current_chunk_words else 0)
            if current_length + word_len_to_add > chunk_size and current_chunk_words:
                chunks_list.append(" ".join(current_chunk_words))
                if approx_overlap_word_count > 0:
                    overlap_start_index = max(0, len(current_chunk_words) - approx_overlap_word_count)
                    current_chunk_words = current_chunk_words[overlap_start_index:]
                else:
                    current_chunk_words = []
                current_length = len(" ".join(current_chunk_words)) if current_chunk_words else 0
            current_chunk_words.append(word)
            current_length += word_len_to_add
            idx += 1
        if current_chunk_words:
            chunks_list.append(" ".join(current_chunk_words))
        return [chunk for chunk in chunks_list if chunk.strip()]

    def _create_chunks(self, text, filename=None, page_numbers=None):
        """Cria chunks de texto e seus metadados"""
        chunks = self._chunk_text(text)
        chunks_with_metadata = []
        
        for i, chunk in enumerate(chunks):
            # Determinar página para este chunk (distribuição aproximada)
            chunk_page = "N/A"
            if page_numbers and len(page_numbers) > 0:
                # Distribuir chunks pelas páginas proporcionalmente
                chunk_position = i / len(chunks) if len(chunks) > 1 else 0
                page_index = min(int(chunk_position * len(page_numbers)), len(page_numbers) - 1)
                chunk_page = page_numbers[page_index]
            
            chunk_metadata = {
                "chunk_index": i,
                "chunk_length": len(chunk),
                "source": filename or "processed_document",
                "page_number": chunk_page
            }
            chunks_with_metadata.append({
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return chunks_with_metadata
    
    def _load_or_process_documents(self):
        """
        Processa PDFs, extraindo texto comum e tabelas separadamente,
        e os adiciona ao ChromaDB.
        """
        processed_status = self._load_processed_files_status()
        new_or_updated_processed_status = processed_status.copy()
        anything_processed_this_run = False
        files_in_db_this_session = set()

        # Suporte para múltiplos tipos de arquivo
        supported_extensions = [".pdf", ".md", ".markdown"]
        document_files_in_folder = [
            f for f in os.listdir(self.data_folder) 
            if any(f.lower().endswith(ext) for ext in supported_extensions)
        ]

        for document_file in document_files_in_folder:
            document_path = os.path.join(self.data_folder, document_file)
            try:
                file_mtime = os.path.getmtime(document_path)
                file_size = os.path.getsize(document_path)
            except FileNotFoundError: continue

            if document_file in processed_status and \
               processed_status[document_file].get('mtime') == file_mtime and \
               processed_status[document_file].get('size') == file_size:
                logger.debug(f"Arquivo '{document_file}' não modificado. Pulando.")
                files_in_db_this_session.add(document_file)
                continue
            
            logger.info(f"Arquivo '{document_file}' novo ou modificado. Reprocessando...")
            self.collection.delete(where={"source": document_file})

            anything_processed_this_run = True
            all_chunks_for_file = []

            try:
                # Processar baseado no tipo de arquivo
                if document_file.lower().endswith('.pdf'):
                    text, page_numbers = self._process_pdf_file(document_path)
                elif document_file.lower().endswith(('.md', '.markdown')):
                    text, page_numbers = self._process_markdown_file(document_path)
                else:
                    continue  # Pula arquivos não suportados
                
                
                # Processa o texto extraído em chunks
                if text.strip():
                    words = text.split()
                    if not words: 
                        continue
                    
                    all_chunks_for_file = self._create_chunks(text, filename=document_file, page_numbers=page_numbers)
                    logger.info(f"Processado arquivo {document_file}: {len(words)} palavras, {len(all_chunks_for_file)} chunks")
                else:
                    all_chunks_for_file = []
                    
                # Processar chunks e adicionar ao ChromaDB
                if all_chunks_for_file:
                    texts_to_embed = [item["text"] for item in all_chunks_for_file]
                    embeddings = self.embedding_model_st.encode(texts_to_embed, show_progress_bar=False)
                    
                    ids_to_add = [f"{document_file}_chunk_{i}" for i in range(len(all_chunks_for_file))]
                    metadatas_to_add = [item["metadata"] for item in all_chunks_for_file]

                    self.collection.add(
                        ids=ids_to_add,
                        embeddings=embeddings.tolist(),
                        documents=texts_to_embed,
                        metadatas=metadatas_to_add
                    )
                    logger.info(f"Adicionados/Atualizados {len(all_chunks_for_file)} chunks de '{document_file}' no ChromaDB.")
                    new_or_updated_processed_status[document_file] = {"mtime": file_mtime, "size": file_size}
                else:
                    logger.warning(f"Nenhum conteúdo extraído de '{document_file}'.")
                    if document_file in new_or_updated_processed_status:
                        del new_or_updated_processed_status[document_file]

            except Exception as e_doc:
                logger.error(f"Erro ao processar o documento '{document_path}': {e_doc}", exc_info=True)
            
            files_in_db_this_session.add(document_file)

        stale_files_in_status = [fname for fname in processed_status if fname not in document_files_in_folder]
        for fname in stale_files_in_status:
            logger.info(f"Removendo '{fname}' (não mais na pasta de dados) do status e do ChromaDB.")
            self.collection.delete(where={"source": fname})
            if fname in new_or_updated_processed_status:
                del new_or_updated_processed_status[fname]
            anything_processed_this_run = True 

        if anything_processed_this_run:
            self._save_processed_files_status(new_or_updated_processed_status)
        
        self.processed_pdf_files = sorted(list(files_in_db_this_session))
        logger.info(f"Carregamento concluído. {self.collection.count()} chunks no total em ChromaDB.")
    
    def _process_pdf_file(self, document_path):
        """Processa arquivo PDF específico"""
        import fitz
        
        text = ""
        page_numbers = []
        
        # Processa as páginas do PDF
        doc = fitz.open(document_path)
        try:
            for page_num_fitz, page in enumerate(doc):
                page_text = page.get_text()
                
                if page_text.strip():
                    text += f"[Página {page_num_fitz + 1}]\n{page_text}\n\n"
                    page_numbers.append(page_num_fitz + 1)
                    
                # Processa tabelas se houver
                tables = page.find_tables()
                if tables:
                    for table in tables:
                        table_text = self._extract_table_text(table)
                        if table_text:
                            text += f"[Tabela na Página {page_num_fitz + 1}]\n{table_text}\n\n"
        finally:
            doc.close()
        
        return text, page_numbers
    
    def _process_markdown_file(self, document_path):
        """Processa arquivo Markdown específico"""
        text = ""
        page_numbers = [1]  # Markdown é tratado como uma única "página"
        
        document_file = os.path.basename(document_path)
        
        try:
            with open(document_path, 'r', encoding='utf-8') as md_file:
                text = md_file.read()
                if text.strip():
                    text = f"[Arquivo Markdown: {document_file}]\n{text}\n\n"
        except UnicodeDecodeError:
            # Fallback para latin-1 se UTF-8 falhar
            with open(document_path, 'r', encoding='latin-1') as md_file:
                text = md_file.read()
                if text.strip():
                    text = f"[Arquivo Markdown: {document_file}]\n{text}\n\n"
        
        return text, page_numbers

    def _extract_table_text(self, table):
        """Extrai texto de uma tabela do PDF"""
        try:
            table_data = table.extract()
            if not table_data: 
                return ""
            
            header = table_data[0] if table_data else []
            text_parts = [" | ".join(str(cell) if cell else "" for cell in header)]
            
            for row in table_data[1:]:
                if len(row) != len(header): 
                    continue
                text_parts.append(" | ".join(str(cell) if cell else "" for cell in row))
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Erro ao processar tabela: {e}")
            return ""

    def retrieve_relevant_chunks(self, query: str, k: int = config.DEFAULT_RETRIEVAL_K) -> List[Dict[str, Any]]:
        """Recupera chunks relevantes do ChromaDB com logging detalhado."""
        if self.collection.count() == 0:
            logger.warning("ChromaDB está vazio - nenhum documento processado")
            return []
        try:
            logger.debug(f"Buscando chunks para query: '{query[:50]}...' (k={k})")
            query_embedding = self.embedding_model_st.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding, n_results=min(k, self.collection.count()), 
                include=["documents", "metadatas", "distances"] )
            retrieved_items = []
            if results['ids'] and results['ids'][0]: 
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                    retrieved_items.append({
                        "id": results['ids'][0][i], "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else None,
                        "distance": distance })
            
            # Log de qualidade dos resultados
            chunks_found = len(retrieved_items)
            logger.info(f"Recuperados {chunks_found} chunks via ChromaDB")
            
            if chunks_found > 0:
                avg_distance = sum(item['distance'] for item in retrieved_items) / chunks_found
                logger.info(f"Qualidade dos chunks: distância média={avg_distance:.4f}")
                
                if avg_distance > 0.8:  # Limiar alto indica baixa relevância
                    logger.warning(f"Chunks com baixa relevância (dist. média: {avg_distance:.4f}) - considere reformular a pergunta")
            
            return retrieved_items
        except Exception as e:
            logger.error(f"Erro ao buscar chunks no ChromaDB: {e}", exc_info=True)
            return []
        
    def answer_query(self, query: str) -> str:
        """Responde consulta usando documentos locais e opcionalmente conhecimento externo."""
        logger.info(f"Consulta recebida: '{query}'")
        retrieved_items = self.retrieve_relevant_chunks(query)
        
        if config.PRINT_DEBUG_CHUNKS:
            print("\n--- CHUNKS RECUPERADOS (DEBUG VIA CHROMA DB) ---")
            if retrieved_items:
                for i, item in enumerate(retrieved_items):
                    meta = item.get('metadata', {})
                    print(f"CHUNK {i+1} (Tipo: {meta.get('content_type', 'N/A')})")
                    print(f"  Fonte: {meta.get('source', 'N/A')}, Página: {meta.get('page_number', 'N/A')}")
                    print(f"  Distância: {item.get('distance', -1.0):.4f}")
                    if meta.get('content_type') == 'table':
                        print(f"  Conteúdo (Tabela Markdown):\n{item.get('document', '')}")
                    else:
                        print(f"  Texto: {item.get('document', '')[:300]}...")
                    print("--------------------")
            else:
                print("Nenhum chunk relevante encontrado para a consulta.")
            print("--- FIM DOS CHUNKS (DEBUG) ---\n")
        
        if self.collection.count() == 0 and not retrieved_items:
            return self._generate_fallback_response(query, "no_documents")
        
        # Gerar resposta base com documentos locais
        base_response = self.query_llm(query, retrieved_items)
        
        # Verificar se deve usar conhecimento externo para complementar
        if (self.external_provider and 
            config.ALLOW_EXTERNAL_KNOWLEDGE and 
            self.external_provider.should_use_external_knowledge(query, retrieved_items, [])):
            
            external_info = self.external_provider.get_external_knowledge(query)
            if external_info:
                logger.info(f"Adicionando conhecimento externo para query: '{query[:50]}...'")
                return self.external_provider.format_response_with_external(
                    base_response, external_info, query)
        
        return base_response

    def _generate_fallback_response(self, query: str, reason: str) -> str:
        """Gera resposta de fallback quando não há informação suficiente."""
        fallback_responses = {
            "no_documents": """
🚫 **Nenhum documento encontrado na base de conhecimento.**

**Sugestões:**
1. **Verifique se os documentos foram processados** - Execute o sistema novamente para reprocessar
2. **Adicione documentos relevantes** - Coloque arquivos PDF ou Markdown na pasta `data/`
3. **Reformule sua pergunta** - Use termos mais específicos ou diferentes palavras-chave

**Para suporte:** Consulte a documentação ou entre em contato com o administrador do sistema.
            """,
            
            "low_relevance": """
📋 **Informação limitada encontrada nos documentos.**

Com base nos documentos disponíveis, não foi possível encontrar informações específicas suficientes para responder sua pergunta adequadamente.

**Sugestões para melhorar a busca:**
1. **Reformule a pergunta** usando palavras-chave diferentes
2. **Seja mais específico** sobre o que você está procurando  
3. **Verifique a grafia** dos termos utilizados
4. **Consulte os documentos oficiais** diretamente para informações detalhadas

**Exemplo de reformulação:**
- Em vez de "como calcular", tente "cálculo de renda per capita"
- Em vez de "cotas", tente "critérios para cotas L2 L3 L4"
            """,
            
            "insufficient_context": """
🔍 **Contexto insuficiente nos documentos encontrados.**

Foram encontrados alguns trechos relacionados, mas não há informação suficiente para fornecer uma resposta completa e precisa.

**Recomendações:**
1. **Consulte os documentos oficiais** para informações completas
2. **Reformule a pergunta** com mais detalhes específicos
3. **Verifique se todos os documentos necessários** estão na base de dados
4. **Entre em contato com a fonte oficial** para esclarecimentos

⚠️ **Importante:** Sempre consulte as fontes oficiais para informações definitivas e atualizadas.
            """
        }
        
        base_response = fallback_responses.get(reason, fallback_responses["insufficient_context"])
        
        # Adicionar conhecimento externo se disponível e apropriado
        if (self.external_provider and 
            config.ALLOW_EXTERNAL_KNOWLEDGE and 
            reason in ["low_relevance", "insufficient_context"]):
            
            external_info = self.external_provider.get_external_knowledge(query)
            if external_info:
                base_response += f"\n\n{external_info}\n\n⚠️ **IMPORTANTE:** Esta informação complementar não substitui a consulta aos documentos oficiais."
        
        return base_response.strip()
        
    def _should_use_external_knowledge(self, query: str, context_items: List[Dict[str, Any]]) -> bool:
        """Determina se deve permitir uso de conhecimento externo baseado nas configurações."""
        
        # Se fontes externas estão desabilitadas globalmente
        if not config.ALLOW_EXTERNAL_KNOWLEDGE:
            return False
            
        # Se temos chunks suficientes com boa qualidade, usar apenas local
        if len(context_items) >= config.EXTERNAL_KNOWLEDGE_CONFIG["min_chunks_threshold"]:
            return False
            
        # Verificar se é uma pergunta conceitual
        query_lower = query.lower()
        is_conceptual = any(
            keyword in query_lower 
            for keyword in config.EXTERNAL_KNOWLEDGE_CONFIG["conceptual_keywords"]
        )
        
        # Verificar se menciona contextos específicos que impedem uso externo
        has_specific_context = any(
            keyword in query_lower 
            for keyword in config.EXTERNAL_KNOWLEDGE_CONFIG["specific_context_keywords"]
        )
        
        # Log da decisão se configurado
        if config.EXTERNAL_KNOWLEDGE_CONFIG.get("log_external_usage", False):
            decision_factors = {
                "chunks_count": len(context_items),
                "is_conceptual": is_conceptual,
                "has_specific_context": has_specific_context,
                "will_use_external": is_conceptual and not has_specific_context
            }
            logger.info(f"External knowledge decision for query '{query[:50]}...': {decision_factors}")
        
        # Permitir fontes externas apenas para perguntas conceituais SEM contexto específico
        return is_conceptual and not has_specific_context

    def query_llm(self, query: str, context_items: List[Dict[str, Any]]) -> str:
        """Envia consulta e contexto (com metadados) para o LLM."""
        
        # Verificar se deve permitir conhecimento externo
        allow_external = self._should_use_external_knowledge(query, context_items)
        
        # Construir diretivas baseadas na configuração
        directives = config.SECURITY_DIRECTIVE.strip()
        if allow_external:
            directives += f"\n\n{config.EXTERNAL_KNOWLEDGE_DIRECTIVE.strip()}"
        
        if not context_items:
            # Sem contexto local - resposta varia baseada na configuração
            if allow_external:
                prompt_message = (
                    f"{directives}\n\n"
                    f"Pergunta do Usuário: {query}\n\n"
                    f"Não encontrei informações específicas nos documentos fornecidos. "
                    f"Como esta parece ser uma pergunta conceitual, você pode usar conhecimento geral "
                    f"para fornecer uma resposta educativa, sempre indicando que informações específicas "
                    f"devem ser consultadas nos documentos oficiais.\n\n"
                    f"Assistente:"
                )
            else:
                prompt_message = (
                    f"{directives}\n\n"
                    f"Pergunta do Usuário: {query}\n\nAssistente: "
                    "Não encontrei informações específicas nos documentos fornecidos para responder a esta pergunta."
                )
        else:
            # Com contexto local
            context_parts = []
            for item in context_items:
                doc_text = item.get('document', '')
                meta = item.get('metadata', {})
                content_type = "Tabela" if meta.get('content_type') == 'table' else "Trecho de Texto"
                source_info = f"Fonte: {meta.get('source', 'Desconhecida')}, Página: {meta.get('page_number', 'N/A')}"
                context_parts.append(f"{source_info} ({content_type}):\n{doc_text}")
            
            context_str = "\n\n---\n\n".join(context_parts)
            
            citation_instruction = ""
            if config.ALWAYS_INCLUDE_PAGE_IN_ANSWER:
                citation_instruction = ("**Ao fornecer sua resposta, você DEVE citar explicitamente a fonte e página da informação usando o formato exato fornecido no contexto.** ")
            else:
                citation_instruction = ("Se possível, mencione a fonte e página da informação usando o formato fornecido no contexto. ")
            
            # Instrução adicional para fontes externas se permitido
            external_instruction = ""
            if allow_external:
                external_instruction = (
                    f"\n\n{config.EXTERNAL_KNOWLEDGE_CONFIG['external_disclaimer']}"
                )
            
            # --- CONSTRUÇÃO DO PROMPT COM SUPORTE A FONTES EXTERNAS ---
            prompt_message = (
                f"{directives}\n\n"
                f"Sua tarefa é ser um assistente factual e preciso. Responda à pergunta do usuário com base nos trechos e tabelas de documentos fornecidos no contexto.\n"
                f"**Regra Importante: Se a pergunta do usuário contiver uma premissa que é falsa ou não suportada pelo contexto, sua primeira prioridade é corrigir essa premissa de forma clara e direta.** "
                f"Por exemplo, se o usuário perguntar 'Quais os detalhes do curso de Medicina?' e o contexto não mencionar tal curso, você deve responder 'O documento não menciona um curso de Medicina. Os cursos mencionados são...'.\n"
                f"{citation_instruction}\n"
                f"Se a informação simplesmente não estiver nos trechos, indique que não foi encontrada.\n"
                f"Priorize sempre a veracidade baseada no contexto.{external_instruction}\n\n"
                f"Contexto dos Documentos:\n{context_str}\n\n"
                f"Pergunta do Usuário: {query}\n\n"
                f"Assistente:"
            )

        # Seleciona o provedor LLM baseado na configuração
        if self.llm_provider == "gemini":
            response = self._query_gemini(prompt_message)
        elif self.llm_provider == "ollama":
            response = self._query_ollama(prompt_message)
        else:
            return f"Erro: Provedor LLM desconhecido: {self.llm_provider}"
        
        # Adicionar indicador de fonte externa se foi utilizada
        return self._add_external_source_indicator(response, allow_external, context_items)

    def _add_external_source_indicator(self, response: str, allow_external: bool, context_items: List[Dict[str, Any]]) -> str:
        """Adiciona indicador visual quando fontes externas foram utilizadas na resposta."""
        
        # Se indicadores estão desabilitados, retorna resposta original
        if not config.EXTERNAL_KNOWLEDGE_CONFIG.get("show_external_indicator", True):
            return response
        
        # Se fontes externas não foram permitidas, retorna resposta original
        if not allow_external:
            return response
        
        # Se não foi usado conhecimento externo (temos contexto suficiente), retorna resposta original  
        if context_items and len(context_items) >= config.EXTERNAL_KNOWLEDGE_CONFIG["min_chunks_threshold"]:
            return response
            
        # Usar indicadores de conhecimento externo do config
        external_usage_indicators = config.EXTERNAL_KNOWLEDGE_CONFIG.get("external_usage_indicators", [])
        
        response_lower = response.lower()
        
        # Verificar se a resposta parece usar conhecimento externo
        uses_external = any(indicator in response_lower for indicator in external_usage_indicators)
        
        # Se detectou uso de conhecimento externo, adicionar indicador
        if uses_external:
            # Usar template configurável
            external_indicator = config.EXTERNAL_KNOWLEDGE_CONFIG.get(
                "external_indicator_template", 
                "\n\n🌐 **FONTE EXTERNA UTILIZADA**\nEsta resposta inclui conhecimento geral.\n---"
            )
            
            # Log da utilização de fonte externa
            if config.EXTERNAL_KNOWLEDGE_CONFIG.get("log_external_usage", False):
                logger.info(f"Resposta incluiu conhecimento externo para query com {len(context_items)} chunks")
            
            return response + external_indicator
        
        return response

    def _query_gemini(self, prompt_message: str) -> str:
        """Envia consulta para o Google Gemini."""
        logger.info(f"Enviando prompt para Google Gemini (modelo: {config.GEMINI_MODEL})...")
        try:
            response = self.gemini_model.generate_content(prompt_message)
            if response and response.text:
                return response.text.strip()
            else:
                logger.error(f"Resposta inesperada do Gemini: {response}")
                return "Erro: O Gemini retornou uma resposta em formato inesperado."
        except Exception as e:
            logger.error(f"Erro ao comunicar com Gemini: {e}", exc_info=True)
            return f"Erro ao comunicar com o Gemini: {e}"

    def _query_ollama(self, prompt_message: str) -> str:
        """Envia consulta para o Ollama local."""
        logger.info(f"Enviando prompt para Ollama (modelo: {self.configured_ollama_model})...")
        try:
            # Cria cliente Ollama com host personalizado
            client = ollama.Client(host=config.OLLAMA_HOST)
            response = client.chat(model=self.configured_ollama_model, messages=[{'role': 'user', 'content': prompt_message}])
            if response and 'message' in response and 'content' in response['message']:
                return response['message']['content'].strip()
            else:
                logger.error(f"Resposta inesperada do Ollama: {response}")
                return "Erro: O Ollama retornou uma resposta em formato inesperado."
        except Exception as e:
            logger.error(f"Erro ao comunicar com Ollama: {e}", exc_info=True)
            return f"Erro ao comunicar com o Ollama: {e}"

# O bloco if __name__ == '__main__' foi removido.
