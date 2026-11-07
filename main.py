import sys

from mainerp.core.paths import preparar_ambiente

preparar_ambiente()

from mainerp.core.app_logging import configurar_logging

configurar_logging()

from mainerp.app import erro_fatal, main


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        erro_fatal("Erro fatal", f"O sistema não conseguiu iniciar:\n{erro}")
        sys.exit(1)
