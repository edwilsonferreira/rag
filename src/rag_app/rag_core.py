# src/rag_app/rag_core.py

import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
import ollama
import logging
from typing import List, Dict, Any
import json
import time
# Removido: from datetime import datetime (não mais usado na classe após remover __main__)

# Importa as configurações usando importação relativa
from . import config

import chromadb

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RAGCore:
    def __init__(self,
                 data_folder: str = config.DEFAULT_DATA_FOLDER,
                 model_name: str = config.DEFAULT_EMBEDDING_MODEL,
                 ollama_model: str = config.DEFAULT_OLLAMA_MODEL):
        self.data_folder = data_folder
        self.configured_ollama_model = ollama_model
        self.configured_embedding_model_name = model_name
        
        self.text_chunks_corpus = [] 
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
            logger.warning(f"Não foi possível carregar o status dos arquivos processados ('{config.PROCESSED_FILES_STATUS_JSON}'): {e}. Tratando como novo processamento.")
            return {}

    def _save_processed_files_status(self, status: Dict[str, Dict[str, Any]]):
        try:
            with open(config.PROCESSED_FILES_STATUS_JSON, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=4)
            logger.info(f"Status dos arquivos processados salvo em '{config.PROCESSED_FILES_STATUS_JSON}'.")
        except Exception as e:
            logger.error(f"Erro ao salvar o status dos arquivos processados: {e}", exc_info=True)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(pdf_path)
            text = "".join(page.get_text("text") for page in doc)
            doc.close()
            return text.strip() 
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF '{pdf_path}' com PyMuPDF: {e}", exc_info=True)
            return ""

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
        processed_status = self._load_processed_files_status()
        new_or_updated_processed_status = processed_status.copy()
        anything_processed_this_run = False
        files_in_db_this_session = set()
        pdf_files_in_folder = [f for f in os.listdir(self.data_folder) if f.lower().endswith(".pdf")]
        if not pdf_files_in_folder:
            logger.info(f"Nenhum arquivo PDF encontrado em '{self.data_folder}'. Verificando conteúdo existente no ChromaDB.")
        for pdf_file in pdf_files_in_folder:
            pdf_path = os.path.join(self.data_folder, pdf_file)
            try:
                file_mtime = os.path.getmtime(pdf_path)
                file_size = os.path.getsize(pdf_path)
            except FileNotFoundError:
                logger.warning(f"Arquivo '{pdf_file}' não encontrado em '{pdf_path}' durante o processamento. Pulando.")
                continue
            needs_reprocessing = True
            if pdf_file in processed_status:
                status_entry = processed_status[pdf_file]
                if status_entry.get('mtime') == file_mtime and status_entry.get('size') == file_size:
                    needs_reprocessing = False
                    files_in_db_this_session.add(pdf_file) 
                else:
                    logger.info(f"Arquivo '{pdf_file}' modificado. Reprocessando e atualizando no ChromaDB...")
                    self.collection.delete(where={"source": pdf_file})
                    logger.info(f"Chunks antigos de '{pdf_file}' removidos do ChromaDB.")
            else:
                logger.info(f"Novo arquivo: '{pdf_file}'. Processando...")
            if needs_reprocessing:
                anything_processed_this_run = True
                logger.info(f"Processando e indexando arquivo: {pdf_path}")
                current_file_chunks_for_db = []
                current_file_embeddings_for_db = []
                current_file_metadatas_for_db = []
                current_file_chunk_ids_for_db = []
                total_chunks_for_file_in_db = 0
                try:
                    doc = fitz.open(pdf_path)
                    for page_num_fitz, page in enumerate(doc):
                        page_number_display = page_num_fitz + 1 
                        page_text = page.get_text("text").strip()
                        if not page_text:
                            logger.debug(f"Página {page_number_display} de '{pdf_file}' não contém texto extraível.")
                            continue
                        page_chunks = self._chunk_text(page_text)
                        if not page_chunks:
                            logger.debug(f"Nenhum chunk gerado para a página {page_number_display} de '{pdf_file}'.")
                            continue
                        page_embeddings = self.embedding_model_st.encode(page_chunks, show_progress_bar=False)
                        for chunk_idx_on_page, chunk_text in enumerate(page_chunks):
                            chunk_id = f"{pdf_file}_page_{page_number_display}_chunk_{chunk_idx_on_page}"
                            current_file_chunk_ids_for_db.append(chunk_id)
                            current_file_chunks_for_db.append(chunk_text)
                            current_file_embeddings_for_db.append(page_embeddings[chunk_idx_on_page].tolist())
                            current_file_metadatas_for_db.append({
                                "source": pdf_file, "page_number": page_number_display,
                                "chunk_on_page_index": chunk_idx_on_page,
                                "text_preview": chunk_text[:100]+"..."})
                            total_chunks_for_file_in_db +=1
                    doc.close()
                    if current_file_chunk_ids_for_db:
                        self.collection.add(ids=current_file_chunk_ids_for_db, embeddings=current_file_embeddings_for_db,
                                            documents=current_file_chunks_for_db, metadatas=current_file_metadatas_for_db)
                        logger.info(f"{total_chunks_for_file_in_db} chunks de '{pdf_file}' adicionados/atualizados no ChromaDB.")
                        new_or_updated_processed_status[pdf_file] = {
                            'mtime': file_mtime, 'size': file_size, 'chunk_count': total_chunks_for_file_in_db}
                        files_in_db_this_session.add(pdf_file)
                    else:
                        logger.warning(f"Nenhum chunk processável encontrado em '{pdf_file}'.")
                        if pdf_file in new_or_updated_processed_status: del new_or_updated_processed_status[pdf_file]
                except Exception as e_doc:
                    logger.error(f"Erro ao processar o documento '{pdf_path}': {e_doc}", exc_info=True)
                    if pdf_file in new_or_updated_processed_status: del new_or_updated_processed_status[pdf_file]
            else: 
                logger.debug(f"Arquivo '{pdf_file}' já estava processado e atualizado no BD (conforme status).")
                files_in_db_this_session.add(pdf_file) # Adiciona aqui pois não passou pelo `needs_reprocessing`
        stale_files_in_status = [fname for fname in new_or_updated_processed_status if fname not in pdf_files_in_folder]
        for fname in stale_files_in_status:
            logger.info(f"Removendo '{fname}' do status e do ChromaDB (arquivo não encontrado na pasta de dados).")
            self.collection.delete(where={"source": fname})
            del new_or_updated_processed_status[fname]
            anything_processed_this_run = True 
        if anything_processed_this_run:
            self._save_processed_files_status(new_or_updated_processed_status)
        self.processed_pdf_files = sorted(list(files_in_db_this_session))
        db_count = self.collection.count()
        if db_count > 0: logger.info(f"Carregamento concluído. Total de {db_count} chunks no ChromaDB de {len(self.processed_pdf_files)} fontes PDF ativas.")
        elif pdf_files_in_folder: logger.warning("Nenhum chunk no ChromaDB após o processamento, apesar de existirem PDFs. Verifique logs.")
        else: logger.info("Nenhum PDF na pasta de dados e nenhum chunk no ChromaDB.")

    def retrieve_relevant_chunks(self, query: str, k: int = config.DEFAULT_RETRIEVAL_K) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            logger.warning("ChromaDB está vazio.")
            return []
        try:
            query_embedding = self.embedding_model_st.encode([query]).tolist()
            results = self.collection.query(query_embeddings=query_embedding, n_results=min(k, self.collection.count()), include=["documents", "metadatas", "distances"])
            retrieved_items = []
            if results['ids'] and results['ids'][0]: 
                for i in range(len(results['ids'][0])):
                    retrieved_items.append({
                        "id": results['ids'][0][i], "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else None,
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else None })
            logger.info(f"Recuperados {len(retrieved_items)} chunks (com metadatos) via ChromaDB.")
            return retrieved_items
        except Exception as e:
            logger.error(f"Erro ao buscar chunks no ChromaDB: {e}", exc_info=True)
            return []

    def answer_query(self, query: str) -> str:
        logger.info(f"Consulta recebida: '{query}'")
        retrieved_items = self.retrieve_relevant_chunks(query)
        if config.PRINT_DEBUG_CHUNKS:
            print("\n--- CHUNKS RECUPERADOS (DEBUG VIA CHROMA DB) ---")
            if retrieved_items:
                for i, item in enumerate(retrieved_items):
                    print(f"CHUNK {i+1} (ID: {item.get('id', 'N/A')})")
                    print(f"  Fonte: {item.get('metadata', {}).get('source', 'N/A')}, Página: {item.get('metadata', {}).get('page_number', 'N/A')}")
                    print(f"  Distância: {item.get('distance', -1.0):.4f}")
                    print(f"  Texto: {item.get('document', '')[:200]}...")
                    print("--------------------")
            else:
                print("Nenhum chunk relevante encontrado para a consulta.")
            print("--- FIM DOS CHUNKS (DEBUG) ---\n")
        if self.collection.count() == 0 and not retrieved_items:
             return "Nenhum documento no banco de dados ou nenhum chunk relevante encontrado."
        return self.query_llm(query, retrieved_items)

    def query_llm(self, query: str, context_items: List[Dict[str, Any]]) -> str:
        if not context_items:
            prompt_message = (f"Pergunta do Usuário: {query}\n\nAssistente: "
                              "Não encontrei informações específicas nos documentos fornecidos para responder a esta pergunta.")
        else:
            context_parts = []
            for item in context_items:
                doc_text = item.get('document', '')
                meta = item.get('metadata', {})
                source_info = f"Fonte: {meta.get('source', 'Desconhecida')}, Página: {meta.get('page_number', 'N/A')}"
                context_parts.append(f"{source_info}\nTrecho do Documento:\n{doc_text}")
            context_str = "\n\n---\n\n".join(context_parts)
            citation_instruction = ""
            if config.ALWAYS_INCLUDE_PAGE_IN_ANSWER:
                citation_instruction = (
                    f"**Ao fornecer sua resposta, você DEVE citar explicitamente o nome do arquivo (Fonte) e o número da página de onde a informação principal foi retirada (ex: 'Esta informação pode ser encontrada em Documento X, Página Y.').** "
                    f"Se a informação for sintetizada de múltiplas fontes, cite as principais. ")
            else:
                citation_instruction = (
                    f"Se possível, ao fornecer informações específicas, mencione o nome do arquivo (Fonte) e o número da página de onde a informação foi retirada. ")
            prompt_message = (
                f"Com base nos seguintes trechos de documentos (cada um com sua fonte e página indicadas), responda à pergunta do usuário de forma concisa e informativa.\n"
                f"{citation_instruction}\n"
                f"Se a informação não estiver nos trechos fornecidos, indique claramente que não foi encontrada nos documentos.\n"
                f"Priorize informações diretamente contidas nos trechos.\n\n"
                f"Contexto dos Documentos:\n{context_str}\n\n"
                f"Pergunta do Usuário: {query}\n\nAssistente:")
        logger.info(f"Enviando prompt para Ollama (modelo: {self.configured_ollama_model})...")
        try:
            response = ollama.chat(model=self.configured_ollama_model, messages=[{'role': 'user', 'content': prompt_message}])
            if response and 'message' in response and 'content' in response['message']:
                return response['message']['content'].strip()
            else:
                logger.error(f"Resposta inesperada do Ollama: {response}")
                return "Erro: LLM retornou resposta em formato inesperado."
        except Exception as e:
            logger.error(f"Erro ao comunicar com Ollama: {e}", exc_info=True)
            return f"Erro ao comunicar com o LLM: {e}"

# O bloco if __name__ == '__main__' foi removido para simplificar o arquivo
# e torná-lo puramente um módulo de classe.
# Os testes interativos agora são responsabilidade primária do rag_terminal.py
# ou de scripts de teste dedicados.