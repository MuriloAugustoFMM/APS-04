"""
api_inpe.py — Integração com o Catálogo Integrado de Imagens do INPE (API STAC).

Documentação: https://data.inpe.br/bdc/web/
Base da API:  https://data.inpe.br/bdc/stac/v1/

Fluxo:
1. listar_colecoes()   -> confirma quais coleções (satélites/sensores)
                           estão disponíveis AGORA (isso muda com o tempo,
                           não deixe fixo sem checar).
2. buscar_itens()      -> busca as cenas dentro do bbox/período, com
                           paginação automática.
3. baixar_thumbnail()  -> baixa os bytes reais do thumbnail de um item.
"""

import time
import requests

STAC_BASE_URL = "https://data.inpe.br/bdc/stac/v1"

# Bbox aproximado cobrindo o Cerrado Goiano / bioma Cerrado em GO
# (min_lon, min_lat, max_lon, max_lat)
BBOX_CERRADO_GO = (-50.5, -19.0, -46.0, -13.0)

# User-Agent decente evita bloqueio por alguns servidores que recusam
# requests "anônimos"
HEADERS = {"User-Agent": "APS-UniversidadeGrupo/1.0 (uso academico)"}


def listar_colecoes() -> list[dict]:
    """
    Retorna a lista de coleções disponíveis no catálogo (id, título,
    descrição). Rode isso primeiro pra saber quais ids usar em
    `buscar_itens(collections=[...])` — os nomes mudam com o tempo.
    """
    resp = requests.get(f"{STAC_BASE_URL}/collections", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json().get("collections", [])


def buscar_itens(
    bbox: tuple = BBOX_CERRADO_GO,
    data_inicio: str = "2020-01-01",
    data_fim: str = "2024-12-31",
    collections: list[str] | None = None,
    limite_por_pagina: int = 100,
    maximo_itens: int = 5000,
    pausa_entre_paginas: float = 0.3,
) -> list[dict]:
    """
    Busca itens (cenas) no catálogo STAC, paginando automaticamente até
    `maximo_itens` ou até acabarem os resultados.

    maximo_itens funciona como um teto de segurança: a quantidade real
    disponível depende do que o INPE tem catalogado pro bbox/período
    escolhidos, pode vir bem menor que isso — é esperado, é o "real" do
    dataset misto (o restante até 10 mil a gente completa com sintético).
    """
    params = {
        "bbox": ",".join(str(c) for c in bbox),
        "datetime": f"{data_inicio}T00:00:00Z/{data_fim}T23:59:59Z",
        "limit": limite_por_pagina,
    }
    if collections:
        params["collections"] = ",".join(collections)

    itens_coletados: list[dict] = []
    url = f"{STAC_BASE_URL}/search"

    while url and len(itens_coletados) < maximo_itens:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        corpo = resp.json()

        itens_coletados.extend(corpo.get("features", []))
        print(f"  coletados até agora: {len(itens_coletados)}")

        # STAC usa um link com rel="next" pra paginação — procura ele
        proximo = next(
            (link["href"] for link in corpo.get("links", []) if link.get("rel") == "next"),
            None,
        )
        url = proximo
        params = {}  # a url 'next' já vem com os query params embutidos
        time.sleep(pausa_entre_paginas)  # não martela o servidor

    return itens_coletados[:maximo_itens]


def extrair_metadados(item: dict) -> dict:
    """
    Normaliza um item STAC bruto (JSON) nos campos que nossa tabela usa.
    """
    props = item.get("properties", {})
    bbox = item.get("bbox", [None, None, None, None])
    # centro aproximado do bbox como lat/lon do registro
    longitude = (bbox[0] + bbox[2]) / 2 if bbox[0] is not None else None
    latitude = (bbox[1] + bbox[3]) / 2 if bbox[1] is not None else None

    return {
        "nome_arquivo": item.get("id", "desconhecido"),
        "data_captura": props.get("datetime"),
        "satelite": props.get("platform", "desconhecido"),
        "sensor": props.get("instruments", [None])[0] if props.get("instruments") else None,
        "latitude": latitude,
        "longitude": longitude,
    }


def baixar_thumbnail(item: dict) -> bytes | None:
    """
    Baixa os bytes reais do thumbnail/preview de um item STAC.
    Tenta algumas chaves de asset comuns, porque isso varia entre coleções.
    Retorna None se o item não tiver nenhum asset de preview baixável.
    """
    assets = item.get("assets", {})
    for chave in ("thumbnail", "preview", "browse", "rendered_preview"):
        asset = assets.get(chave)
        if asset and asset.get("href"):
            try:
                resp = requests.get(asset["href"], headers=HEADERS, timeout=30)
                resp.raise_for_status()
                return resp.content
            except requests.RequestException as erro:
                print(f"  falha ao baixar thumbnail de {item.get('id')}: {erro}")
                return None
    return None
