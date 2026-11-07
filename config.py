# \erp\config.py
import json
import os
from typing import Any

from paths import caminho_dados


class Config:
    """Classe para gerenciar configurações do sistema"""

    # Constantes da aplicação
    APP_NAME = "MainERP"
    APP_VERSION = "0.06"
    DEBUG_MODE = False

    def __init__(self, config_file: str | None = None):
        # config.json fica na pasta de dados, fora do código das releases
        self.config_file = config_file or caminho_dados("config.json")
        self.default_config = {
            "database": {"name": "erp.db"},
            "appearance": {
                "theme": "dark",
                "font_family": "Segoe UI",
                "font_size": 9,
                "accent_color": "#007acc",
            },
            "company": {
                "name": "",
                "cnpj": "",
                "address": "",
                "phone": "",
                "email": "",
                "logo_path": "",
            },
            "sales": {
                "default_payment_method": "dinheiro",
                "enable_installments": True,
                "max_installments": 12,
                "default_installments": 1,
            },
            "inventory": {
                "low_stock_threshold": 10,
                "enable_stock_control": True,
                "notify_low_stock": True,
            },
            "security": {
                "password_required": False,
                "auto_logout_minutes": 30,
                "max_login_attempts": 3,
            },
            "reports": {
                "default_report_path": "relatorios",
                "auto_generate_sales_report": True,
                "report_format": "pdf",
            },
        }
        self.config = self.load_config()

    # ------------------------------------------------------------------
    # Métodos de caminho
    # ------------------------------------------------------------------

    def obter_caminho_banco(self) -> str:
        """Retorna o caminho completo do banco de dados"""
        return caminho_dados(self.get("database.name", "erp.db"))

    def obter_caminho_relatorios(self) -> str:
        """Retorna o caminho da pasta de relatórios"""
        return caminho_dados(self.get("reports.default_report_path", "relatorios"))

    def criar_pastas_necessarias(self):
        """Cria as pastas necessárias para o funcionamento do sistema"""
        pastas = [
            self.obter_caminho_relatorios(),
        ]
        for pasta in pastas:
            try:
                os.makedirs(pasta, exist_ok=True)
            except OSError as e:
                print(f"Erro ao criar pasta '{pasta}': {e}")

    # ------------------------------------------------------------------
    # Métodos de persistência
    # ------------------------------------------------------------------

    def load_config(self) -> dict[str, Any]:
        """Carrega as configurações do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return self.default_config.copy()
        except (OSError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar configurações: {e}")
            return self.default_config.copy()

    def save_config(self) -> bool:
        """Salva as configurações no arquivo JSON"""
        try:
            dir_name = os.path.dirname(self.config_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except OSError as e:
            print(f"Erro ao salvar configurações: {e}")
            return False

    # ------------------------------------------------------------------
    # Acesso genérico por chave
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração usando notação de ponto"""
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        """Define um valor de configuração usando notação de ponto"""
        keys = key.split(".")
        config_ref = self.config
        try:
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            config_ref[keys[-1]] = value
            return self.save_config()
        except (KeyError, TypeError):
            return False

    def reset_to_defaults(self) -> bool:
        """Restaura as configurações padrão"""
        self.config = self.default_config.copy()
        return self.save_config()

    # ------------------------------------------------------------------
    # Atalhos semânticos
    # ------------------------------------------------------------------

    def get_database_path(self) -> str:
        return self.obter_caminho_banco()

    def get_report_path(self) -> str:
        return self.obter_caminho_relatorios()

    def get_company_info(self) -> dict[str, str]:
        return {
            "name": self.get("company.name", ""),
            "cnpj": self.get("company.cnpj", ""),
            "address": self.get("company.address", ""),
            "phone": self.get("company.phone", ""),
            "email": self.get("company.email", ""),
        }

    def set_company_info(self, info: dict[str, str]) -> bool:
        try:
            for key, value in info.items():
                self.set(f"company.{key}", value)
            return True
        except (AttributeError, TypeError, ValueError):
            return False


# Instância global
config = Config()


# ------------------------------------------------------------------
# Funções de conveniência
# ------------------------------------------------------------------


def obter_config() -> Config:
    """Retorna a instância global de configuração"""
    return config


def get_config(key: str, default: Any = None) -> Any:
    return config.get(key, default)


def set_config(key: str, value: Any) -> bool:
    return config.set(key, value)


def save_config() -> bool:
    return config.save_config()
