"""
popular_banco.py — Popula o SQLite com os metadados + thumbnails (BLOB).

Dois modos:

  sintetico  -> 100% dados gerados localmente (não usa internet).
  misto      -> parte real (API STAC do INPE, thumbnails baixados) e o
                restante sintético, até completar o total.

Exemplos (rodar da raiz do projeto):

  python -m core.dados.popular_banco sintetico --total 10000
  python -m core.dados.popular_banco misto --total 10000 --max-reais 3000

Opções comuns:
  --banco CAMINHO   arquivo .sqlite (padrão: data/catalogo_cerrado.sqlite)
  --recriar         apaga o banco existente antes de popular
  --tam-min / --tam-max   faixa de tamanho (bytes) dos thumbnails sintéticos
"""

import argparse
import os

import requests

from core.dados import api_inpe, db, gerador_sintetico

COMMIT_A_CADA = 500  # grava em disco de tempos em tempos (não perde tudo se cair no meio)


def popular_com_dados_sinteticos(conn, quantidade: int, tam_min: int, tam_max: int) -> int:
    print(f"Gerando {quantidade} registros sintéticos...")
    inseridos = 0
    for registro in gerador_sintetico.gerar_lote(quantidade, tam_min=tam_min, tam_max=tam_max):
        db.inserir_registro(conn, registro)
        inseridos += 1
        if inseridos % COMMIT_A_CADA == 0:
            conn.commit()
        if inseridos % 1000 == 0:
            print(f"  {inseridos} registros sintéticos inseridos...")
    conn.commit()
    return inseridos


def popular_com_dados_reais(conn, maximo: int) -> int:
    """
    Busca cenas reais na API STAC do INPE e baixa o thumbnail de cada uma.
    Se a API estiver fora do ar / sem internet, avisa e devolve o que
    conseguiu inserir até ali (o restante é completado com sintético).
    """
    inseridos = 0
    try:
        print("Buscando itens (cenas) no catálogo do INPE (bbox do Cerrado Goiano)...")
        itens = api_inpe.buscar_itens(maximo_itens=maximo)
        print(f"  {len(itens)} itens encontrados.")

        for item in itens:
            thumb = api_inpe.baixar_thumbnail(item)
            if thumb is None:
                continue  # item sem thumbnail disponível

            metadados = api_inpe.extrair_metadados(item)
            metadados["tamanho_bytes"] = len(thumb)
            metadados["thumbnail_blob"] = thumb
            metadados["origem"] = "real"
            db.inserir_registro(conn, metadados)
            inseridos += 1

            if inseridos % COMMIT_A_CADA == 0:
                conn.commit()
            if inseridos % 100 == 0:
                print(f"  {inseridos} registros reais inseridos...")
    except requests.RequestException as erro:
        print(f"\n[AVISO] Falha ao acessar a API do INPE: {erro}")
        print("        Seguindo com o que foi baixado até aqui; o resto será sintético.")

    conn.commit()
    return inseridos


def preparar_banco(caminho: str, recriar: bool) -> bool:
    """Cria o banco (ou recria, se pedido). Retorna False se já existe com dados."""
    if recriar and os.path.exists(caminho):
        os.remove(caminho)
        print(f"Banco anterior removido: {caminho}")

    db.inicializar_banco(caminho)
    with db.conectar(caminho) as conn:
        existentes = db.contar_registros(conn)
    if existentes > 0:
        print(f"O banco '{caminho}' já tem {existentes} registros. Nada foi feito.")
        print("Use --recriar para apagar e popular de novo.")
        return False
    return True


def resumo_final(caminho: str) -> None:
    with db.conectar(caminho) as conn:
        total = db.contar_registros(conn)
        reais = db.contar_registros(conn, origem="real")
        sinteticos = db.contar_registros(conn, origem="sintetico")
    tamanho_mb = os.path.getsize(caminho) / (1024 * 1024)
    print(f"\nBanco finalizado: {total} registros ({reais} reais + {sinteticos} sintéticos)")
    print(f"Arquivo: {caminho} ({tamanho_mb:.1f} MB)")


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Popula o banco SQLite de metadados + thumbnails (BLOB)."
    )
    sub = parser.add_subparsers(dest="modo", required=True)

    def adicionar_opcoes_comuns(p):
        p.add_argument("--total", type=int, default=10_000, help="total de registros (padrão: 10000)")
        p.add_argument("--banco", default=db.CAMINHO_BANCO_PADRAO, help="caminho do arquivo .sqlite")
        p.add_argument("--recriar", action="store_true", help="apaga o banco existente antes")
        p.add_argument("--tam-min", type=int, default=gerador_sintetico.TAMANHO_MIN_PADRAO,
                       help="tamanho mínimo (bytes) dos thumbnails sintéticos")
        p.add_argument("--tam-max", type=int, default=gerador_sintetico.TAMANHO_MAX_PADRAO,
                       help="tamanho máximo (bytes) dos thumbnails sintéticos")

    p_sint = sub.add_parser("sintetico", help="100%% dados sintéticos (sem internet)")
    adicionar_opcoes_comuns(p_sint)

    p_misto = sub.add_parser("misto", help="parte real (API do INPE) + resto sintético")
    adicionar_opcoes_comuns(p_misto)
    p_misto.add_argument("--max-reais", type=int, default=3000,
                         help="máximo de registros reais a buscar na API (padrão: 3000)")
    return parser


def main():
    args = montar_parser().parse_args()

    if args.tam_min > args.tam_max:
        raise SystemExit("--tam-min não pode ser maior que --tam-max")

    if not preparar_banco(args.banco, args.recriar):
        return

    with db.conectar(args.banco) as conn:
        total_real = 0
        if args.modo == "misto":
            total_real = popular_com_dados_reais(conn, min(args.max_reais, args.total))
            print(f"Registros reais inseridos: {total_real}")

        faltam = max(args.total - total_real, 0)
        if faltam:
            popular_com_dados_sinteticos(conn, faltam, args.tam_min, args.tam_max)

    resumo_final(args.banco)


if __name__ == "__main__":
    main()
