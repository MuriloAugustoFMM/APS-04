"""
test_algoritmos.py — Testes unitários para os 5 algoritmos de ordenação.

Rodar com: pytest tests/test_algoritmos.py -v

Todos os algoritmos (exceto radix_sort, que tem teste à parte por causa
da restrição de chave inteira) passam pela MESMA bateria de casos —
isso garante que todos têm o mesmo comportamento esperado, o que é
importante porque o benchmark depois vai compará-los diretamente.
"""

import pytest

from core.algoritmos import bubble_sort, insertion_sort, merge_sort, quick_sort, radix_sort

# Algoritmos que aceitam qualquer tipo de chave (int, float, string...)
ALGORITMOS_GERAIS = [bubble_sort, insertion_sort, merge_sort, quick_sort]

# Registros simulando o que vem do banco (lista de dicts)
REGISTROS_EXEMPLO = [
    {"id": 1, "tamanho_bytes": 500, "nome": "c"},
    {"id": 2, "tamanho_bytes": 100, "nome": "a"},
    {"id": 3, "tamanho_bytes": 300, "nome": "b"},
]


@pytest.mark.parametrize("algoritmo", ALGORITMOS_GERAIS)
class TestAlgoritmosGerais:

    def test_lista_vazia(self, algoritmo):
        assert algoritmo.sort([]) == []

    def test_lista_um_elemento(self, algoritmo):
        assert algoritmo.sort([42]) == [42]

    def test_lista_ja_ordenada(self, algoritmo):
        assert algoritmo.sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_lista_invertida(self, algoritmo):
        assert algoritmo.sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

    def test_lista_com_duplicatas(self, algoritmo):
        assert algoritmo.sort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]

    def test_nao_modifica_lista_original(self, algoritmo):
        original = [5, 3, 1, 4, 2]
        copia_para_comparar = original.copy()
        algoritmo.sort(original)
        assert original == copia_para_comparar, "o algoritmo não deveria mutar a entrada"

    def test_ordena_por_chave_customizada(self, algoritmo):
        resultado = algoritmo.sort(REGISTROS_EXEMPLO, key=lambda r: r["tamanho_bytes"])
        tamanhos = [r["tamanho_bytes"] for r in resultado]
        assert tamanhos == [100, 300, 500]

    def test_ordena_por_string(self, algoritmo):
        resultado = algoritmo.sort(REGISTROS_EXEMPLO, key=lambda r: r["nome"])
        nomes = [r["nome"] for r in resultado]
        assert nomes == ["a", "b", "c"]


class TestMergeSortEstabilidade:
    """Merge Sort precisa ser estável: elementos com chave igual mantêm
    a ordem relativa original."""

    def test_estabilidade(self):
        dados = [("a", 1), ("b", 1), ("c", 0)]
        resultado = merge_sort.sort(dados, key=lambda x: x[1])
        assert resultado == [("c", 0), ("a", 1), ("b", 1)]


class TestRadixSort:
    """Radix Sort só aceita chaves inteiras não-negativas — testes à parte."""

    def test_lista_vazia(self):
        assert radix_sort.sort([]) == []

    def test_lista_ja_ordenada(self):
        assert radix_sort.sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_lista_invertida(self):
        assert radix_sort.sort([500, 300, 100]) == [100, 300, 500]

    def test_ordena_por_chave_customizada(self):
        resultado = radix_sort.sort(REGISTROS_EXEMPLO, key=lambda r: r["tamanho_bytes"])
        tamanhos = [r["tamanho_bytes"] for r in resultado]
        assert tamanhos == [100, 300, 500]

    def test_rejeita_chave_negativa(self):
        with pytest.raises(ValueError):
            radix_sort.sort([-1, 2, 3])
