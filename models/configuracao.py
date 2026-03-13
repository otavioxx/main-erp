#\erp\model\configuracao.py
import json
import os
from typing import Any, Dict

class configuracao:
    """Classe para gerenciar configurações do sistema"""

    def __init__(self, config_file: str = 'configuracao.json'):
        self.config_file = config_file
        self.default_config = {
            'database': {
                'name': 'erp.db',
                'timezone': '-03:00'
            },
            'appearance': {
                'theme': 'dark',
                'font_family': 'Segoe UI',
                'font_size': 9,
                'accent_color': '#007acc'
            },
            'company': {
                'name': '',
                'cnpj': '',
                'address': '',
                'phone': '',
                'email': '',
                'logo_path': ''
            },
            'sales': {
                'default_payment_method': 'dinheiro',
                'enable_installments': True,
                'max_installments': 12,
                'default_installments': 1
            },
            'inventory': {
                'low_stock_threshold': 10,
                'enable_stock_control': True,
                'notify_low_stock': True
            },
            'security': {
                'password_required': False,
                'auto_logout_minutes': 30,
                'max_login_attempts': 3
            },
            'reports': {
                'default_report_path': 'relatorios',
                'auto_generate_sales_report': True,
                'report_format': 'pdf'
            }
        }
        self.configuracao = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Carrega as configurações do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.default_config.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar configurações: {e}")
            return self.default_config.copy()

    def save_config(self) -> bool:
        """Salva as configurações no arquivo JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configuracao, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erro ao salvar configurações: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração usando notação de ponto"""
        keys = key.split('.')
        value = self.configuracao

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        """Define um valor de configuração usando notação de ponto"""
        keys = key.split('.')
        config_ref = self.configuracao

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
        self.configuracao = self.default_config.copy()
        return self.save_config()

    def get_database_path(self) -> str:
        """Retorna o caminho completo do banco de dados"""
        db_name = self.get('database.name', 'erp.db')
        return db_name

    def get_report_path(self) -> str:
        """Retorna o caminho completo para relatórios"""
        report_path = self.get('reports.default_report_path', 'relatorios')
        return report_path

    def get_company_info(self) -> Dict[str, str]:
        """Retorna informações da empresa"""
        return {
            'name': self.get('company.name', ''),
            'cnpj': self.get('company.cnpj', ''),
            'address': self.get('company.address', ''),
            'phone': self.get('company.phone', ''),
            'email': self.get('company.email', '')
        }

    def set_company_info(self, info: Dict[str, str]) -> bool:
        """Define informações da empresa"""
        try:
            for key, value in info.items():
                self.set(f'company.{key}', value)
            return True
        except Exception:
            return False

configuracao = configuracao()

def get_config(key: str, default: Any = None) -> Any:
    return configuracao.get(key, default)

def set_config(key: str, value: Any) -> bool:
    return configuracao.set(key, value)

def save_config() -> bool:
    return configuracao.save_config()