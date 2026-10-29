"""
importar_sqlite.py — Copia as linhas de um banco SQLite antigo para o MySQL.

Serve para reaproveitar o .sqlite que já foi baixado, sem baixar tudo do INPE de novo:

  python -m core.dados.importar_sqlite data/catalogo_cerrado.sqlite

Só copia se a tabela do MySQL estiver vazia (para não duplicar). Linhas sintéticas do banco antigo são ignoradas.
"""

import os
import sqlite3
import sys

from core.dados import db

COLUNAS = ("nome_arquivo", "data_captura", "satelite", "sensor", "latitude", "longitude",
           "tamanho_bytes", "thumbnail_blob", "origem")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python -m core.dados.importar_sqlite caminho/do/arquivo.sqlite")

    if not os.path.exists(sys.argv[1]):
        raise SystemExit(f"Arquivo não encontrado: {sys.argv[1]}")
    antigo = sqlite3.connect(sys.argv[1])
    linhas = antigo.execute(f"SELECT {', '.join(COLUNAS)} FROM metadados_imagem WHERE origem IN ('real', 'manual') ORDER BY id").fetchall()
    antigo.close()

    with db.conectar() as conn:
        if db.contar(conn):
            raise SystemExit("A tabela do MySQL já tem registros; nada foi copiado.")
        for i, linha in enumerate(linhas, 1):
            db.inserir(conn, dict(zip(COLUNAS, linha)))
            if i % 500 == 0:
                conn.commit()
                print(f"  {i}/{len(linhas)}")
        print(f"Pronto: {len(linhas)} registros copiados para o MySQL.")


if __name__ == "__main__":
    main()
