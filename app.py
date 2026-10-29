"""
app.py — Servidor Flask: entrega as 3 páginas HTML e liga os algoritmos aos dados do banco.

Rodar:  python app.py   ->  http://localhost:5000
"""

import os
import random
import time

import pymysql
from flask import Flask, Response, jsonify, redirect, request, send_from_directory

from core.algoritmos import bubble_sort, insertion_sort, merge_sort, quick_sort
from core.dados import db
from core.dados.imagens import detectar_mime

app = Flask(__name__)
app.config["BANCO"] = db.NOME_BANCO
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # imagens enviadas no CRUD: até 5 MB

ALGORITMOS = {
    "bubble": ("Bubble Sort", bubble_sort),
    "insertion": ("Insertion Sort", insertion_sort),
    "merge": ("Merge Sort", merge_sort),
    "quick": ("Quick Sort", quick_sort),
}
CAMPOS = ("tamanho_bytes", "data_captura", "nome_arquivo", "satelite", "id")


class Erro(Exception):
    """Pedido inválido: vira uma resposta 400 com a mensagem."""


@app.errorhandler(Erro)
def _erro(e):
    return jsonify({"erro": str(e)}), 400


@app.errorhandler(413)
def _arquivo_grande(e):
    return jsonify({"erro": "a imagem passa de 5 MB"}), 413


def _banco():
    return db.conectar(app.config["BANCO"])


def _chave(campo):
    """Como ler o valor que será ordenado. Valor vazio (None) vira '' para não quebrar a comparação."""
    if campo in ("tamanho_bytes", "id"):
        return lambda r: r[campo]
    return lambda r: r[campo] or ""


def _validar_ordenacao(algoritmo, campo):
    if algoritmo not in ALGORITMOS:
        raise Erro(f"algoritmo inválido: {algoritmo}")
    if campo not in CAMPOS:
        raise Erro(f"campo inválido: {campo}")


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

@app.route("/")
def inicio():
    return redirect("/ordenacao")


@app.route("/ordenacao")
def pagina_ordenacao():
    return send_from_directory("static", "ordenacao.html")


@app.route("/crud")
def pagina_crud():
    return send_from_directory("static", "crud.html")


@app.route("/comparador")
def pagina_comparador():
    return send_from_directory("static", "comparador.html")


# ---------------------------------------------------------------------------
# Página 1: ordenação com um algoritmo
# ---------------------------------------------------------------------------

@app.route("/api/ordenar")
def ordenar():
    algoritmo = request.args.get("algoritmo", "quick")
    campo = request.args.get("campo", "tamanho_bytes")
    _validar_ordenacao(algoritmo, campo)

    with _banco() as conn:
        registros = db.listar_todos(conn)

    inicio = time.perf_counter()  # o cronômetro mede SÓ o sort(), sem a leitura do banco
    ordenados = ALGORITMOS[algoritmo][1].sort(registros, key=_chave(campo))
    tempo = time.perf_counter() - inicio

    return jsonify({
        "algoritmo": ALGORITMOS[algoritmo][0],
        "campo": campo,
        "quantidade": len(ordenados),
        "tempo_segundos": tempo,
        "itens": ordenados,
    })


# ---------------------------------------------------------------------------
# Página 3: comparador
# ---------------------------------------------------------------------------

@app.route("/api/resumo")
def resumo():
    with _banco() as conn:
        return jsonify({"total": db.contar(conn)})


@app.route("/api/comparar")
def comparar():
    campo = request.args.get("campo", "tamanho_bytes")
    cenario = request.args.get("cenario", "aleatorio")
    try:
        quantidade = int(request.args.get("quantidade", 1000))
    except ValueError:
        raise Erro("quantidade precisa ser um número inteiro")
    if campo not in CAMPOS:
        raise Erro(f"campo inválido: {campo}")
    if cenario not in ("aleatorio", "ordenado", "invertido"):
        raise Erro(f"cenário inválido: {cenario}")

    with _banco() as conn:
        registros = db.listar_todos(conn)
    if not registros:
        raise Erro("o banco está vazio. Rode: python -m core.dados.popular_banco")

    quantidade = max(1, min(quantidade, len(registros)))
    amostra = random.sample(registros, quantidade)  # amostra aleatória do banco
    chave = _chave(campo)
    if cenario == "ordenado":
        amostra.sort(key=chave)                # prepara os dados ANTES de cronometrar
    elif cenario == "invertido":
        amostra.sort(key=chave, reverse=True)

    resultados = []
    for nome, (rotulo, modulo) in ALGORITMOS.items():
        inicio = time.perf_counter()
        modulo.sort(amostra, key=chave)
        resultados.append({"algoritmo": rotulo, "tempo_segundos": time.perf_counter() - inicio})

    return jsonify({"quantidade": quantidade, "campo": campo, "cenario": cenario, "resultados": resultados})


# ---------------------------------------------------------------------------
# Página 2: CRUD
# ---------------------------------------------------------------------------

def _numero(valor, nome):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise Erro(f"{nome} precisa ser um número")


def _campos_do_pedido(dados, obrigatorio):
    """Lê e confere os metadados enviados pelo formulário (dados = request.form ou JSON)."""
    campos = {}
    for nome in db.CAMPOS_EDITAVEIS:
        if nome in dados:
            valor = dados[nome]
            campos[nome] = _numero(valor, nome) if nome in ("latitude", "longitude") else (valor or None)
    if obrigatorio and not campos.get("nome_arquivo"):
        raise Erro("nome_arquivo é obrigatório")
    if "nome_arquivo" in campos and not campos["nome_arquivo"]:
        raise Erro("nome_arquivo não pode ficar vazio")
    return campos


@app.route("/api/registros", methods=["GET"])
def listar_registros():
    id_busca = request.args.get("id", "").strip()
    if id_busca:  # busca por ID: devolve só esse registro (ou lista vazia)
        try:
            id_ = int(id_busca)
        except ValueError:
            raise Erro("o ID precisa ser um número inteiro")
        with _banco() as conn:
            registro = db.obter(conn, id_)
        itens = [registro] if registro else []
        return jsonify({"itens": itens, "total": len(itens), "pagina": 1, "total_paginas": 1})
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except ValueError:
        raise Erro("pagina precisa ser um número inteiro")
    por_pagina = 20
    with _banco() as conn:
        itens, total = db.listar_pagina(conn, pagina, por_pagina)
    return jsonify({"itens": itens, "total": total, "pagina": pagina,
                    "total_paginas": max(1, -(-total // por_pagina))})


@app.route("/api/registros", methods=["POST"])
def criar_registro():
    campos = _campos_do_pedido(request.form, obrigatorio=True)
    arquivo = request.files.get("imagem")
    if not arquivo:
        raise Erro("envie uma imagem")
    imagem = arquivo.read()
    if detectar_mime(imagem) is None:
        raise Erro("o arquivo enviado não é uma imagem válida (PNG, JPEG, GIF ou WEBP)")
    try:
        with _banco() as conn:
            novo_id = db.criar(conn, campos, imagem)
            return jsonify(db.obter(conn, novo_id)), 201
    except (pymysql.err.IntegrityError, pymysql.err.DataError) as erro:
        raise Erro(f"não foi possível gravar: {erro}")


@app.route("/api/registros/<int:id_>", methods=["PUT"])
def editar_registro(id_):
    campos = _campos_do_pedido(request.form, obrigatorio=False)
    arquivo = request.files.get("imagem")
    imagem = arquivo.read() if arquivo and arquivo.filename else None  # imagem nova é opcional
    if imagem is not None and detectar_mime(imagem) is None:
        raise Erro("o arquivo enviado não é uma imagem válida (PNG, JPEG, GIF ou WEBP)")
    with _banco() as conn:
        if not db.atualizar(conn, id_, campos, imagem):
            return jsonify({"erro": "registro não encontrado"}), 404
        return jsonify(db.obter(conn, id_))


@app.route("/api/registros/<int:id_>", methods=["DELETE"])
def apagar_registro(id_):
    with _banco() as conn:
        if not db.deletar(conn, id_):
            return jsonify({"erro": "registro não encontrado"}), 404
    return jsonify({"apagado": id_})


@app.route("/api/imagens/<int:id_>/thumbnail")
def thumbnail(id_):
    with _banco() as conn:
        blob = db.obter_thumbnail(conn, id_)
    mime = detectar_mime(blob) if blob else None
    if mime is None:
        return jsonify({"erro": "sem imagem"}), 404
    resposta = Response(blob, mimetype=mime)
    resposta.headers["Cache-Control"] = "no-cache"  # depois de trocar a imagem, o navegador busca a nova
    return resposta


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
