"""
medir_desempenho.py — Benchmark dos quatro algoritmos (monografia, seção Resultados).

Gera registros com chave tamanho_bytes aleatória (dados internos), prepara os cenários
aleatório / semiordenado / ordenado / invertido, mede só o sort() com time.perf_counter
e grava benchmark/resultados.json. Rode na raiz do projeto:  python -m benchmark.medir_desempenho
"""
import sys, time, random, json, statistics, os
from core.algoritmos import bubble_sort, insertion_sort, merge_sort, quick_sort
ALG = {"Bubble Sort": bubble_sort, "Insertion Sort": insertion_sort, "Merge Sort": merge_sort, "Quick Sort": quick_sort}
random.seed(2026)
# registros sintéticos com o mesmo formato do banco; chave = tamanho_bytes (PNG de miniatura ~ 5 KB a 400 KB)
base = [{"id": i, "tamanho_bytes": random.randint(5_000, 400_000)} for i in range(1, 10001)]
chave = lambda r: r["tamanho_bytes"]
def preparar(n, cen):
    a = random.sample(base, n)
    if cen == "ordenado": a.sort(key=chave)
    elif cen == "invertido": a.sort(key=chave, reverse=True)
    elif cen == "semi":
        a.sort(key=chave)
        for _ in range(max(1, n // 20)):   # 5% de trocas aleatórias
            i, j = random.randrange(n), random.randrange(n); a[i], a[j] = a[j], a[i]
    return a
res = []
for cen in ["aleatorio", "semi", "ordenado", "invertido"]:
    for n in [100, 500, 1000, 2500, 5000, 10000]:
        reps = 5 if n <= 1000 else (3 if n <= 5000 else 2)
        dados = [preparar(n, cen) for _ in range(reps)]
        for nome, mod in ALG.items():
            ts = []
            for d in dados:
                t = time.perf_counter(); out = mod.sort(d, key=chave); ts.append(time.perf_counter() - t)
                assert [chave(x) for x in out] == sorted(chave(x) for x in d)
            res.append({"cenario": cen, "n": n, "algoritmo": nome, "t": statistics.median(ts), "reps": reps})
            print(cen, n, nome, round(res[-1]["t"], 6), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "resultados.json"), "w"), indent=1)
print("FIM")
