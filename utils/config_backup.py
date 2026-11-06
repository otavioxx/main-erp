"""
Utilitário para gerenciar configurações de backup
"""

import json
import os

from paths import caminho_dados


class BackupConfig:
    """Gerencia configurações de backup"""
    
    CONFIG_FILE = "backup_config.json"
    
    @classmethod
    def get_last_backup_path(cls):
        """Retorna o último caminho de backup salvo"""
        config_path = cls._get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('last_backup_path', cls._get_default_path())
            except:
                return cls._get_default_path()
        
        return cls._get_default_path()
    
    @classmethod
    def save_last_backup_path(cls, path):
        """Salva o último caminho de backup"""
        config_path = cls._get_config_path()
        
        # Validar se o caminho existe
        if not os.path.exists(path):
            # Se não existe, usa o diretório pai se existir
            parent = os.path.dirname(path)
            if os.path.exists(parent):
                path = parent
            else:
                # Se o diretório pai também não existe, usa o padrão
                path = cls._get_default_path()
        
        config = {
            'last_backup_path': path,
            'saved_at': os.path.getmtime(cls._get_config_path()) if os.path.exists(config_path) else None
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    @classmethod
    def _get_config_path(cls):
        """Retorna o caminho completo do arquivo de configuração (pasta de dados)"""
        return caminho_dados(cls.CONFIG_FILE)
    
    @staticmethod
    def _get_default_path():
        """Retorna o caminho padrão (Desktop)"""
        return os.path.join(os.path.expanduser("~"), "Desktop")
    
    @classmethod
    def get_backup_history(cls, limit=10):
        """Retorna histórico de backups"""
        config_path = cls._get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('history', [])[:limit]
            except:
                return []
        
        return []
    
    @classmethod
    def add_to_history(cls, backup_path):
        """Adiciona backup ao histórico"""
        config_path = cls._get_config_path()
        config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                config = {}
        
        if 'history' not in config:
            config['history'] = []
        
        # Adiciona novo backup ao início da lista
        backup_info = {
            'path': backup_path,
            'timestamp': os.path.getmtime(backup_path) if os.path.exists(backup_path) else None,
            'size': os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
        }
        
        # Remove duplicados
        config['history'] = [b for b in config['history'] if b.get('path') != backup_path]
        config['history'].insert(0, backup_info)
        
        # Limita o histórico
        config['history'] = config['history'][:20]
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False