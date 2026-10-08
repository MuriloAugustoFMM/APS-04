"""
gerador_sintetico.py — Gera registros sintéticos com bytes REAIS
(conteúdo gerado e medido com len(), nunca um número "chutado").

A faixa de tamanho padrão fica na mesma ordem de grandeza de um
thumbnail de satélite (dezenas de KB). Com os padrões abaixo, 10 mil
registros ocupam em torno de 450 MB no SQLite. Se quiser um banco menor,
reduza com --tam-max no comando de popular o banco.
"""

import os
import random
from datetime import datetime, timedelta

SATELITES_SIMULADOS = [
    ("CBERS-4", "WFI"),
    ("CBERS-4A", "WPM"),
    ("AMAZONIA-1", "WFI"),
    ("LANDSAT-8", "OLI"),
    ("SENTINEL-2", "MSI"),
]

# Faixa padrão de tamanho do thumbnail sintético (bytes)
TAMANHO_MIN_PADRAO = 10_000
TAMANHO_MAX_PADRAO = 80_000

# Bbox aproximado do Cerrado Goiano, pra manter lat/lon plausíveis
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = -50.5, -19.0, -46.0, -13.0


def gerar_registro_sintetico(
    data_min: datetime,
    data_max: datetime,
    tam_min: int = TAMANHO_MIN_PADRAO,
    tam_max: int = TAMANHO_MAX_PADRAO,
) -> dict:
    """Gera um registro sintético completo, pronto para db.inserir_registro()."""
    satelite, sensor = random.choice(SATELITES_SIMULADOS)

    delta_total = (data_max - data_min).days
    data_captura = data_min + timedelta(days=random.randint(0, max(delta_total, 1)))

    conteudo = os.urandom(random.randint(tam_min, tam_max))

    return {
        "nome_arquivo": f"sintetico_{satelite}_{data_captura:%Y%m%d}_{random.randint(100000, 999999)}.jpg",
        "data_captura": data_captura.isoformat(),
        "satelite": satelite,
        "sensor": sensor,
        "latitude": round(random.uniform(LAT_MIN, LAT_MAX), 6),
        "longitude": round(random.uniform(LON_MIN, LON_MAX), 6),
        "tamanho_bytes": len(conteudo),  # medido do conteúdo gerado
        "thumbnail_blob": conteudo,
        "origem": "sintetico",
    }


def gerar_lote(
    quantidade: int,
    data_min: datetime = datetime(2020, 1, 1),
    data_max: datetime = datetime(2024, 12, 31),
    tam_min: int = TAMANHO_MIN_PADRAO,
    tam_max: int = TAMANHO_MAX_PADRAO,
):
    """Generator: produz `quantidade` registros sob demanda (sem manter todos em memória)."""
    for _ in range(quantidade):
        yield gerar_registro_sintetico(data_min, data_max, tam_min, tam_max)
