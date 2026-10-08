"""
bubble_sort.py — Ordenação por bolha.

Complexidade: O(n²) em todos os casos, exceto com a otimização de parar
cedo quando não há mais trocas numa passada (melhor caso O(n) se a lista
já estiver ordenada).

Ideia: a cada passada, percorre a lista comparando pares vizinhos e troca
quando estão fora de ordem. O maior elemento "borbulha" até o fim a cada
passada completa.

Interface comum a todos os algoritmos deste pacote:
    sort(dados: list, key=lambda x: x) -> list

- NÃO modifica a lista original (retorna uma cópia ordenada) — isso é
  importante pro benchmark: cada algoritmo deve receber os mesmos dados
  de entrada, sem um "contaminar" o teste do outro.
- `key` extrai o valor usado na comparação (ex: lambda r: r['tamanho_bytes']),
  permitindo ordenar por qualquer campo do registro sem duplicar código.
"""


def sort(dados: list, key=lambda x: x) -> list:
    lista = dados.copy()
    n = len(lista)

    for i in range(n - 1):
        trocou = False
        for j in range(n - 1 - i):
            if key(lista[j]) > key(lista[j + 1]):
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
                trocou = True
        if not trocou:
            break  # já está ordenada, não precisa das passadas restantes

    return lista
