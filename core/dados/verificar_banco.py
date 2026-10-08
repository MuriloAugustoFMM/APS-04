"""
verificar_banco.py — Checagem rápida de sanidade após popular o banco.

Rodar com: python -m core.dados.verificar_banco
"""

from core.dados import db


def main():
    with db.conectar() as conn:
        total = db.contar_registros(conn)
        reais = db.contar_registros(conn, origem="real")
        sinteticos = db.contar_registros(conn, origem="sintetico")

        print(f"Total de registros: {total}")
        print(f"  reais:      {reais}")
        print(f"  sintéticos: {sinteticos}")

        cur = conn.execute(
            "SELECT MIN(tamanho_bytes), MAX(tamanho_bytes), AVG(tamanho_bytes) "
            "FROM metadados_imagem"
        )
        minimo, maximo, media = cur.fetchone()
        print(f"\ntamanho_bytes -> min: {minimo}, max: {maximo}, média: {media:.0f}")

        # confere que o BLOB foi salvo de verdade e o tamanho bate com o campo
        cur = conn.execute(
            "SELECT id, tamanho_bytes, LENGTH(thumbnail_blob) AS tamanho_real "
            "FROM metadados_imagem LIMIT 5"
        )
        print("\nAmostra (tamanho_bytes declarado vs. tamanho real do BLOB):")
        for row in cur.fetchall():
            status = "OK" if row["tamanho_bytes"] == row["tamanho_real"] else "DIVERGENTE!"
            print(f"  id={row['id']}: declarado={row['tamanho_bytes']}, "
                  f"real={row['tamanho_real']} [{status}]")


if __name__ == "__main__":
    main()
