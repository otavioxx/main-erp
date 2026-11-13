# \erp\main.py
import atexit
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime

import pytz
from PyQt6.QtCore import QLibraryInfo, QTimer, QTranslator
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from mainerp.core import paths
from mainerp.core.app_logging import configurar_logging, registrar_excecao
from mainerp.core.config import obter_config

# Importações movidas para o topo para evitar problemas
from mainerp.data.database import obter_database
from mainerp.data.restore import aplicar_restauracao_pendente
from mainerp.ui.dialogs.sobre_atualizacoes_dialog import (
    mostrar_novidades_apos_atualizacao,
)
from mainerp.ui.splash_pluma import PlumaSplash
from mainerp.ui.styles import aplicar_tema, cores_ativas
from mainerp.ui.views.main_window import MainWindow

logger = logging.getLogger(__name__)

# Códigos de saída entendidos pelo launcher (distribuicao/launcher.pyw)
EXIT_REINICIAR = 100  # o sistema pediu reinício (ex.: após restaurar backup)
EXIT_JA_EM_EXECUCAO = 3  # outra instância já está aberta (não é uma falha)
EXIT_RESTAURACAO_FALHOU = 4  # não iniciar versão antiga com restauração pendente

# Progresso da splash: percentual de etapas já concluídas quando cada etapa começa.
# As telas da janela principal dividem a faixa de PROGRESSO_INTERFACE a 100.
PROGRESSO_DIRETORIOS = 5
PROGRESSO_BANCO = 10
PROGRESSO_LIMPEZA = 15
PROGRESSO_INTERFACE = 20
PROGRESSO_CONCLUIDO = 100

_PADRAO_TELA = re.compile(r"(\d+)/(\d+)")


def percentual_carregamento_telas(mensagem: str) -> float | None:
    """Converte 'Carregando tela 3/8: ...' no percentual de telas já concluídas.

    Retorna None se a mensagem não informar a posição da tela; nesse caso a
    splash mantém o percentual atual, sem estimar avanço.
    """
    encontrado = _PADRAO_TELA.search(mensagem)
    if encontrado is None:
        return None
    atual, total = int(encontrado.group(1)), int(encontrado.group(2))
    if total <= 0 or not 1 <= atual <= total:
        return None
    faixa = PROGRESSO_CONCLUIDO - PROGRESSO_INTERFACE
    return PROGRESSO_INTERFACE + faixa * (atual - 1) / total


def obter_caminho_base():
    """Pasta do código desta versão (onde ficam o ícone e os módulos)."""
    return str(paths.CODE_DIR)


def definir_identidade_windows():
    """Dá ao processo uma identidade própria na barra de tarefas do Windows.

    Sem isso, rodando via pythonw.exe, o Windows agrupa a janela sob o ícone
    do Python em vez do ícone do PLUMA.
    """
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DigitalSolutions.MainERP"
        )
    except (AttributeError, OSError, ctypes.ArgumentError):
        return


def confirmar_abertura():
    """Avisa o launcher que a janela principal abriu (esta versão é saudável)."""
    arquivo = os.environ.get("MAINERP_OK_FILE")
    if not arquivo:
        return
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())
    except OSError:
        pass


def data_hora_brasilia():
    """Retorna a data e hora atual no fuso horário de Brasília"""
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia)


def limpar_pasta_relatorios():
    """Limpa a pasta de relatórios de forma segura"""
    caminho_relatorios = obter_config().obter_caminho_relatorios()

    try:
        if os.path.exists(caminho_relatorios):
            for arquivo in os.listdir(caminho_relatorios):
                caminho_arquivo = os.path.join(caminho_relatorios, arquivo)
                if os.path.isfile(caminho_arquivo):
                    os.unlink(caminho_arquivo)
    except OSError:
        logger.exception("Erro ao limpar pasta de relatórios")


def verificar_banco_dados():
    db = obter_database()
    try:
        with db.transacao() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='duplicatas'"
            )
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(duplicatas)")
    except sqlite3.Error:
        logger.exception("Erro ao verificar banco")

    return db


def carregar_icone_aplicacao() -> QIcon:
    """
    Retorna o ícone oficial da aplicação (icon.ico), que fica na pasta do código.
    """
    base_path = obter_caminho_base()
    caminho = os.path.join(base_path, "icon.ico")

    if os.path.exists(caminho):
        return QIcon(caminho)

    return QIcon()


def show_splash():
    """Mostra a splash Pluma com barra de progresso, com as cores do tema ativo."""
    config = obter_config()
    splash = PlumaSplash(
        cores=cores_ativas(),
        rodape=f"© OTC Tecnology - {config.APP_NAME} v{config.APP_VERSION}",
    )

    # Aplica ícone no splash se disponível
    icon = carregar_icone_aplicacao()
    if not icon.isNull():
        splash.setWindowIcon(icon)

    splash.show()
    return splash


def verificar_instancia_unica(nome_aplicacao):
    """
    Verifica se já existe uma instância do aplicativo em execução no Windows
    usando um mutex do sistema
    """
    try:
        # Tenta importar as bibliotecas do Windows
        import win32api
        import win32event
        import win32security
        import winerror

        # Cria um nome único para o mutex baseado no nome do aplicativo
        mutex_name = f"Global\\{nome_aplicacao}_Mutex"

        # Cria um atributo de segurança vazio para atender ao tipo esperado
        # pelo pywin32 e evitar o erro de análise de tipo em IDEs.
        mutex_attributes = win32security.SECURITY_ATTRIBUTES()
        mutex = win32event.CreateMutex(mutex_attributes, False, mutex_name)
        mutex_handle = int(mutex)
        last_error = win32api.GetLastError()

        if last_error == winerror.ERROR_ALREADY_EXISTS:
            # Mutex já existe - outra instância está executando
            win32api.CloseHandle(mutex_handle)
            return False

        # Registra função para fechar o mutex quando o programa terminar
        def cleanup_mutex():
            try:
                win32api.CloseHandle(mutex_handle)
            except Exception:  # noqa: S110 - limpeza ao encerrar; nada a fazer se falhar
                registrar_excecao(
                    __name__,
                    "Exception handled in verificar_instancia_unica.cleanup_mutex in main.py",
                )
                pass

        atexit.register(cleanup_mutex)
        return True

    except ImportError:
        # Fallback se pywin32 não estiver instalado
        logger.warning("pywin32 não instalado. Usando verificação simplificada.")
        return verificar_instancia_unica_simples(nome_aplicacao)
    except Exception:
        logger.exception("Erro ao verificar instância única")
        # Em caso de erro, permite a execução mas mostra aviso
        return True


def verificar_instancia_unica_simples(nome_aplicacao):
    """
    Método de fallback simples para verificar instância única
    usando arquivo de lock (menos confiável mas funciona sem dependências)
    """
    lock_dir = os.path.join(os.path.expanduser("~"), ".erp_lock")
    lock_file = os.path.join(lock_dir, f"{nome_aplicacao}.lock")

    os.makedirs(lock_dir, exist_ok=True)

    try:
        # Verifica se o arquivo de lock existe e está recente (últimos 5 minutos)
        if os.path.exists(lock_file):
            import time

            file_age = time.time() - os.path.getmtime(lock_file)
            if file_age < 300:  # 5 minutos
                return False
            else:
                # Arquivo muito antigo, provavelmente de uma instância que crashou
                os.unlink(lock_file)

        # Cria o arquivo de lock
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))

        # Registra função para remover o lock na saída
        def cleanup_lock():
            try:
                if os.path.exists(lock_file):
                    os.unlink(lock_file)
            except OSError:
                pass

        atexit.register(cleanup_lock)
        return True

    except Exception:
        logger.exception("Erro no método simples de verificação")
        return True


def reiniciar_aplicacao():
    """Reabre o sistema após restaurar um backup.

    Com o launcher (uso normal) basta sair com EXIT_REINICIAR: ele espera este
    processo terminar e abre de novo, já aplicando qualquer atualização.
    Rodando main.py direto (desenvolvimento), o próprio sistema se reabre.
    """
    if os.environ.get("MAINERP_LAUNCHER") == "1":
        return

    QMessageBox.information(
        None,
        "Reinício Necessário",
        "Abra o sistema novamente para concluir a restauração.",
    )


def erro_fatal(titulo, detalhe):
    """Registra o erro e avisa o usuário sem exigir console."""
    logger.exception("%s: %s", titulo, detalhe)
    try:
        if QApplication.instance() is None:
            QApplication(sys.argv)
        QMessageBox.critical(None, titulo, detalhe)
    except Exception:  # noqa: S110 - ultimo recurso ao reportar um erro fatal
        registrar_excecao(__name__, "Exception handled in erro_fatal in main.py")
        pass


def main():
    paths.preparar_ambiente()
    configurar_logging()
    definir_identidade_windows()
    config = obter_config()

    # Verificar se já existe uma instância em execução
    if not verificar_instancia_unica(config.APP_NAME):
        # Cria QApplication apenas para mostrar a mensagem
        temp_app = QApplication(sys.argv)
        temp_app.setWindowIcon(carregar_icone_aplicacao())

        QMessageBox.warning(
            None,
            "Aplicativo já em execução",
            f"{config.APP_NAME} já está sendo executado.\n"
            "Não é possível abrir múltiplas instâncias.",
        )
        sys.exit(EXIT_JA_EM_EXECUCAO)

    logger.info("App: %s v%s", config.APP_NAME, config.APP_VERSION)
    logger.info("Código: %s", obter_caminho_base())
    logger.info("Dados: %s", paths.DATA_DIR)
    logger.info("Banco: %s", config.obter_caminho_banco())
    logger.info("Relatórios: %s", config.obter_caminho_relatorios())
    logger.info("Debug: %s", config.DEBUG_MODE)

    # Criar aplicação
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("Digital Solutions")
    app.setWindowIcon(carregar_icone_aplicacao())

    # Configurar tradutor
    translator = QTranslator()
    if translator.load(
        "qtbase_pt_BR", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    ):
        app.installTranslator(translator)

    aplicar_tema(app, config.obter_tema())

    # Mostrar splash enquanto as tarefas reais de inicialização são executadas.
    splash = show_splash()
    app.processEvents()

    def update_splash_message(message, percentual=None):
        # A MainWindow informa só a mensagem "Carregando tela i/n"; dela sai o
        # percentual. Sem percentual conhecido, a barra permanece onde está.
        if percentual is None:
            percentual = percentual_carregamento_telas(message)
        splash.atualizar(message, percentual)
        app.processEvents()

    try:
        update_splash_message("Verificando restauração pendente...", 0)
        anterior = aplicar_restauracao_pendente(config.obter_caminho_banco())
        if anterior:
            logger.info("Restauração aplicada; backup anterior: %s", anterior)
    except Exception as erro:
        logger.exception("Falha ao aplicar restauração pendente")
        splash.close()
        QMessageBox.critical(
            None,
            "Erro na restauração",
            "O sistema não será aberto para proteger os dados. O estado do banco "
            "pode ter sido alterado e não é possível confirmar uma reversão.\n\n"
            "Não exclua nem altere o banco, a restauração pendente ou os backups. "
            "Procure suporte para verificar os arquivos antes de tentar novamente.\n\n"
            f"Detalhes: {erro!s}",
        )
        sys.exit(EXIT_RESTAURACAO_FALHOU)

    try:
        update_splash_message(
            "Preparando diretórios do sistema...", PROGRESSO_DIRETORIOS
        )
        config.criar_pastas_necessarias()

        update_splash_message(
            "Verificando banco de dados e migrações...", PROGRESSO_BANCO
        )
        verificar_banco_dados()

        update_splash_message("Limpando arquivos temporários...", PROGRESSO_LIMPEZA)
        limpar_pasta_relatorios()

        update_splash_message("Preparando interface...", PROGRESSO_INTERFACE)
        window = MainWindow(progress_callback=update_splash_message)

    except Exception as e:
        logger.exception("Erro durante inicialização")
        splash.close()
        QMessageBox.critical(
            None,
            "Erro de Inicialização",
            f"Erro durante a inicialização do sistema:\n{e!s}",
        )
        sys.exit(1)

    update_splash_message("Concluindo...", PROGRESSO_CONCLUIDO)
    splash.finish(window)
    window.show()
    confirmar_abertura()
    QTimer.singleShot(
        0, lambda: mostrar_novidades_apos_atualizacao(window, config.APP_VERSION)
    )

    # Executar aplicação
    try:
        result = app.exec()

        # Verificar se é um código de reinício (100)
        if result == EXIT_REINICIAR:
            window.backup_automatico.parar()
            worker = window.backup_automatico._worker
            if worker is not None:
                worker.wait()
            obter_database().close_connection()
            reiniciar_aplicacao()

        if result == EXIT_REINICIAR and os.environ.get("MAINERP_LAUNCHER") != "1":
            result = 0
        sys.exit(result)
    except Exception as e:
        erro_fatal(
            "Erro inesperado", f"O sistema encontrou um erro e será fechado:\n{e}"
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        erro_fatal("Erro fatal", f"O sistema não conseguiu iniciar:\n{e}")
        sys.exit(1)
