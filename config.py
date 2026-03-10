"""
Arquivo de configuração simples para o ERP
Use este arquivo para centralizr configurações que você pode querer mudar
"""

import os
from pathlib import Path


class ConfigERP:
    """Configurações centralizadas do ERP"""

    # === CONFIGURAÇÕES BÁSICAS ===
    APP_NAME = "MainERP"
    APP_VERSION = "0.05"
    ORGANIZATION = "Meu Negócio"

    # === CONFIGURAÇÕES DE ARQUIVO ===
    # Pasta onde ficam os relatórios
    PASTA_RELATORIOS = "relatorios"

    # Arquivo de log
    ARQUIVO_LOG = "erp.log"

    # === CONFIGURAÇÕES DE BANCO ===
    # Nome do arquivo do banco SQLite
    BANCO_SQLITE = "erp.db"

    # === CONFIGURAÇÕES VISUAIS ===
    # Tema padrão (você pode mudar facilmente)
    TEMA_PADRAO = "light_clean"  # ou "dark_clean", "dark_blue", "high_contrast"

    # Fonte padrão
    FONTE_FAMILIA = "Segoe UI"
    FONTE_TAMANHO = 13

    # === CONFIGURAÇÕES REGIONAIS ===
    TIMEZONE = "America/Sao_Paulo"
    IDIOMA = "pt_BR"

    # === CONFIGURAÇÕES DE DESENVOLVIMENTO ===
    # Habilitar logs detalhados (True para desenvolvimento, False para uso normal)
    DEBUG_MODE = False

    # Nível de log (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = "WARNING"

    # === MÉTODOS AUXILIARES ===

    @classmethod
    def criar_pastas_necessarias(cls):
        """Cria pastas necessárias se não existirem"""
        pastas = [cls.PASTA_RELATORIOS, "icons"]

        for pasta in pastas:
            Path(pasta).mkdir(exist_ok=True)

    @classmethod
    def obter_caminho_banco(cls):
        """Retorna caminho completo do banco"""
        return Path(cls.BANCO_SQLITE).absolute()

    @classmethod
    def obter_caminho_relatorios(cls):
        """Retorna caminho da pasta de relatórios"""
        return Path(cls.PASTA_RELATORIOS).absolute()

    @classmethod
    def verificar_primeira_execucao(cls):
        """Verifica se é a primeira execução do sistema"""
        return not cls.obter_caminho_banco().exists()


# === CONFIGURAÇÕES ESPECÍFICAS POR AMBIENTE ===


class ConfigDesenvolvimento(ConfigERP):
    """Configurações para desenvolvimento"""

    DEBUG_MODE = True
    LOG_LEVEL = "DEBUG"
    ARQUIVO_LOG = "erp_dev.log"


class ConfigProducao(ConfigERP):
    """Configurações para uso normal"""

    DEBUG_MODE = False
    LOG_LEVEL = "WARNING"


# === FUNÇÃO PARA OBTER CONFIGURAÇÃO ATUAL ===


def obter_config():
    """
    Retorna a configuração apropriada
    Você pode mudar aqui qual configuração usar
    """

    # Para desenvolvimento, descomente esta linha:
    # return ConfigDesenvolvimento

    # Para uso normal:
    return ConfigProducao
