"""
app.py — API Flask que expõe o core (banco + algoritmos) para o frontend web.

Rotas:
  GET /api/imagens      -> lista paginada de imagens (metadados + thumbnail em base64)
                            já ordenada pelo algoritmo e campo escolhidos
  GET /api/benchmark     -> roda os 5 algoritmos sobre um dataset de tamanho N
                            e devolve os tempos, para montar o gráfico comparativo
  GET /                  -> serve o frontend estático (static/index.html)

Rodar (a partir da raiz do projeto):
    python app.py
Depois acessar http://localhost:5000
"""

import base64
import random
import time

from flask import Flask, jsonify, request, send_from_directory

from core.algoritmos import bubble_sort, insertion_sort, merge_sort, quick_sort, radix_sort
from core.dados import db

app = Flask(__name__, static_folder="static", static_url_path="")

ALGORITMOS = {
    "bubble": bubble_sort,
    "insertion": insertion_sort,
    "merge": merge_sort,
    "quick": quick_sort,
    "radix": radix_sort,
}

CAMPOS_PERMITIDOS = {"tamanho_bytes", "data_captura", "nome_arquivo", "satelite"}


# ---------------------------------------------------------------------------
# Frontend estático
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# API: imagens
# ---------------------------------------------------------------------------

@app.route("/api/imagens")
def listar_imagens():
    """
    Query params:
      pagina        (int, padrão 1)
      por_pagina    (int, padrão 20, máximo 100)
      ordenar_por   (um de CAMPOS_PERMITIDOS, padrão 'tamanho_bytes')
      algoritmo     (um de ALGORITMOS, padrão 'quick')
    """
    pagina = max(int(request.args.get("pagina", 1)), 1)
    por_pagina = min(int(request.args.get("por_pagina", 20)), 100)
    ordenar_por = request.args.get("ordenar_por", "tamanho_bytes")
    algoritmo_nome = request.args.get("algoritmo", "quick")

    if ordenar_por not in CAMPOS_PERMITIDOS:
        return jsonify({"erro": f"campo inválido. use um de: {sorted(CAMPOS_PERMITIDOS)}"}), 400
    if algoritmo_nome not in ALGORITMOS:
        return jsonify({"erro": f"algoritmo inválido. use um de: {sorted(ALGORITMOS)}"}), 400
    if algoritmo_nome == "radix" and ordenar_por != "tamanho_bytes":
        return jsonify({"erro": "radix só ordena por 'tamanho_bytes' (chave inteira)"}), 400

    with db.conectar() as conn:
        # Visualização mostra SOMENTE imagens reais (baixadas de verdade do
        # INPE) — os registros sintéticos existem apenas para dar volume ao
        # benchmark de ordenação, nunca são exibidos como se fossem imagem.
        registros = [r for r in db.buscar_todos(conn, incluir_blob=False) if r["origem"] == "real"]

        modulo = ALGORITMOS[algoritmo_nome]
        ordenados = modulo.sort(registros, key=lambda r: r[ordenar_por])

        total = len(ordenados)
        inicio = (pagina - 1) * por_pagina
        pagina_atual = ordenados[inicio: inicio + por_pagina]

        ids_pagina = [r["id"] for r in pagina_atual]
        thumbs = _buscar_thumbnails_por_id(conn, ids_pagina)

    itens = []
    for r in pagina_atual:
        item = dict(r)
        blob = thumbs.get(r["id"])
        item["thumbnail_base64"] = base64.b64encode(blob).decode("ascii") if blob else None
        itens.append(item)

    return jsonify({
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": total,
        "total_paginas": (total + por_pagina - 1) // por_pagina,
        "ordenar_por": ordenar_por,
        "algoritmo": algoritmo_nome,
        "itens": itens,
    })


def _buscar_thumbnails_por_id(conn, ids: list[int]) -> dict:
    if not ids:
        return {}
    marcadores = ",".join("?" for _ in ids)
    cur = conn.execute(
        f"SELECT id, thumbnail_blob FROM metadados_imagem WHERE id IN ({marcadores})",
        ids,
    )
    return {row["id"]: row["thumbnail_blob"] for row in cur.fetchall()}


# ---------------------------------------------------------------------------
# API: benchmark
# ---------------------------------------------------------------------------

@app.route("/api/benchmark")
def rodar_benchmark():
    """
    Query params:
      tamanho   (int, padrão 1000) quantidade de registros usados no teste
      campo     (um de CAMPOS_PERMITIDOS, padrão 'tamanho_bytes')
      cenario   'aleatorio' | 'ordenado' | 'invertido' (padrão 'aleatorio')

    Mede só o tempo da chamada sort() — os dados já vêm carregados do banco
    antes de cronometrar, como exige o enunciado da APS.
    """
    tamanho = min(int(request.args.get("tamanho", 1000)), 10000)
    campo = request.args.get("campo", "tamanho_bytes")
    cenario = request.args.get("cenario", "aleatorio")

    if campo not in CAMPOS_PERMITIDOS:
        return jsonify({"erro": f"campo inválido. use um de: {sorted(CAMPOS_PERMITIDOS)}"}), 400

    with db.conectar() as conn:
        registros = db.buscar_todos(conn, incluir_blob=False)

    if len(registros) < tamanho:
        tamanho = len(registros)
    base = registros[:tamanho]

    if cenario == "ordenado":
        base = sorted(base, key=lambda r: r[campo])
    elif cenario == "invertido":
        base = sorted(base, key=lambda r: r[campo], reverse=True)
    elif cenario == "aleatorio":
        base = base.copy()
        random.shuffle(base)
    else:
        return jsonify({"erro": "cenario inválido. use: aleatorio, ordenado ou invertido"}), 400

    resultados = {}
    for nome, modulo in ALGORITMOS.items():
        if nome == "radix" and campo != "tamanho_bytes":
            continue  # radix não serve pra chaves não-inteiras, pula
        inicio = time.perf_counter()
        modulo.sort(base, key=lambda r: r[campo])
        resultados[nome] = round(time.perf_counter() - inicio, 6)

    return jsonify({
        "tamanho": tamanho,
        "campo": campo,
        "cenario": cenario,
        "tempos_segundos": resultados,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
