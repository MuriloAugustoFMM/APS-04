"""
radix_sort.py — Ordenação por base (Radix Sort, variante LSD - Least
Significant Digit first).

Complexidade: O(d * (n + b)), onde n = quantidade de elementos,
b = base usada (10, aqui) e d = número de dígitos do maior valor.
Na prática, pra chaves com quantidade de dígitos limitada (como
`tamanho_bytes`, que não cresce indefinidamente), isso se comporta como
O(n) — é o algoritmo NÃO-COMPARATIVO do grupo: em nenhum momento ele
compara dois elementos entre si, só olha os dígitos de cada chave.
Essa é a diferença conceitual que vale destacar no Referencial Teórico.

LIMITAÇÃO IMPORTANTE: só funciona com chaves inteiras e não-negativas.
Por isso, no benchmark, Radix Sort só entra nos testes que ordenam por
`tamanho_bytes` (inteiro) — não faz sentido (nem é chamado) pra ordenar
por `data_captura` (string) sem antes convertê-la pra um inteiro
(timestamp), o que é uma limitação real do algoritmo a ser discutida nos
Resultados.

Interface: igual à dos outros (sort(dados, key) -> list, não mutante),
mas com a restrição de key(x) ser sempre um int >= 0.
"""


def sort(dados: list, key=lambda x: x) -> list:
    lista = dados.copy()
    if len(lista) <= 1:
        return lista

    chaves = [key(x) for x in lista]
    if any(c < 0 for c in chaves):
        raise ValueError(
            "radix_sort só suporta chaves inteiras não-negativas. "
            "Converta ou use outro algoritmo para esse campo."
        )

    maior_valor = max(chaves)
    casa_decimal = 1  # 1, 10, 100, 1000... (unidade, dezena, centena...)

    while maior_valor // casa_decimal > 0:
        lista = _contagem_por_digito(lista, key, casa_decimal)
        casa_decimal *= 10

    return lista


def _contagem_por_digito(lista: list, key, casa_decimal: int) -> list:
    """
    Counting sort estável aplicado a um único dígito (unidade, dezena...).
    É o que dá a estabilidade necessária pro Radix Sort funcionar: cada
    passada precisa preservar a ordem relativa definida pelas passadas
    anteriores (dígitos menos significativos já processados).
    """
    n = len(lista)
    saida = [None] * n
    contagem = [0] * 10  # dígitos de 0 a 9

    for item in lista:
        digito = (key(item) // casa_decimal) % 10
        contagem[digito] += 1

    # contagem acumulada -> define a posição final de cada dígito
    for i in range(1, 10):
        contagem[i] += contagem[i - 1]

    # percorre de trás pra frente para manter estabilidade
    for item in reversed(lista):
        digito = (key(item) // casa_decimal) % 10
        contagem[digito] -= 1
        saida[contagem[digito]] = item

    return saida
