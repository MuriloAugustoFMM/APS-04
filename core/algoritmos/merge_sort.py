"""
merge_sort.py — Ordenação por intercalação (divisão e conquista).

Complexidade: O(n log n) garantido em qualquer caso (melhor, médio e
pior) — é o preço de ser mais previsível: sempre divide a lista ao meio,
sempre intercala. É estável (elementos com chaves iguais mantêm a ordem
relativa original), o que o conecta bem com o tema de "ordenação externa"
citado no enunciado — é a base de algoritmos que ordenam arquivos maiores
que a memória disponível, juntando pedaços já ordenados.

Interface: igual à de bubble_sort.py (sort(dados, key) -> list, não mutante).
"""


def sort(dados: list, key=lambda x: x) -> list:
    lista = dados.copy()

    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2
    esquerda = sort(lista[:meio], key)
    direita = sort(lista[meio:], key)

    return _intercalar(esquerda, direita, key)


def _intercalar(esquerda: list, direita: list, key) -> list:
    """Combina duas listas já ordenadas em uma só, ordenada."""
    resultado = []
    i = j = 0

    while i < len(esquerda) and j < len(direita):
        # <= (não <) garante estabilidade: em caso de empate, o elemento
        # da esquerda (que veio antes na lista original) entra primeiro
        if key(esquerda[i]) <= key(direita[j]):
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1

    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])
    return resultado
