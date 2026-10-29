"""
imagens.py — Confere se uns bytes são mesmo uma imagem (usa a biblioteca Pillow).
Evita gravar no banco uma página de erro (HTML) como se fosse thumbnail.
"""

import io

from PIL import Image

FORMATOS = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}


def detectar_mime(conteudo: bytes) -> str | None:
    """Devolve 'image/png', 'image/jpeg', 'image/gif' ou 'image/webp'; None se não for imagem."""
    try:
        with Image.open(io.BytesIO(conteudo)) as imagem:
            formato = imagem.format
            imagem.verify()
    except Exception:
        return None
    return FORMATOS.get(formato)
