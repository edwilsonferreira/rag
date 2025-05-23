# rag_core.py

import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama
import logging
from typing import List, Tuple

# Importa as configurações do arquivo config.py
import config

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGCore:
    def __init__(self,
                 data_folder: str = config.DEFAULT_DATA_FOLDER,
                 model_name: str = config.DEFAULT_EMBEDDING_MODEL,
                 ollama_model: str = config.DEFAULT_OLLAMA_MODEL):
        self.data_folder = data_folder
        self.embedding_model = None
        self.index = None
        self.text_chunks_corpus = []
        self.processed_pdf_files = []

        self.configured_ollama_model = ollama_model
        self.configured_embedding_model_name = model_name

        try:
            logging.info(f"Carregando modelo de embedding: {self.configured_embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.configured_embedding_model_name)
            logging.info("Modelo de embedding carregado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao carregar o modelo SentenceTransformer '{self.configured_embedding_model_name}': {e}")
            raise

        self._ensure_data_folder()
        self._process_documents()

    def _ensure_data_folder(self):
        if not os.path.exists(self.data_folder):
            logging.warning(f"Pasta de dados '{self.data_folder}' não encontrada. Criando...")
            os.makedirs(self.data_folder)
            logging.info(f"Pasta '{self.data_folder}' criada.")

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text")
            doc.close()
            return text
        except Exception as e:
            logging.error(f"Erro ao extrair texto do PDF '{pdf_path}': {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = config.DEFAULT_CHUNK_SIZE, overlap: int = config.DEFAULT_CHUNK_OVERLAP) -> List[str]:
        words = text.split()
        if not words: return []
        chunks = []
        current_chunk_words = []
        current_length = 0
        approx_overlap_word_count = max(1, int(overlap * 0.2))

        for word in words:
            word_len_to_add = len(word) + (1 if current_chunk_words else 0)
            if current_length + word_len_to_add > chunk_size and current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                if approx_overlap_word_count > 0 and len(current_chunk_words) > approx_overlap_word_count:
                    current_chunk_words = current_chunk_words[-approx_overlap_word_count:]
                else:
                    current_chunk_words = []
                current_length = len(" ".join(current_chunk_words))
            current_chunk_words.append(word)
            current_length += word_len_to_add
        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))
        return [chunk for chunk in chunks if chunk.strip()]

    def _process_documents(self):
        pdf_files_in_folder = [f for f in os.listdir(self.data_folder) if f.endswith(".pdf")]
        if not pdf_files_in_folder:
            logging.warning(f"Nenhum arquivo PDF encontrado em '{self.data_folder}'.")
            self.processed_pdf_files = []
            return

        all_texts = []
        successfully_processed_files_temp = []
        for pdf_file in pdf_files_in_folder:
            pdf_path = os.path.join(self.data_folder, pdf_file)
            logging.info(f"Processando arquivo: {pdf_path}")
            text = self._extract_text_from_pdf(pdf_path)
            if text.strip():
                all_texts.append(text)
                successfully_processed_files_temp.append(pdf_file)
            else:
                logging.warning(f"Nenhum texto útil extraído de '{pdf_file}'.")
        self.processed_pdf_files = successfully_processed_files_temp

        if not all_texts:
            logging.warning("Nenhum texto pôde ser extraído dos PDFs para processamento.")
            return

        self.text_chunks_corpus = []
        for text_content in all_texts:
            chunks = self._chunk_text(text_content)
            self.text_chunks_corpus.extend(chunks)

        if not self.text_chunks_corpus:
            logging.warning("Nenhum chunk de texto gerado.")
            return
        logging.info(f"Total de {len(self.text_chunks_corpus)} chunks de texto gerados a partir de {len(self.processed_pdf_files)} arquivos PDF.")

        try:
            logging.info("Gerando embeddings...")
            embeddings = self.embedding_model.encode(self.text_chunks_corpus, show_progress_bar=True)
            logging.info("Embeddings gerados.")
            if embeddings is None or len(embeddings) == 0:
                logging.error("Nenhum embedding foi gerado.")
                return
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings, dtype=np.float32))
            logging.info(f"Índice FAISS criado com {self.index.ntotal} vetores.")
        except Exception as e:
            logging.error(f"Erro durante embeddings ou criação do índice FAISS: {e}")
            raise

    def retrieve_relevant_chunks(self, query: str, k: int = config.DEFAULT_RETRIEVAL_K) -> List[str]:
        if self.index is None or self.embedding_model is None or not self.text_chunks_corpus:
            return []
        try:
            query_embedding = self.embedding_model.encode([query])
            distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), k)
            relevant_chunks = [self.text_chunks_corpus[i] for i in indices[0] if i < len(self.text_chunks_corpus)]
            logging.info(f"Encontrados {len(relevant_chunks)} chunks relevantes.")
            return relevant_chunks
        except Exception as e:
            logging.error(f"Erro ao buscar chunks relevantes: {e}")
            return []

    def query_llm(self, query: str, context_chunks: List[str]) -> str:
        if not context_chunks:
            prompt = f"Usuário: {query}\n\nAssistente: Não encontrei informações relevantes nos documentos para responder."
        else:
            context_str = "\n\n---\n\n".join(context_chunks)
            prompt = (
                f"Com base nos seguintes trechos de documentos, responda à pergunta do usuário de forma concisa e informativa.\n"
                f"Se a informação não estiver nos trechos, indique que não foi encontrada nos documentos fornecidos.\n"
                f"Priorize informações diretamente contidas nos trechos fornecidos.\n\n"
                f"Contexto dos Documentos:\n{context_str}\n\n"
                f"Pergunta do Usuário: {query}\n\n"
                f"Assistente:"
            )
        logging.info(f"Enviando prompt para Ollama (modelo: {self.configured_ollama_model})...")
        try:
            response = ollama.chat(
                model=self.configured_ollama_model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            if 'message' in response and 'content' in response['message']:
                return response['message']['content'].strip()
            else:
                logging.error(f"Resposta inesperada do Ollama: {response}")
                return "Erro ao processar a resposta do LLM."
        except Exception as e:
            logging.error(f"Erro ao comunicar com o Ollama: {e}")
            return f"Erro ao comunicar com o LLM: {e}"

    def answer_query(self, query: str) -> str:
        logging.info(f"Recebida nova consulta: '{query}'")
        relevant_chunks = self.retrieve_relevant_chunks(query)

        if config.PRINT_DEBUG_CHUNKS:
            print("\n--- CHUNKS RECUPERADOS (DEBUG) ---")
            if relevant_chunks:
                for i, chunk_text in enumerate(relevant_chunks):
                   print(f"CHUNK {i+1}:\n{chunk_text}\n--------------------")
            else:
                print("Nenhum chunk relevante encontrado para a consulta.")
            print("--- FIM DOS CHUNKS (DEBUG) ---\n")
        
        if not self.text_chunks_corpus and not relevant_chunks:
             return "Nenhum documento foi carregado ou processado, ou nenhum chunk relevante foi encontrado."
        
        response = self.query_llm(query, relevant_chunks)
        logging.info(f"Resposta gerada para '{query}': '{response}'")
        return response

if __name__ == '__main__':
    print(f"Usando embedding_model='{config.DEFAULT_EMBEDDING_MODEL}', ollama_model='{config.DEFAULT_OLLAMA_MODEL}'")
    if config.PRINT_DEBUG_CHUNKS:
        print("Depuração de chunks ATIVADA.")
    else:
        print("Depuração de chunks DESATIVADA.")
    try:
        rag_system = RAGCore()
        if rag_system.index or rag_system.text_chunks_corpus:
            print("-" * 50)
            test_query_1 = "Qual o tema principal discutido?" 
            answer_1 = rag_system.answer_query(test_query_1)
            print(f"\nConsulta: {test_query_1}\nResposta: {answer_1}\n{'-'*50}")
        else:
            print("Sistema RAG não pôde ser inicializado ou não processou documentos.")
    except Exception as e:
        print(f"Ocorreu um erro crítico ao executar o RAGCore: {e}")
        logging.error("Erro crítico no __main__ do RAGCore", exc_info=True)
        