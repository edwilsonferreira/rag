# rag_terminal.py

from rag_core import RAGCore
import logging
import readline # Para melhor experiência de input
from datetime import datetime # Para timestamps
import config # Para acessar o flag SHOW_CHAT_TIMESTAMPS

# Configuração de logging (opcional, pode ser controlado pelo rag_core)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        if not self.rag_core.text_chunks_corpus and (not hasattr(self.rag_core, 'processed_pdf_files') or not self.rag_core.processed_pdf_files):
             print("⚠️  Atenção: Nenhum documento foi carregado ou processado no RAGCore.")
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

                # Monta o prompt para o input
                full_prompt = f"{timestamp_prefix}{prompt_text.lstrip()}" # lstrip para remover o \n se o prefixo já estiver lá
                
                query = input(full_prompt)

                if query.strip().lower() == 'sair':
                    print("Saindo do sistema RAG. Até logo!")
                    break
                if not query.strip():
                    continue

                print("\nBuscando e processando sua resposta...")
                answer = self.rag_core.answer_query(query)

                # Prepara a exibição da resposta com timestamp (se ativado)
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
                logging.error(f"Ocorreu um erro na sessão interativa: {e}")
                print("Ocorreu um erro. Tente novamente ou digite 'sair'.")

if __name__ == '__main__':
    print("Inicializando o sistema RAG Core para o terminal...")
    print("Isso pode levar alguns minutos dependendo do número e tamanho dos PDFs...")

    try:
        # RAGCore usará os defaults de config.py para os modelos
        core_system = RAGCore()

        if core_system.index or core_system.text_chunks_corpus or \
           (hasattr(core_system, 'processed_pdf_files') and core_system.processed_pdf_files):
            terminal = RAGTerminal(core_system)
            terminal.start_interactive_session()
        else:
            print(f"\n❌ Falha ao inicializar o RAGCore ou nenhum documento processado. Verifique os logs e a pasta '{config.DEFAULT_DATA_FOLDER}'.")
            print("   O terminal interativo não será iniciado se não houver dados para consulta.")

    except Exception as e:
        print(f"\n❌ Erro crítico durante a inicialização do RAGCore: {e}")
        print("   Verifique se o Ollama está rodando e se os modelos estão acessíveis.")
        print("   O terminal interativo não será iniciado.")