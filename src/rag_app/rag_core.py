# src/rag_app/rag_core.py

import os
import fitz
from sentence_transformers import SentenceTransformer
import numpy as np
import ollama
import logging
from typing import List, Dict, Any
import json
import time

from . import config
import chromadb

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
    
    def _load_or_process_documents(self):
        """
        Processa PDFs, extraindo texto comum e tabelas separadamente,
        e os adiciona ao ChromaDB.
        """
        processed_status = self._load_processed_files_status()
        new_or_updated_processed_status = processed_status.copy()
        anything_processed_this_run = False
        files_in_db_this_session = set()

        pdf_files_in_folder = [f for f in os.listdir(self.data_folder) if f.lower().endswith(".pdf")]

        for pdf_file in pdf_files_in_folder:
            pdf_path = os.path.join(self.data_folder, pdf_file)
            try:
                file_mtime = os.path.getmtime(pdf_path)
                file_size = os.path.getsize(pdf_path)
            except FileNotFoundError: continue

            if pdf_file in processed_status and \
               processed_status[pdf_file].get('mtime') == file_mtime and \
               processed_status[pdf_file].get('size') == file_size:
                logger.debug(f"Arquivo '{pdf_file}' não modificado. Pulando.")
                files_in_db_this_session.add(pdf_file)
                continue
            
            logger.info(f"Arquivo '{pdf_file}' novo ou modificado. Reprocessando...")
            self.collection.delete(where={"source": pdf_file})

            anything_processed_this_run = True
            all_chunks_for_file = []

            try:
                doc = fitz.open(pdf_path)
                total_tables_in_file = 0 # << INICIA O CONTADOR DE TABELAS PARA O ARQUIVO

                for page_num_fitz, page in enumerate(doc):
                    page_number_display = page_num_fitz + 1
                    
                    # 1. Encontra tabelas e CONVERTE para uma lista
                    tables_list = list(page.find_tables())
                    
                    # --- INÍCIO DA MUDANÇA NO LOG ---
                    # Só registra o número de tabelas se for maior que zero,
                    # e em nível DEBUG para não poluir o console.
                    if len(tables_list) > 0:
                        total_tables_in_file += len(tables_list)
                        logger.debug(f"Arquivo '{pdf_file}', Página {page_number_display}: {len(tables_list)} tabelas encontradas.")
                    # --- FIM DA MUDANÇA NO LOG ---

                    # Processa cada tabela da lista
                    for table_idx, table in enumerate(tables_list):
                        table_data = table.extract()
                        if not table_data: continue
                        
                        markdown_table = self._markdown_from_table(table_data)
                        if markdown_table:
                            all_chunks_for_file.append({
                                "text": markdown_table,
                                "metadata": {"source": pdf_file, "page_number": page_number_display, "content_type": "table"}
                            })

                    # 2. Extrai texto comum, ignorando as áreas das tabelas
                    all_table_bboxes = [fitz.Rect(t.bbox) for t in tables_list]
                    text_blocks = page.get_text("blocks")
                    prose_text = ""
                    for block in text_blocks:
                        x0, y0, x1, y1, text_content, _, _ = block
                        block_rect = fitz.Rect(x0, y0, x1, y1)
                        is_part_of_table = any(table_bbox.intersects(block_rect) for table_bbox in all_table_bboxes)
                        if not is_part_of_table:
                            prose_text += text_content.strip() + "\n"
                    
                    if prose_text.strip():
                        normal_chunks = self._chunk_text(prose_text)
                        for chunk_text in normal_chunks:
                            all_chunks_for_file.append({
                                "text": chunk_text,
                                "metadata": {"source": pdf_file, "page_number": page_number_display, "content_type": "text"}
                            })
                
                # NOVO LOG DE SUMÁRIO DO ARQUIVO
                logger.info(f"Arquivo '{pdf_file}' escaneado: {total_tables_in_file} tabelas encontradas em {doc.page_count} páginas.")
                doc.close()

                # 3. Gera embeddings e adiciona ao ChromaDB para todo o arquivo
                if all_chunks_for_file:
                    texts_to_embed = [item["text"] for item in all_chunks_for_file]
                    embeddings = self.embedding_model_st.encode(texts_to_embed, show_progress_bar=False)
                    
                    ids_to_add = [f"{pdf_file}_chunk_{i}" for i in range(len(all_chunks_for_file))]
                    metadatas_to_add = [item["metadata"] for item in all_chunks_for_file]

                    self.collection.add(
                        ids=ids_to_add,
                        embeddings=embeddings.tolist(),
                        documents=texts_to_embed,
                        metadatas=metadatas_to_add
                    )
                    logger.info(f"Adicionados/Atualizados {len(all_chunks_for_file)} chunks (texto e tabelas) de '{pdf_file}' no ChromaDB.")
                    new_or_updated_processed_status[pdf_file] = {'mtime': file_mtime, 'size': file_size}
                else:
                    logger.warning(f"Nenhum conteúdo (texto ou tabela) extraído de '{pdf_file}'.")
                    if pdf_file in new_or_updated_processed_status:
                        del new_or_updated_processed_status[pdf_file]

            except Exception as e_doc:
                logger.error(f"Erro ao processar o documento '{pdf_path}': {e_doc}", exc_info=True)
            
            files_in_db_this_session.add(pdf_file)

        stale_files_in_status = [fname for fname in processed_status if fname not in pdf_files_in_folder]
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
        
    def retrieve_relevant_chunks(self, query: str, k: int = config.DEFAULT_RETRIEVAL_K) -> List[Dict[str, Any]]:
        # ... (método permanece o mesmo da versão anterior) ...
        if self.collection.count() == 0: return []
        try:
            query_embedding = self.embedding_model_st.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding, n_results=min(k, self.collection.count()), 
                include=["documents", "metadatas", "distances"] )
            retrieved_items = []
            if results['ids'] and results['ids'][0]: 
                for i in range(len(results['ids'][0])):
                    retrieved_items.append({
                        "id": results['ids'][0][i], "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else None,
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else None })
            logger.info(f"Recuperados {len(retrieved_items)} chunks via ChromaDB.")
            return retrieved_items
        except Exception as e:
            logger.error(f"Erro ao buscar chunks no ChromaDB: {e}", exc_info=True)
            return []
        
    def answer_query(self, query: str) -> str:
        # ... (método permanece o mesmo da versão anterior) ...
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
             return "Nenhum documento no banco de dados ou nenhum chunk relevante encontrado."
        return self.query_llm(query, retrieved_items)
        
    def query_llm(self, query: str, context_items: List[Dict[str, Any]]) -> str:
        """Envia consulta e contexto (com metadados) para o LLM via Ollama."""
        
        if not context_items:
            prompt_message = (f"Pergunta do Usuário: {query}\n\nAssistente: "
                              "Não encontrei informações específicas nos documentos fornecidos para responder a esta pergunta.")
        else:
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
                citation_instruction = ("**Ao fornecer sua resposta, você DEVE citar explicitamente a fonte e página da informação (ex: 'Conforme Documento X, Página Y...').** ")
            else:
                citation_instruction = ("Se possível, mencione a fonte e página da informação. ")
            
            # --- INÍCIO DA MUDANÇA NO PROMPT ---
            # Adicionamos uma instrução explícita para corrigir premissas falsas.
            prompt_message = (
                f"Sua tarefa é ser um assistente factual e preciso. Responda à pergunta do usuário estritamente com base nos trechos e tabelas de documentos fornecidos no contexto.\n"
                f"**Regra Importante: Se a pergunta do usuário contiver uma premissa que é falsa ou não suportada pelo contexto, sua primeira prioridade é corrigir essa premissa de forma clara e direta.** "
                f"Por exemplo, se o usuário perguntar 'Quais os detalhes do curso de Medicina?' e o contexto não mencionar tal curso, você deve responder 'O documento não menciona um curso de Medicina. Os cursos mencionados são...'.\n"
                f"{citation_instruction}\n"
                f"Se a informação simplesmente não estiver nos trechos, indique que não foi encontrada.\n"
                f"Priorize sempre a veracidade baseada no contexto.\n\n"
                f"Contexto dos Documentos:\n{context_str}\n\n"
                f"Pergunta do Usuário: {query}\n\n"
                f"Assistente:"
            )
            # --- FIM DA MUDANÇA NO PROMPT ---

        logger.info(f"Enviando prompt para Ollama (modelo: {self.configured_ollama_model})...")
        try:
            response = ollama.chat(model=self.configured_ollama_model, messages=[{'role': 'user', 'content': prompt_message}])
            if response and 'message' in response and 'content' in response['message']:
                return response['message']['content'].strip()
            else:
                logger.error(f"Resposta inesperada do Ollama: {response}")
                return "Erro: O LLM retornou uma resposta em formato inesperado."
        except Exception as e:
            logger.error(f"Erro ao comunicar com Ollama: {e}", exc_info=True)
            return f"Erro ao comunicar com o LLM: {e}"

# O bloco if __name__ == '__main__' foi removido.
