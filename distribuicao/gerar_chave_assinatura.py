import argparse
import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def caminho_padrao() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".mainerp")
    return Path(base) / "MainERP" / "signing" / "ed25519-private.pem"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera uma chave Ed25519 para assinar releases do MainERP."
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=caminho_padrao(),
        help="arquivo privado PEM (padrão: pasta signing em LOCALAPPDATA)",
    )
    args = parser.parse_args()

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    chave_privada = Ed25519PrivateKey.generate()
    dados_privados = chave_privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with args.saida.open("xb") as arquivo:
        arquivo.write(dados_privados)

    chave_publica = chave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    print(f"Chave privada criada em: {args.saida}")
    print(f"Chave pública Ed25519 (Base64): {base64.b64encode(chave_publica).decode()}")
    print("Não compartilhe, versione ou envie a chave privada ao repositório.")


if __name__ == "__main__":
    main()
