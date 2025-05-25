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

# Importa as configurações usando importação relativa
from . import config # Correto para estrutura de pacote

import chromadb

logger = logging.getLogger(__name__)
# Configura o logging uma vez, idealmente no ponto de entrada da aplicação,
# mas para execução direta do módulo, podemos fazer aqui com uma verificação.
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

        # Chamada para o método que estava faltando/causando erro
        self._ensure_data_folder() # << ESTA LINHA CHAMA O MÉTODO ABAIXO
        self._load_or_process_documents()

    # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
    # CERTIFIQUE-SE DE QUE ESTE MÉTODO ESTÁ DEFINIDO DENTRO DA CLASSE RAGCore
    # COM A INDENTAÇÃO CORRETA
    # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
    def _ensure_data_folder(self):
        """Garante que a pasta de dados (definida em config.py e passada ao __init__) exista."""
        if not os.path.exists(self.data_folder):
            logger.warning(f"Pasta de dados '{self.data_folder}' não encontrada. Criando...")
            os.makedirs(self.data_folder)
            logger.info(f"Pasta '{self.data_folder}' criada.")
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # FIM DA DEFINIÇÃO DO MÉTODO _ensure_data_folder
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF '{pdf_path}': {e}", exc_info=True)
            return ""

    def _chunk_text(self, text: str, chunk_size: int = config.DEFAULT_CHUNK_SIZE, overlap: int = config.DEFAULT_CHUNK_OVERLAP) -> List[str]:
        words = text.split()
        if not words:
            return []

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

        # self.data_folder é definido no __init__ usando config.DEFAULT_DATA_FOLDER
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

            needs_processing = True
            if pdf_file in processed_status:
                status_entry = processed_status[pdf_file]
                if status_entry.get('mtime') == file_mtime and status_entry.get('size') == file_size:
                    needs_processing = False
                    files_in_db_this_session.add(pdf_file) 
                else:
                    logger.info(f"Arquivo '{pdf_file}' modificado. Reprocessando...")
                    self.collection.delete(where={"source": pdf_file})
                    logger.info(f"Chunks antigos de '{pdf_file}' removidos do ChromaDB.")
            else:
                logger.info(f"Novo arquivo: '{pdf_file}'. Processando...")

            if needs_processing:
                anything_processed_this_run = True
                logger.info(f"Processando e indexando: {pdf_path}")
                text = self._extract_text_from_pdf(pdf_path)

                if not text.strip():
                    logger.warning(f"Nenhum texto útil extraído de '{pdf_file}'.")
                    if pdf_file in new_or_updated_processed_status:
                        del new_or_updated_processed_status[pdf_file]
                    continue

                chunks = self._chunk_text(text)
                if not chunks:
                    logger.warning(f"Nenhum chunk gerado para '{pdf_file}'. Verifique o conteúdo e o chunk_size.")
                    if pdf_file in new_or_updated_processed_status:
                        del new_or_updated_processed_status[pdf_file]
                    continue

                logger.info(f"Gerando embeddings para {len(chunks)} chunks de '{pdf_file}'.")
                try:
                    embeddings = self.embedding_model_st.encode(chunks, show_progress_bar=False)
                    chunk_ids = [f"{pdf_file}_chunk_{i}" for i in range(len(chunks))]
                    # Adicionando mais metadados, como o preview do texto original do chunk
                    metadatas = [{"source": pdf_file, "chunk_index": i, "text_preview": chunk[:100]+"..."} for i, chunk in enumerate(chunks)] 

                    self.collection.add(
                        ids=chunk_ids,
                        embeddings=embeddings.tolist(),
                        documents=chunks,
                        metadatas=metadatas
                    )
                    logger.info(f"{len(chunks)} chunks de '{pdf_file}' adicionados/atualizados no ChromaDB.")
                    new_or_updated_processed_status[pdf_file] = {
                        'mtime': file_mtime, 'size': file_size, 'chunk_count': len(chunks)
                    }
                    files_in_db_this_session.add(pdf_file)
                except Exception as e:
                    logger.error(f"Erro ao processar/adicionar chunks de '{pdf_file}' ao ChromaDB: {e}", exc_info=True)
            else:
                logger.debug(f"Arquivo '{pdf_file}' já estava processado e atualizado no BD (conforme status).")
                files_in_db_this_session.add(pdf_file)

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
        if db_count > 0:
            logger.info(f"Carregamento concluído. Total de {db_count} chunks no ChromaDB de {len(self.processed_pdf_files)} fontes PDF ativas.")
        elif pdf_files_in_folder:
            logger.warning("Nenhum chunk no ChromaDB após o processamento, apesar de existirem PDFs. Verifique logs de extração/chunking.")
        else:
            logger.info("Nenhum PDF na pasta de dados e nenhum chunk no ChromaDB.")

    def retrieve_relevant_chunks(self, query: str, k: int = config.DEFAULT_RETRIEVAL_K) -> List[str]:
        if self.collection.count() == 0:
            logger.warning("ChromaDB está vazio. Não é possível realizar busca.")
            return []
        try:
            query_embedding = self.embedding_model_st.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(k, self.collection.count()), 
                include=["documents"] 
            )
            retrieved_documents = results.get('documents', [[]])[0]
            logger.info(f"Recuperados {len(retrieved_documents)} chunks via ChromaDB.")
            return retrieved_documents
        except Exception as e:
            logger.error(f"Erro ao buscar chunks no ChromaDB: {e}", exc_info=True)
            return []

    def answer_query(self, query: str) -> str:
        logger.info(f"Consulta recebida: '{query}'")
        relevant_chunks = self.retrieve_relevant_chunks(query)

        if config.PRINT_DEBUG_CHUNKS:
            print("\n--- CHUNKS RECUPERADOS (DEBUG VIA CHROMA DB) ---")
            if relevant_chunks:
                for i, chunk_text in enumerate(relevant_chunks):
                   print(f"CHUNK {i+1}:\n{chunk_text}\n--------------------")
            else:
                print("Nenhum chunk relevante encontrado para a consulta.")
            print("--- FIM DOS CHUNKS (DEBUG) ---\n")
        
        if self.collection.count() == 0 and not relevant_chunks:
             return "Nenhum documento no banco de dados ou nenhum chunk relevante encontrado."
        
        return self.query_llm(query, relevant_chunks)

    def query_llm(self, query: str, context_chunks: List[str]) -> str:
        if not context_chunks:
            prompt_message = (f"Pergunta do Usuário: {query}\n\nAssistente: "
                              "Não encontrei informações específicas nos documentos para responder a esta pergunta.")
        else:
            context_str = "\n\n---\n\n".join(context_chunks)
            prompt_message = (
                f"Com base nos seguintes trechos de documentos, responda à pergunta do usuário de forma concisa e informativa.\n"
                f"Se a informação não estiver nos trechos, indique que não foi encontrada nos documentos fornecidos.\n"
                f"Priorize informações diretamente contidas nos trechos fornecidos.\n\n"
                f"Contexto dos Documentos:\n{context_str}\n\n"
                f"Pergunta do Usuário: {query}\n\n"
                f"Assistente:"
            )
        logger.info(f"Enviando prompt para Ollama (modelo: {self.configured_ollama_model})...")
        try:
            response = ollama.chat(
                model=self.configured_ollama_model,
                messages=[{'role': 'user', 'content': prompt_message}]
            )
            if response and 'message' in response and 'content' in response['message']:
                return response['message']['content'].strip()
            else:
                logger.error(f"Resposta inesperada do Ollama: {response}")
                return "Erro: LLM retornou resposta em formato inesperado."
        except Exception as e:
            logger.error(f"Erro ao comunicar com Ollama: {e}", exc_info=True)
            return f"Erro ao comunicar com o LLM: {e}"


if __name__ == '__main__':
    logger.info(f"Modo de teste RAGCore. Embedding: '{config.DEFAULT_EMBEDDING_MODEL}', Ollama: '{config.DEFAULT_OLLAMA_MODEL}'")
    if config.PRINT_DEBUG_CHUNKS: logger.info("Depuração de chunks ATIVADA.")
    else: logger.info("Depuração de chunks DESATIVADA.")

    try:
        rag_system = RAGCore() 
        if rag_system.collection.count() > 0:
            test_queries = ["Qual o tema principal?", "Existem prazos?", "Informações sobre bolsas?"] # Adapte aos seus PDFs
            for tq in test_queries:
                answer = rag_system.answer_query(tq)
                print(f"\nConsulta: {tq}\nResposta: {answer}\n{'-'*30}")
        else:
            print(f"Sistema RAG inicializado, mas sem documentos no ChromaDB. Verifique '{config.DEFAULT_DATA_FOLDER}'.")
            print("Para testar, adicione arquivos PDF à pasta 'data' (relativa à raiz do projeto) e reinicie.")

    except Exception as e:
        print(f"Erro crítico no teste do RAGCore: {e}")
        logger.error("Erro crítico no __main__ do RAGCore", exc_info=True)