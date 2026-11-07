# \erp\utils\export_utils.py
import os
import subprocess
import sys

from app_logging import registrar_excecao


class ExportUtils:
    @staticmethod
    def abrir_arquivo(filename: str) -> bool:
        """Abre arquivo de acordo com o sistema operacional"""
        try:
            if not os.path.exists(filename):
                return False

            if os.name == "nt":  # Windows
                os.startfile(filename)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", filename], check=False)
            else:  # Linux e outros
                subprocess.run(["xdg-open", filename], check=False)
            return True
        except OSError:
            registrar_excecao(
                __name__,
                "Exception handled in ExportUtils.abrir_arquivo in utils/export_utils.py",
            )
            return False

    @staticmethod
    def validar_caminho(caminho: str) -> str:
        """Valida e cria o caminho se não existir"""
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        return caminho
