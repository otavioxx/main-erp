import argparse
import base64
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

CHAVE_PUBLICA_ED25519_B64 = "H9gLoB9JOf7ca1NHIfbGeuCOh71sG/h5CjhoivGz8KA="


def assinar(arquivo: Path, chave_privada_pem: bytes) -> bytes:
    chave = serialization.load_pem_private_key(chave_privada_pem, password=None)
    if not isinstance(chave, Ed25519PrivateKey):
        raise ValueError("A chave informada não é uma chave privada Ed25519.")
    chave_publica = chave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if base64.b64encode(chave_publica).decode("ascii") != CHAVE_PUBLICA_ED25519_B64:
        raise ValueError("A chave privada não corresponde à chave pública do launcher.")
    return chave.sign(arquivo.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assina o ZIP da release com a chave Ed25519 privada."
    )
    parser.add_argument("arquivo", type=Path, help="arquivo ZIP da release")
    parser.add_argument(
        "--saida",
        type=Path,
        help="arquivo .sig de saída (padrão: <arquivo>.sig)",
    )
    args = parser.parse_args()

    valor_chave = os.environ.get("MAINERP_ED25519_PRIVATE_KEY")
    if not valor_chave:
        sys.exit(
            "Defina o secret MAINERP_ED25519_PRIVATE_KEY com a chave privada PEM."
        )
    if "-----BEGIN PRIVATE KEY-----" not in valor_chave:
        sys.exit("O secret MAINERP_ED25519_PRIVATE_KEY não contém uma chave PEM válida.")
    if not args.arquivo.is_file():
        sys.exit(f"Pacote não encontrado: {args.arquivo}")

    assinatura = assinar(args.arquivo, valor_chave.encode("utf-8"))
    destino = args.saida or Path(f"{args.arquivo}.sig")
    destino.write_text(base64.b64encode(assinatura).decode("ascii") + "\n")
    print(f"Assinatura Ed25519 criada: {destino}")


if __name__ == "__main__":
    main()
