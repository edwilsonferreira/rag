# rag_terminal.py

from rag_core import RAGCore
import logging
import readline # Para melhor experiência de input
from datetime import datetime # Para timestamps
import config # Para acessar flags e defaults

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGTerminal:
    """
    Interface de terminal interativa para o sistema RAG.
    """

    def __init__(self, rag_core_instance: RAGCore):
        """
        Inicializa o RAGTerminal.

        Args:
            rag_core_instance (RAGCore): Uma instância já inicializada de RAGCore.
        """
        self.rag_core = rag_core_instance
        # Atualiza a verificação para usar o ChromaDB e a lista de arquivos processados
        if self.rag_core.collection.count() == 0 and \
           (not hasattr(self.rag_core, 'processed_pdf_files') or not self.rag_core.processed_pdf_files):
             print("⚠️  Atenção: Nenhum documento parece ter sido carregado ou processado no RAGCore.")
             print("⚠️  (A coleção ChromaDB está vazia e nenhum PDF processado foi listado).")
             print("⚠️  As respostas podem não ser baseadas em seus documentos.")
             print(f"⚠️  Certifique-se de que há arquivos PDF na pasta '{config.DEFAULT_DATA_FOLDER}' e que foram processados.")


    def start_interactive_session(self):
        """
        Inicia a sessão interativa no terminal.
        """
        print("\n--- Sistema RAG Interativo (Terminal) ---")
        if config.SHOW_CHAT_TIMESTAMPS:
            print("Timestamps das mensagens estão ATIVADOS.")
        else:
            print("Timestamps das mensagens estão DESATIVADOS.")
        print("Digite sua consulta abaixo ou 'sair' para terminar.")

        while True:
            try:
                prompt_text = "\nSua pergunta: "
                timestamp_prefix = ""

                if config.SHOW_CHAT_TIMESTAMPS:
                    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    timestamp_prefix = f"[{current_time_str}] "
                
                full_prompt = f"{timestamp_prefix}{prompt_text.lstrip()}"
                query = input(full_prompt)

                if query.strip().lower() == 'sair':
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
                logging.error(f"Ocorreu um erro na sessão interativa: {e}", exc_info=True)
                print("Ocorreu um erro. Tente novamente ou digite 'sair'.")

if __name__ == '__main__':
    logger.info("Inicializando o sistema RAG Core para o terminal...")
    logger.info("Isso pode levar alguns minutos na primeira execução ou ao processar novos PDFs...")

    try:
        core_system = RAGCore()

        # Condição ATUALIZADA para verificar se o RAGCore está pronto usando ChromaDB
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