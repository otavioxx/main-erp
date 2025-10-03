# \erp\main.py
import atexit
import os
import sys
from datetime import datetime

import pytz
from PyQt6.QtCore import QLibraryInfo, Qt, QTimer, QTranslator
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen

from config import obter_config

# Importações movidas para o topo para evitar problemas
from database import Database
from styles import aplicar_tema_dark_clean
from views.main_window import MainWindow


def obter_caminho_base():
    """Obtém o caminho base correto para o executável ou script"""
    if getattr(sys, "frozen", False):
        # Executando como executável compilado
        base_path = sys._MEIPASS
    else:
        # Executando como script normal
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path


def data_hora_brasilia():
    """Retorna a data e hora atual no fuso horário de Brasília"""
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia)


def limpar_pasta_relatorios():
    """Limpa a pasta de relatórios de forma segura"""
    base_path = obter_caminho_base()
    caminho_relatorios = os.path.join(base_path, "relatorios")

    try:
        if os.path.exists(caminho_relatorios):
            for arquivo in os.listdir(caminho_relatorios):
                caminho_arquivo = os.path.join(caminho_relatorios, arquivo)
                if os.path.isfile(caminho_arquivo):
                    os.unlink(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao limpar pasta de relatórios: {e}")


def verificar_banco_dados():
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='duplicatas'"
        )
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(duplicatas)")
            colunas = cursor.fetchall()
        else:
            pass

    except Exception as e:
        print(f"Erro ao verificar banco: {e}")
    finally:
        conn.close()

    return db


def carregar_icone_aplicacao():
    """Carrega o ícone da aplicação com fallbacks"""
    base_path = obter_caminho_base()

    possiveis_caminhos = [
        os.path.join(base_path, "icon.ico"),
        os.path.join(base_path, "icons", "icon.ico"),
        os.path.join(base_path, "assets", "icon.ico"),
        os.path.join(base_path, "resources", "icon.ico"),
        os.path.join(base_path, "icon.png"),
        os.path.join(base_path, "icons", "icon.png"),
    ]

    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                return QIcon(caminho)
            except:
                continue

    # Fallback: ícone padrão do Qt
    return QIcon()


def show_splash(
    app_name="ERP System",
    footer_text="© Digital Solutions - Todos os direitos reservados",
):
    """Mostra tela de splash com quinas arredondadas e textos - Adaptado para PyQt6"""
    width, height = 450, 300
    radius = 12

    def create_splash_pixmap(progress_message=""):
        """Cria o pixmap do splash com mensagem de progresso"""
        splash_pixmap = QPixmap(width, height)
        splash_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fundo arredondado
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, radius, radius)
        painter.fillPath(path, QColor("#2b2b2b"))

        # Borda sutil
        painter.setPen(QColor("#404040"))
        painter.drawRoundedRect(1, 1, width - 2, height - 2, radius - 1, radius - 1)

        # Título
        title_font = QFont("Segoe UI", 34, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff"))
        title_rect = splash_pixmap.rect().adjusted(20, 40, -20, -200)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, app_name)

        # Subtítulo
        subtitle_font = QFont("Segoe UI", 11)
        painter.setFont(subtitle_font)
        painter.setPen(QColor("#cccccc"))
        subtitle_rect = splash_pixmap.rect().adjusted(20, 100, -20, -160)
        painter.drawText(
            subtitle_rect, Qt.AlignmentFlag.AlignCenter, "Sistema de Gestão Empresarial"
        )

        # MENSAGEM DE PROGRESSO (no meio)
        if progress_message:
            progress_font = QFont("Segoe UI", 10)
            painter.setFont(progress_font)
            painter.setPen(QColor("#ffffff"))
            # Posiciona no meio da tela (Y: 180-200)
            progress_rect = splash_pixmap.rect().adjusted(30, 180, -30, -80)
            painter.drawText(
                progress_rect, Qt.AlignmentFlag.AlignCenter, progress_message
            )

        # Copyright (rodapé)
        footer_font = QFont("Segoe UI", 8)
        painter.setFont(footer_font)
        painter.setPen(QColor("#888888"))
        footer_rect = splash_pixmap.rect().adjusted(20, 0, -20, -15)
        painter.drawText(
            footer_rect,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            footer_text,
        )

        painter.end()
        return splash_pixmap

    # Cria splash inicial sem mensagem
    initial_pixmap = create_splash_pixmap()
    splash = QSplashScreen(initial_pixmap)
    splash.setMask(initial_pixmap.mask())

    # Aplica ícone no splash se disponível
    icon = carregar_icone_aplicacao()
    if not icon.isNull():
        splash.setWindowIcon(icon)

    # Adiciona método para atualizar mensagem
    def update_message(message):
        new_pixmap = create_splash_pixmap(message)
        splash.setPixmap(new_pixmap)
        splash.setMask(new_pixmap.mask())

    # Adiciona o método ao objeto splash
    splash.update_message = update_message

    splash.show()
    return splash


def configurar_caminhos():
    """Configura os caminhos para o ambiente compilado"""
    base_path = obter_caminho_base()

    # Adiciona caminhos ao sys.path para imports
    if getattr(sys, "frozen", False):
        caminhos_import = [
            os.path.join(base_path, "views"),
            os.path.join(base_path, "utils"),
            os.path.join(base_path, "models"),
            os.path.join(base_path, "imprecoes"),
            os.path.join(base_path, "relatorios"),
            os.path.join(base_path, "database"),
        ]

        for caminho in caminhos_import:
            if os.path.exists(caminho) and caminho not in sys.path:
                sys.path.insert(0, caminho)


def verificar_instancia_unica(nome_aplicacao):
    """
    Verifica se já existe uma instância do aplicativo em execução no Windows
    usando um mutex do sistema
    """
    try:
        # Tenta importar as bibliotecas do Windows
        import win32api
        import win32event
        import winerror

        # Cria um nome único para o mutex baseado no nome do aplicativo
        mutex_name = f"Global\\{nome_aplicacao}_Mutex"

        # Tenta criar o mutex
        mutex = win32event.CreateMutex(None, False, mutex_name)
        last_error = win32api.GetLastError()

        if last_error == winerror.ERROR_ALREADY_EXISTS:
            # Mutex já existe - outra instância está executando
            win32api.CloseHandle(mutex)
            return False

        # Registra função para fechar o mutex quando o programa terminar
        def cleanup_mutex():
            try:
                win32api.CloseHandle(mutex)
            except:
                pass

        atexit.register(cleanup_mutex)
        return True

    except ImportError:
        # Fallback se pywin32 não estiver instalado
        print("Aviso: pywin32 não instalado. Usando verificação simplificada.")
        return verificar_instancia_unica_simples(nome_aplicacao)
    except Exception as e:
        print(f"Erro ao verificar instância única: {e}")
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
            except:
                pass

        atexit.register(cleanup_lock)
        return True

    except Exception as e:
        print(f"Erro no método simples de verificação: {e}")
        return True


def main():
    import time

    # Configura caminhos primeiro
    configurar_caminhos()

    # Agora importa após configurar os caminhos
    global Database, MainWindow, aplicar_tema_dark_clean, obter_config
    from config import obter_config
    from database import Database
    from styles import aplicar_tema_dark_clean
    from views.main_window import MainWindow

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
        sys.exit(1)

    print(f"App: {config.APP_NAME} v{config.APP_VERSION}")
    print(f"Base path: {obter_caminho_base()}")
    print(f"Banco: {config.obter_caminho_banco()}")
    print(f"Relatórios: {config.obter_caminho_relatorios()}")
    print(f"Debug: {config.DEBUG_MODE}")

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

    # Aplicar tema
    aplicar_tema_dark_clean(app)

    # SPLASH COM DURAÇÃO ESTENDIDA E MENSAGENS DE PROGRESSO
    SPLASH_MIN_DURATION = 6.0  # Mínimo de 6 segundos

    # Mostrar splash screen
    splash = show_splash(config.APP_NAME)
    app.processEvents()  # Força a exibição do splash

    # Função para atualizar mensagem no splash (posicionada no meio)
    def update_splash_message(message):
        # Usa o método customizado para desenhar a mensagem no meio
        splash.update_message(message)
        app.processEvents()

    # Inicia cronômetro
    start_time = time.time()

    # Executa inicializações com delays intencionais e mensagens
    print("Iniciando processos de inicialização...")

    try:
        # Etapa 1: Configurações
        update_splash_message("Carregando configurações do sistema...")
        time.sleep(0.8)  # Delay intencional

        # Etapa 2: Pastas
        update_splash_message("Criando estrutura de diretórios...")
        config.criar_pastas_necessarias()
        time.sleep(0.7)

        # Etapa 3: Banco de dados
        update_splash_message("Conectando ao banco de dados...")
        time.sleep(0.6)
        db = verificar_banco_dados()
        time.sleep(0.4)

        # Etapa 4: Limpeza
        update_splash_message("Limpando arquivos temporários...")
        limpar_pasta_relatorios()
        time.sleep(0.5)

        # Etapa 5: Módulos do sistema
        update_splash_message("Carregando módulos do sistema...")
        time.sleep(1.0)  # Simula carregamento de módulos

        # Etapa 6: Interface
        update_splash_message("Inicializando interface gráfica...")
        time.sleep(0.8)
        window = MainWindow()
        time.sleep(0.6)

        # Etapa 7: Finalizando
        update_splash_message("Finalizando inicialização...")
        time.sleep(0.6)

    except Exception as e:
        print(f"Erro durante inicialização: {e}")
        splash.close()
        QMessageBox.critical(
            None,
            "Erro de Inicialização",
            f"Erro durante a inicialização do sistema:\n{str(e)}",
        )
        sys.exit(1)

    # Calcula tempo decorrido
    elapsed = time.time() - start_time
    print(f"Inicialização concluída em {elapsed:.2f} segundos")

    # Calcula tempo restante para atingir duração mínima
    remaining = max(0, (SPLASH_MIN_DURATION - elapsed) * 1000)  # Converte para ms

    # Função para finalizar splash e mostrar janela principal
    def show_main_window():
        update_splash_message("Sistema pronto! Abrindo interface...")
        app.processEvents()
        time.sleep(0.3)  # Pequeno delay antes de abrir
        splash.finish(window)
        window.show()

    if remaining > 0:
        print(
            f"Aguardando {remaining/1000:.1f}s adicionais para duração mínima do splash..."
        )
        update_splash_message("Preparando sistema...")
        QTimer.singleShot(int(remaining), show_main_window)
    else:
        print(
            "Inicialização demorou mais que o mínimo, mostrando sistema imediatamente."
        )
        show_main_window()

    # Executar aplicação
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro fatal: {e}")
        import traceback

        traceback.print_exc()
        input("Pressione Enter para sair...")
