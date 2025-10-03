#\erp\utils\export_utils.py
import os
import subprocess
import sys

class ExportUtils:
    @staticmethod
    def abrir_arquivo(filename: str) -> bool:
        """Abre arquivo de acordo com o sistema operacional"""
        try:
            if not os.path.exists(filename):
                return False

            if os.name == 'nt':  # Windows
                os.startfile(filename)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', filename])
            else:  # Linux e outros
                subprocess.run(['xdg-open', filename])
            return True
        except Exception:
            return False

    @staticmethod
    def validar_caminho(caminho: str) -> str:
        """Valida e cria o caminho se não existir"""
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        return caminho
