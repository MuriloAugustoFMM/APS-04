"""
insertion_sort.py — Ordenação por inserção.

Complexidade: O(n²) no pior caso (lista invertida), mas O(n) no melhor
caso (lista já ordenada ou quase) — é o algoritmo que deve se destacar
no cenário "semi-ordenado" do benchmark, em contraste com o Bubble Sort.

Ideia: constrói a lista ordenada aos poucos, pegando um elemento de cada
vez e "inserindo" ele na posição correta entre os já ordenados — como
organizar cartas de baralho na mão.

Interface: igual à de bubble_sort.py (sort(dados, key) -> list, não mutante).
"""


def sort(dados: list, key=lambda x: x) -> list:
    lista = dados.copy()

    for i in range(1, len(lista)):
        atual = lista[i]
        chave_atual = key(atual)
        j = i - 1

        # desloca os elementos maiores que `atual` uma posição à direita
        while j >= 0 and key(lista[j]) > chave_atual:
            lista[j + 1] = lista[j]
            j -= 1

        lista[j + 1] = atual

    return lista
