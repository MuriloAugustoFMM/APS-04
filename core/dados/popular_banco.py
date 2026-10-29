"""
popular_banco.py — Enche o banco MySQL com 10000 thumbnails + metadados do INPE.

  python -m core.dados.popular_banco

Sem parâmetros. Baixa um thumbnail por vez; se a tabela já tiver registros, não faz nada.
"""

import pymysql
import requests

from core.dados import api_inpe, db

TOTAL = 10_000


def baixar_reais(conn, quantidade: int) -> int:
    """Busca cenas no INPE e baixa o thumbnail de cada uma, até juntar `quantidade`."""
    print("Buscando cenas no INPE (Cerrado Goiano)...")
    # pede 20% a mais: algumas cenas podem não ter thumbnail baixável
    cenas = api_inpe.buscar_itens(maximo_itens=quantidade + quantidade // 5 + 1)
    print(f"  {len(cenas)} cenas encontradas. Baixando thumbnails (um por vez)...")

    inseridas = 0
    for cena in cenas:
        if inseridas >= quantidade:
            break
        thumb = api_inpe.baixar_thumbnail(cena)
        if thumb is None:
            continue
        registro = api_inpe.extrair_metadados(cena)
        registro.update(tamanho_bytes=len(thumb), thumbnail_blob=thumb, origem="real")
        db.inserir(conn, registro)
        inseridas += 1
        if inseridas % 500 == 0:
            conn.commit()  # salva de tempos em tempos
        if inseridas % 100 == 0:
            print(f"  {inseridas}/{quantidade} thumbnails baixados")
    return inseridas


def _popular():
    with db.conectar() as conn:
        existentes = db.contar(conn)
        if existentes:
            print(f"O banco '{db.NOME_BANCO}' já tem {existentes} registros. Para recriar, rode no phpMyAdmin (aba SQL): "
                  f"TRUNCATE TABLE metadados_imagem;")
            return
        try:
            total = baixar_reais(conn, TOTAL)
        except requests.RequestException as erro:
            raise SystemExit(f"Não foi possível acessar o INPE: {erro}")
        print(f"Pronto: {total} registros gravados.")
        if total < TOTAL:
            print(f"Atenção: faltaram {TOTAL - total} (cenas sem thumbnail).")


def main():
    try:
        _popular()
    except pymysql.err.OperationalError as erro:
        raise SystemExit(f"Não foi possível conectar ao MySQL: {erro}\n"
                         "Confira se o MySQL está ligado e os dados de conexão em core/dados/db.py.")


if __name__ == "__main__":
    main()
