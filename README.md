# APS — Ordenação de dados de imagens do Cerrado Goiano

Sistema em Python que cataloga metadados (e thumbnails) de imagens de satélite
do Cerrado Goiano em um banco SQLite e implementa algoritmos de ordenação para
comparar o desempenho entre eles.

**Estado atual:** banco de dados + coleta de dados (API real e sintética), 5 algoritmos
de ordenação com testes, API Flask e frontend estático (tabela de imagens reais +
comparação de desempenho). Diagrama da arquitetura em `docs/diagrama_arquitetura.png`.

## Requisitos

- Python 3.10 ou superior
- Dependências: `pip install -r requirements.txt`

## Rodando o frontend web (Flask)

Após popular o banco (ver seção abaixo), suba o servidor:

```bash
python app.py
```

Acesse http://localhost:5000 no navegador. A tabela de imagens mostra **apenas
registros reais** (baixados de verdade do catálogo do INPE) — os registros
sintéticos servem só para dar volume ao benchmark de algoritmos, nunca aparecem
como imagem na tela.

Para ter imagens reais na galeria, popule o banco no modo `misto` (ver abaixo).

## Como rodar

Todos os comandos devem ser executados **a partir da raiz do projeto** (a pasta
que contém `core/`).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Opção 1 — Banco 100% sintético (não usa internet)

```bash
python -m core.dados.popular_banco sintetico --total 10000 --recriar
```

### Opção 2 — Banco misto (parte real via API do INPE + resto sintético)

```bash
python -m core.dados.popular_banco misto --total 10000 --max-reais 3000 --recriar
```

Baixa até 3000 thumbnails reais do catálogo STAC do INPE (bbox do Cerrado Goiano)
e completa o restante até 10000 com dados sintéticos. Se a API estiver fora do ar
ou sem internet, o script avisa e completa tudo com sintético.

### Opções úteis

| Opção | O que faz |
|---|---|
| `--total N` | Quantidade total de registros (padrão 10000) |
| `--max-reais N` | (só `misto`) Máximo de registros reais a buscar |
| `--recriar` | Apaga o banco existente antes de popular |
| `--banco CAMINHO` | Arquivo .sqlite de destino (padrão `data/catalogo_cerrado.sqlite`) |
| `--tam-min` / `--tam-max` | Faixa de tamanho (bytes) dos thumbnails sintéticos |

> **Espaço em disco:** com os padrões, 10 mil registros ocupam cerca de 450 MB.
> Para um banco menor, use por exemplo `--tam-max 30000`.

### Verificar o banco

```bash
python -m core.dados.verificar_banco
```

### Rodar os testes

```bash
pytest tests/ -v
```

## Estrutura

```
core/
├── dados/
│   ├── db.py                 # schema SQLite (thumbnail como BLOB) e acesso
│   ├── api_inpe.py           # busca de cenas via API STAC do INPE
│   ├── gerador_sintetico.py  # registros sintéticos com bytes reais
│   ├── popular_banco.py      # CLI: modos sintetico e misto
│   └── verificar_banco.py    # checagem de sanidade
└── algoritmos/               # bubble, insertion, merge, quick, radix
app.py                        # API Flask (/api/imagens, /api/benchmark)
static/                       # frontend: index.html, style.css, app.js
docs/                         # diagrama de arquitetura
tests/                        # testes unitários dos algoritmos
data/                         # onde o .sqlite é criado (ignorado pelo git)
```

## Autores

| Integrante | Responsabilidade |
|---|---|
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |
