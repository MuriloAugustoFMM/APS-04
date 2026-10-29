"""
api_inpe.py — Busca cenas do Cerrado Goiano no catálogo STAC do INPE e baixa os thumbnails (PNG).

Fluxo: buscar_itens() -> extrair_metadados() + baixar_thumbnail()
"""

import requests

from core.dados.imagens import detectar_mime

STAC_BASE_URL = "https://data.inpe.br/bdc/stac/v1"
BBOX_CERRADO_GO = (-50.5, -19.0, -46.0, -13.0)  # (lon_min, lat_min, lon_max, lat_max)
HEADERS = {"User-Agent": "APS-UniversidadeGrupo/1.0 (uso academico)"}

# id da coleção -> (satélite, sensor). Só coleções que têm thumbnail PNG.
COLECOES_CERRADO = {
    "S2_L1C_BUNDLE-1": ("SENTINEL-2", "MSI"),
    "CB4-MUX-L4-DN-1": ("CBERS-4", "MUX"),
    "AMZ1-WFI-L2-DN-1": ("AMAZONIA-1", "WFI"),
}
MAX_LADO_CENA_GRAUS = 12.0

# Sessão HTTP: reaproveita a conexão entre os downloads (muito mais rápido
# do que abrir uma conexão nova para cada thumbnail).
SESSAO = requests.Session()
SESSAO.headers.update(HEADERS)


def cena_pertence_ao_cerrado(item, bbox=BBOX_CERRADO_GO, max_lado=MAX_LADO_CENA_GRAUS) -> bool:
    """Funil: descarta cena gigante (produto global) e cena com o centro fora do Cerrado."""
    caixa = item.get("bbox")
    if not caixa or len(caixa) != 4:
        return False
    min_lon, min_lat, max_lon, max_lat = caixa
    if (max_lon - min_lon) > max_lado or (max_lat - min_lat) > max_lado:
        return False
    lon, lat = (min_lon + max_lon) / 2, (min_lat + max_lat) / 2
    return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]


def _buscar_colecao(colecao, bbox, data_inicio, data_fim, maximo):
    """Busca UMA coleção, seguindo o link 'next' de cada página."""
    url = f"{STAC_BASE_URL}/search"
    params = {
        "collections": colecao,  # sem isso vêm cenas de qualquer coleção (radar, GOES...)
        "bbox": ",".join(str(c) for c in bbox),
        "datetime": f"{data_inicio}T00:00:00Z/{data_fim}T23:59:59Z",
        "limit": 500,
    }
    aceitos, vistos = [], set()
    while url and len(aceitos) < maximo:
        resp = SESSAO.get(url, params=params, timeout=30)
        resp.raise_for_status()
        corpo = resp.json()
        features = corpo.get("features", [])
        if not features:
            break
        for item in features:
            if item.get("id") not in vistos and cena_pertence_ao_cerrado(item, bbox):
                vistos.add(item.get("id"))
                aceitos.append(item)
        url = next((l["href"] for l in corpo.get("links", []) if l.get("rel") == "next"), None)
        params = None  # o link 'next' já traz os filtros
    return aceitos[:maximo]


def buscar_itens(bbox=BBOX_CERRADO_GO, data_inicio="2020-01-01", data_fim="2024-12-31",
                 collections=None, maximo_itens=5000):
    """Cenas do Cerrado. Busca coleção por coleção e só passa para a próxima se faltar cena."""
    itens = []
    for colecao in (collections or COLECOES_CERRADO):
        faltam = maximo_itens - len(itens)
        itens.extend(_buscar_colecao(colecao, bbox, data_inicio, data_fim, faltam))
        if len(itens) >= maximo_itens:
            break
    return itens[:maximo_itens]


def extrair_metadados(item) -> dict:
    """Transforma o JSON da cena nos campos da nossa tabela."""
    props = item.get("properties", {})
    sat_padrao, sensor_padrao = COLECOES_CERRADO.get(item.get("collection", ""), (None, None))
    min_lon, min_lat, max_lon, max_lat = item["bbox"]
    instrumentos = props.get("instruments") or []
    return {
        "nome_arquivo": item.get("id", "desconhecido"),
        "data_captura": props.get("datetime") or props.get("start_datetime"),
        "satelite": props.get("platform") or props.get("platformShortName")
                    or sat_padrao or item.get("collection") or "desconhecido",
        "sensor": (instrumentos[0] if instrumentos else None)
                  or props.get("instrumentShortName") or sensor_padrao,
        "latitude": (min_lat + max_lat) / 2,
        "longitude": (min_lon + max_lon) / 2,
    }


def baixar_thumbnail(item) -> bytes | None:
    """Bytes do PNG do thumbnail, ou None (sem thumbnail, erro de rede ou não é imagem)."""
    asset = item.get("assets", {}).get("thumbnail")  # NUNCA "asset": é o .zip de ~1 GB
    if not (asset and asset.get("href")):
        return None
    try:
        resp = SESSAO.get(asset["href"], timeout=30)
        resp.raise_for_status()
    except requests.RequestException as erro:
        print(f"  falha ao baixar thumbnail de {item.get('id')}: {erro}")
        return None
    return resp.content if detectar_mime(resp.content) else None
