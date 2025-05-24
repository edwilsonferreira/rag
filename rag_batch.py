# rag_batch_query.py

import argparse
import logging # Removido 'json' já que não será mais usado para saída
from datetime import datetime

# Certifique-se de que RAGCore e config estão acessíveis no PYTHONPATH
# ou na mesma pasta
from rag_core import RAGCore
import config

# Configuração do logging para este script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_batch_queries(input_file_path: str, output_file_path: str = None):
    """
    Lê perguntas de um arquivo, consulta o sistema RAG e opcionalmente salva os resultados.

    Args:
        input_file_path (str): Caminho para o arquivo de texto contendo uma pergunta por linha.
        output_file_path (str, optional): Caminho para salvar os resultados em formato texto puro.
                                          Se None, os resultados são apenas impressos no console.
    """
    logger.info(f"Iniciando o processamento em lote do arquivo de perguntas: {input_file_path}")

    try:
        logger.info("Inicializando o RAGCore...")
        rag_system = RAGCore(
            data_folder=config.DEFAULT_DATA_FOLDER,
            model_name=config.DEFAULT_EMBEDDING_MODEL,
            ollama_model=config.DEFAULT_OLLAMA_MODEL
        )
        if not rag_system.text_chunks_corpus and (not hasattr(rag_system, 'processed_pdf_files') or not rag_system.processed_pdf_files):
            logger.error("O RAGCore não pôde ser inicializado corretamente ou nenhum documento foi processado.")
            logger.error(f"Verifique se existem documentos PDF na pasta '{config.DEFAULT_DATA_FOLDER}' e se foram processados com sucesso.")
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

    results_for_file = [] # Mantemos uma lista para os dados, mesmo para saída de texto
    total_questions = len(questions)

    for i, question in enumerate(questions):
        start_time_query = datetime.now()
        logger.info(f"Processando pergunta {i+1}/{total_questions}: \"{question}\"")
        print(f"\n{'-'*10} Pergunta {i+1}/{total_questions} {'-'*10}")
        print(f"P: {question}")

        try:
            answer = rag_system.answer_query(question)
            print(f"R: {answer}")
            results_for_file.append({"question_number": i+1, "question": question, "answer": answer})
        except Exception as e:
            error_message = f"Erro ao processar a pergunta \"{question}\": {e}"
            logger.error(error_message, exc_info=True)
            print(f"R: ERRO - {e}")
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
                    outfile.write("-" * 40 + "\n\n") # Separador entre perguntas
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
        help="Caminho opcional para o arquivo de texto de saída onde as perguntas e respostas serão salvas." # Alterado JSON para texto
    )
    
    args = parser.parse_args()
    
    if config.PRINT_DEBUG_CHUNKS:
        logger.info("A depuração de chunks está ATIVADA (config.PRINT_DEBUG_CHUNKS=True). Os chunks recuperados serão impressos no console.")
    else:
        logger.info("A depuração de chunks está DESATIVADA (config.PRINT_DEBUG_CHUNKS=False).")

    run_batch_queries(args.input_file, args.output_file)

if __name__ == "__main__":
    main()