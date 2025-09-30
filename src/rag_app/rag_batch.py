# src/rag_app/rag_batch_query.py (ou src/rag_app/rag_batch.py se você renomeou)

import argparse
import logging
from datetime import datetime

# Importações corrigidas para usar referências relativas dentro do pacote 'rag_app'
from .rag_core import RAGCore
from . import config

logger = logging.getLogger(__name__)
if not logger.handlers: # Evita adicionar handlers múltiplos
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_batch_queries(input_file_path: str, output_file_path: str = None):
    """
    Lê perguntas de um arquivo, consulta o sistema RAG e opcionalmente salva os resultados.
    """
    logger.info(f"Iniciando o processamento em lote do arquivo de perguntas: {input_file_path}")

    try:
        logger.info("Inicializando o RAGCore...")
        # RAGCore usará as configurações padrão de config.py se não forem passadas aqui
        rag_system = RAGCore(
            data_folder=config.DEFAULT_DATA_FOLDER,
            model_name=config.DEFAULT_EMBEDDING_MODEL,
            ollama_model=config.DEFAULT_OLLAMA_MODEL
        )
        db_count = 0
        if hasattr(rag_system, 'collection') and rag_system.collection:
            db_count = rag_system.collection.count()

        # Verifica se o RAGCore foi inicializado e processou documentos
        if db_count == 0 and \
           (not hasattr(rag_system, 'processed_pdf_files') or not rag_system.processed_pdf_files):
            logger.error("O RAGCore não pôde ser inicializado corretamente ou nenhum documento foi processado.")
            logger.error(f"Verifique se existem documentos PDF na pasta '{config.DEFAULT_DATA_FOLDER}' (relativa à raiz do projeto) e se foram processados com sucesso.")
            return
        logger.info("RAGCore inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao inicializar o RAGCore: {e}", exc_info=True)
        return

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
        if not questions:
            logger.warning(f"Nenhuma pergunta encontrada no arquivo de entrada: {input_file_path}")
            return
        logger.info(f"Lidas {len(questions)} perguntas de '{input_file_path}'.")
    except FileNotFoundError:
        logger.error(f"Arquivo de entrada não encontrado: {input_file_path}")
        return
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo de entrada '{input_file_path}': {e}", exc_info=True)
        return

    results_for_file = [] 
    total_questions = len(questions)

    for i, question in enumerate(questions):
        start_time_query = datetime.now()
        logger.info(f"Processando pergunta {i+1}/{total_questions}: \"{question}\"")
        print(f"\n{'-'*10} Pergunta {i+1}/{total_questions} {'-'*10}")
        
        timestamp_prefix = ""
        if config.SHOW_CHAT_TIMESTAMPS:
            timestamp_prefix = f"[{start_time_query.strftime('%Y-%m-%d %H:%M:%S')}] "
        print(f"{timestamp_prefix}P: {question}")

        try:
            answer = rag_system.answer_query(question)
            answer_timestamp_prefix = ""
            if config.SHOW_CHAT_TIMESTAMPS:
                answer_timestamp_prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            print(f"{answer_timestamp_prefix}R: {answer}")
            results_for_file.append({"question_number": i+1, "question": question, "answer": answer})
        except Exception as e:
            error_message = f"Erro ao processar a pergunta \"{question}\": {e}"
            logger.error(error_message, exc_info=True)
            error_timestamp_prefix = ""
            if config.SHOW_CHAT_TIMESTAMPS:
                error_timestamp_prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            print(f"{error_timestamp_prefix}R: ERRO - {e}")
            results_for_file.append({"question_number": i+1, "question": question, "answer": f"ERRO: {e}"})
        
        end_time_query = datetime.now()
        logger.info(f"Pergunta {i+1} processada em {(end_time_query - start_time_query).total_seconds():.2f} segundos.")

    if output_file_path:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                for result in results_for_file:
                    outfile.write(f"Pergunta {result['question_number']}:\n")
                    outfile.write(f"P: {result['question']}\n")
                    outfile.write(f"R: {result['answer']}\n")
                    outfile.write("-" * 40 + "\n\n") 
            logger.info(f"Resultados salvos em formato texto puro em: {output_file_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar os resultados no arquivo '{output_file_path}': {e}", exc_info=True)
            print(f"\nERRO ao salvar resultados em '{output_file_path}'. Verifique os logs.")

    logger.info("Processamento em lote concluído.")

def main():
    parser = argparse.ArgumentParser(
        description="Processa um lote de perguntas de um arquivo de texto usando o sistema RAG."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Caminho para o arquivo de texto de entrada (uma pergunta por linha)."
    )
    parser.add_argument(
        "-o", "--output_file",
        type=str,
        default=None,
        help="Caminho opcional para o arquivo de texto de saída onde as perguntas e respostas serão salvas."
    )
    
    args = parser.parse_args()
    
    if config.PRINT_DEBUG_CHUNKS:
        logger.info("A depuração de chunks está ATIVADA (config.PRINT_DEBUG_CHUNKS=True).")
    else:
        logger.info("A depuração de chunks está DESATIVADA (config.PRINT_DEBUG_CHUNKS=False).")
    if config.SHOW_CHAT_TIMESTAMPS:
        logger.info("Timestamps de chat ATIVADOS (config.SHOW_CHAT_TIMESTAMPS=True).")
    else:
        logger.info("Timestamps de chat DESATIVADOS (config.SHOW_CHAT_TIMESTAMPS=False).")


    run_batch_queries(args.input_file, args.output_file)

if __name__ == "__main__":
    # Para executar este script da raiz do projeto:
    # python -m src.rag_app.rag_batch_query <argumentos>
    # (ou src.rag_app.rag_batch se você renomeou o arquivo)
    main()