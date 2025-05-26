# src/rag_app/rag_terminal.py

import logging
import readline 
from datetime import datetime 

from .rag_core import RAGCore
from . import config # Importa config para EXIT_COMMANDS e SHOW_CHAT_TIMESTAMPS

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RAGTerminal:
    def __init__(self, rag_core_instance: RAGCore):
        self.rag_core = rag_core_instance
        db_count = 0
        if hasattr(self.rag_core, 'collection') and self.rag_core.collection:
            db_count = self.rag_core.collection.count()

        if db_count == 0 and \
           (not hasattr(self.rag_core, 'processed_pdf_files') or not self.rag_core.processed_pdf_files):
             print("⚠️  Atenção: Nenhum documento parece ter sido carregado ou processado no RAGCore.")
             print("⚠️  (A coleção ChromaDB está vazia e nenhum PDF processado foi listado).")
             print(f"⚠️  Certifique-se de que há arquivos PDF na pasta '{config.DEFAULT_DATA_FOLDER}' e que foram processados.")

    def start_interactive_session(self):
        print("\n--- Sistema RAG Interativo (Terminal) ---")
        if config.SHOW_CHAT_TIMESTAMPS: print("Timestamps das mensagens estão ATIVADOS.")
        else: print("Timestamps das mensagens estão DESATIVADOS.")
        
        # Informa alguns dos comandos de saída
        exit_cmds_preview = ', '.join(config.EXIT_COMMANDS[:3])
        print(f"Digite sua consulta ou um comando de saída (ex: {exit_cmds_preview}...) para terminar.")

        while True:
            try:
                prompt_text = "\nSua pergunta: "
                timestamp_prefix = ""

                if config.SHOW_CHAT_TIMESTAMPS:
                    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    timestamp_prefix = f"[{current_time_str}] "
                
                full_prompt = f"{timestamp_prefix}{prompt_text.lstrip()}"
                query = input(full_prompt)

                # Verifica se a entrada é um comando de saída
                if query.strip().lower() in config.EXIT_COMMANDS:
                    print("Saindo do sistema RAG. Até logo!")
                    break
                if not query.strip():
                    continue

                print("\nBuscando e processando sua resposta...")
                answer = self.rag_core.answer_query(query)

                response_prefix = "\nResposta do Sistema:\n"
                if config.SHOW_CHAT_TIMESTAMPS:
                    response_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    response_prefix = f"\n[{response_time_str}] Resposta do Sistema:\n"
                
                print(f"{response_prefix}{answer}")
                print("-" * 30)

            except KeyboardInterrupt:
                print("\nSessão interrompida pelo usuário. Saindo...")
                break
            except Exception as e:
                logger.error(f"Ocorreu um erro na sessão interativa: {e}", exc_info=True)
                print("Ocorreu um erro. Tente novamente ou use um comando de saída.")

if __name__ == '__main__':
    logger.info("Inicializando o sistema RAG Core para o terminal...")
    logger.info("Execute este script a partir da raiz do projeto: python -m src.rag_app.rag_terminal")

    try:
        core_system = RAGCore()
        if core_system.collection and core_system.collection.count() > 0:
            logger.info(f"{core_system.collection.count()} chunks encontrados no ChromaDB. Iniciando terminal.")
            terminal = RAGTerminal(core_system)
            terminal.start_interactive_session()
        else:
            logger.error(f"\n❌ Nenhum dado encontrado no ChromaDB ou nenhum PDF processado com sucesso. Verifique os logs e a pasta '{config.DEFAULT_DATA_FOLDER}'.")
            logger.error("   O terminal interativo não será iniciado se não houver dados para consulta.")
    except Exception as e:
        logger.error(f"\n❌ Erro crítico durante a inicialização do RAGCore: {e}", exc_info=True)
        logger.error("   Verifique se o Ollama está rodando e se os modelos estão acessíveis.")
        logger.error("   O terminal interativo não será iniciado.")