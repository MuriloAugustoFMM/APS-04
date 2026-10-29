"""
db.py — Conexão com o MySQL e as operações da tabela (inserir, listar, editar, apagar).

Uma tabela só: metadados_imagem. O thumbnail fica na coluna thumbnail_blob (BLOB = os
bytes da imagem guardados dentro do próprio banco).

Os dados de conexão têm padrão de XAMPP/WAMP (usuário root, sem senha, porta 3306).
Para mudar, defina variáveis de ambiente antes de rodar:
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

O banco (database) é criado sozinho se não existir. Dá para ver as tabelas e linhas
pelo phpMyAdmin: http://localhost/phpmyadmin
"""

import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
}
NOME_BANCO = os.environ.get("MYSQL_DATABASE", "catalogo_cerrado")

# CREATE TABLE IF NOT EXISTS: cria a tabela só se ela ainda não existir.
#   INT AUTO_INCREMENT PRIMARY KEY  -> id numérico que o próprio MySQL numera (1, 2, 3...)
#   VARCHAR(n)                      -> texto de até n caracteres
#   DOUBLE                          -> número com casas decimais (latitude/longitude)
#   MEDIUMBLOB                      -> bytes de até 16 MB (um BLOB comum guarda só 64 KB)
#   ENUM(...)                       -> a coluna só aceita um dos valores da lista. É o que diz
#                                      de onde veio a linha: real (INPE) ou manual (cadastrada pelo CRUD)
#   TIMESTAMP DEFAULT CURRENT_TIMESTAMP -> data/hora preenchida sozinha no INSERT
#   utf8mb4                         -> codificação que aceita acentos e qualquer caractere
SCHEMA = """
CREATE TABLE IF NOT EXISTS metadados_imagem (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome_arquivo    VARCHAR(255) NOT NULL,
    data_captura    VARCHAR(40),
    satelite        VARCHAR(100),
    sensor          VARCHAR(100),
    latitude        DOUBLE,
    longitude       DOUBLE,
    tamanho_bytes   INT NOT NULL,
    thumbnail_blob  MEDIUMBLOB NOT NULL,
    origem          ENUM('real', 'manual') NOT NULL,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

CAMPOS_EDITAVEIS = ("nome_arquivo", "data_captura", "satelite", "sensor", "latitude", "longitude")

# Todas as colunas menos o BLOB: listar milhares de linhas sem carregar as imagens é bem mais rápido.
# CAST(criado_em AS CHAR) transforma a data em texto ('2026-10-25 15:07:18'), que o JSON entende.
COLUNAS = ("id, nome_arquivo, data_captura, satelite, sensor, latitude, longitude, "
           "tamanho_bytes, origem, CAST(criado_em AS CHAR) AS criado_em")


@contextmanager
def conectar(banco=NOME_BANCO):
    """Abre o banco, salva (commit) no final e fecha. Uso: with conectar() as conn: ..."""
    conn = pymysql.connect(**CONFIG, charset="utf8mb4", cursorclass=DictCursor)
    try:
        with conn.cursor() as cur:
            # Crases (`) protegem o nome do banco. USE escolhe em qual banco os comandos vão rodar.
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{banco}` CHARACTER SET utf8mb4")
            cur.execute(f"USE `{banco}`")
            cur.execute(SCHEMA)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _executar(conn, sql, params=()):
    """Roda um comando. Os %s do SQL são preenchidos com 'params' (evita SQL injection)."""
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def inserir(conn, registro: dict) -> int:
    """INSERT INTO: adiciona uma linha. Devolve o id que o MySQL deu a ela."""
    cur = _executar(
        conn,
        """INSERT INTO metadados_imagem
           (nome_arquivo, data_captura, satelite, sensor, latitude, longitude,
            tamanho_bytes, thumbnail_blob, origem)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (registro["nome_arquivo"], registro.get("data_captura"), registro.get("satelite"),
         registro.get("sensor"), registro.get("latitude"), registro.get("longitude"),
         registro["tamanho_bytes"], registro["thumbnail_blob"], registro["origem"]),
    )
    return cur.lastrowid


def contar(conn) -> int:
    """SELECT COUNT(*): quantas linhas existem na tabela."""
    cur = _executar(conn, "SELECT COUNT(*) AS total FROM metadados_imagem")
    return cur.fetchone()["total"]


def listar_todos(conn) -> list[dict]:
    """SELECT: todas as linhas (sem o BLOB), como lista de dicionários. É isto que vai para os algoritmos."""
    cur = _executar(conn, f"SELECT {COLUNAS} FROM metadados_imagem")
    return cur.fetchall()


def listar_pagina(conn, pagina: int, por_pagina: int):
    """Uma página de linhas, as mais novas primeiro. LIMIT = quantas; OFFSET = quantas pular."""
    cur = _executar(
        conn,
        f"SELECT {COLUNAS} FROM metadados_imagem ORDER BY id DESC LIMIT %s OFFSET %s",
        (por_pagina, (pagina - 1) * por_pagina),
    )
    return cur.fetchall(), contar(conn)


def obter(conn, id_: int):
    cur = _executar(conn, f"SELECT {COLUNAS} FROM metadados_imagem WHERE id = %s", (id_,))
    return cur.fetchone()  # None se não existir


def obter_thumbnail(conn, id_: int):
    cur = _executar(conn, "SELECT thumbnail_blob FROM metadados_imagem WHERE id = %s", (id_,))
    linha = cur.fetchone()
    return linha["thumbnail_blob"] if linha else None


def criar(conn, campos: dict, imagem: bytes) -> int:
    """Cadastro pelo CRUD: o tamanho vem da própria imagem e a origem é 'manual'."""
    return inserir(conn, {**campos, "tamanho_bytes": len(imagem), "thumbnail_blob": imagem, "origem": "manual"})


def atualizar(conn, id_: int, campos: dict, imagem: bytes | None = None) -> bool:
    """
    UPDATE ... SET ... WHERE id = %s: muda só os campos informados. False se o id não existe.
    Se vier uma imagem nova, troca também o thumbnail_blob e recalcula o tamanho_bytes.
    """
    campos = {k: v for k, v in campos.items() if k in CAMPOS_EDITAVEIS}
    if imagem is not None:
        campos["thumbnail_blob"] = imagem
        campos["tamanho_bytes"] = len(imagem)
    if campos:
        trecho = ", ".join(f"{k} = %s" for k in campos)  # nomes vêm de lista fixa, nunca do usuário
        _executar(conn, f"UPDATE metadados_imagem SET {trecho} WHERE id = %s", (*campos.values(), id_))
    return obter(conn, id_) is not None


def deletar(conn, id_: int) -> bool:
    """DELETE FROM ... WHERE id = %s: apaga a linha. False se o id não existia."""
    return _executar(conn, "DELETE FROM metadados_imagem WHERE id = %s", (id_,)).rowcount > 0
