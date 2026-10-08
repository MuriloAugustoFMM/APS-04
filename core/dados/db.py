"""
db.py — Camada de acesso ao SQLite.

Guarda os metadados de cada "imagem" (real ou sintética) junto com o
thumbnail em formato BLOB (bytes reais, não estimados).

Por que BLOB aqui e não caminho de arquivo:
- São thumbnails pequenos (KB, não a cena completa em alta resolução),
  então o banco não cresce de forma inviável mesmo com 10 mil+ linhas.
- Satisfaz literalmente o requisito do enunciado de ter um campo BLOB
  na tabela.
- Simplifica o projeto: um único arquivo .sqlite contém tudo, sem
  precisar sincronizar banco + pasta de arquivos.
"""

import os
import sqlite3
from contextlib import contextmanager

CAMINHO_BANCO_PADRAO = "data/catalogo_cerrado.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadados_imagem (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_arquivo    TEXT NOT NULL,
    data_captura    TEXT,                 -- ISO 8601, ex: '2023-05-12T13:40:00'
    satelite        TEXT,
    sensor          TEXT,
    latitude        REAL,
    longitude       REAL,
    tamanho_bytes   INTEGER NOT NULL,      -- len(thumbnail_blob), medido de verdade
    thumbnail_blob  BLOB NOT NULL,
    origem          TEXT NOT NULL CHECK(origem IN ('real', 'sintetico')),
    criado_em       TEXT DEFAULT (datetime('now'))
);

-- Índices nos campos que vamos usar como chave de ordenação com mais frequência
CREATE INDEX IF NOT EXISTS idx_data_captura  ON metadados_imagem(data_captura);
CREATE INDEX IF NOT EXISTS idx_tamanho_bytes ON metadados_imagem(tamanho_bytes);
"""


@contextmanager
def conectar(caminho_banco: str = CAMINHO_BANCO_PADRAO):
    """
    Context manager simples: abre a conexão, garante commit no final
    (ou rollback se der erro), e fecha a conexão sempre.
    Uso:
        with conectar() as conn:
            ...
    """
    pasta = os.path.dirname(caminho_banco)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    conn = sqlite3.connect(caminho_banco)
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_banco(caminho_banco: str = CAMINHO_BANCO_PADRAO) -> None:
    """Cria a tabela e os índices caso ainda não existam."""
    with conectar(caminho_banco) as conn:
        conn.executescript(SCHEMA)


def inserir_registro(conn: sqlite3.Connection, registro: dict) -> int:
    """
    Insere um registro de metadado + thumbnail.

    `registro` deve conter as chaves:
    nome_arquivo, data_captura, satelite, sensor, latitude, longitude,
    tamanho_bytes, thumbnail_blob, origem.

    Retorna o id gerado.
    """
    cursor = conn.execute(
        """
        INSERT INTO metadados_imagem
            (nome_arquivo, data_captura, satelite, sensor,
             latitude, longitude, tamanho_bytes, thumbnail_blob, origem)
        VALUES (:nome_arquivo, :data_captura, :satelite, :sensor,
                :latitude, :longitude, :tamanho_bytes, :thumbnail_blob, :origem)
        """,
        registro,
    )
    return cursor.lastrowid


def contar_registros(conn: sqlite3.Connection, origem: str | None = None) -> int:
    """Conta quantos registros existem, opcionalmente filtrando por origem."""
    if origem:
        cur = conn.execute(
            "SELECT COUNT(*) FROM metadados_imagem WHERE origem = ?", (origem,)
        )
    else:
        cur = conn.execute("SELECT COUNT(*) FROM metadados_imagem")
    return cur.fetchone()[0]


def buscar_todos(conn: sqlite3.Connection, incluir_blob: bool = False) -> list[dict]:
    """
    Carrega os registros em memória como lista de dicts — é essa lista
    que vai alimentar os algoritmos de ordenação (a carga dos dados do
    banco NÃO entra na medição de tempo do benchmark, só a chamada do
    sort em cima dessa lista já carregada).

    incluir_blob=False por padrão: pra ordenar não precisamos do
    thumbnail em si, só dos metadados — carregar o BLOB de 10 mil
    linhas em memória sem necessidade só deixaria o benchmark mais lento
    por motivo errado (I/O, não o algoritmo).
    """
    colunas = "id, nome_arquivo, data_captura, satelite, sensor, latitude, longitude, tamanho_bytes, origem"
    if incluir_blob:
        colunas += ", thumbnail_blob"
    cur = conn.execute(f"SELECT {colunas} FROM metadados_imagem")
    return [dict(row) for row in cur.fetchall()]
