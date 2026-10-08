"""
quick_sort.py — Ordenação rápida (divisão e conquista, in-place por natureza).

Complexidade: O(n log n) em média — na prática costuma ser o mais rápido
dos comparativos — mas O(n²) no pior caso, que acontece justamente quando
o pivô escolhido é sempre o menor ou maior valor (ex: lista já ordenada
com pivô fixo no primeiro elemento). Por isso usamos um pivô pelo meio,
que mitiga (mas não elimina) esse risco nos cenários de teste.

Ideia: escolhe um "pivô", particiona a lista em (menores, iguais, maiores)
em relação a ele, e ordena cada partição recursivamente.

Interface: igual à de bubble_sort.py (sort(dados, key) -> list, não mutante).
Aqui a não-mutação é natural: cada chamada recursiva já cria novas listas
(menores/iguais/maiores), então o `dados` original nunca é tocado.
"""


def sort(dados: list, key=lambda x: x) -> list:
    if len(dados) <= 1:
        return dados.copy()

    pivo = dados[len(dados) // 2]
    chave_pivo = key(pivo)

    menores = [x for x in dados if key(x) < chave_pivo]
    iguais = [x for x in dados if key(x) == chave_pivo]
    maiores = [x for x in dados if key(x) > chave_pivo]

    return sort(menores, key) + iguais + sort(maiores, key)
