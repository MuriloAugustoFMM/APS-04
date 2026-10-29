# APS — Ordenação de imagens do Cerrado Goiano (versão de apresentação)

Compara algoritmos de ordenação (Bubble, Insertion, Merge e Quick) usando thumbnails de
satélite do INPE guardados num banco MySQL.

## Pré-requisito: MySQL ligado

Ligue o MySQL (no XAMPP, botão **Start** do MySQL). O banco `catalogo_cerrado` e a tabela
são criados sozinhos. Padrão: usuário `root`, sem senha, porta 3306. Para mudar, defina antes
de rodar as variáveis `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.
Os dados aparecem no phpMyAdmin: http://localhost/phpmyadmin

## Rodar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m core.dados.popular_banco     # baixa 10000 thumbnails + metadados do INPE
python app.py                          # abre em http://localhost:5000
```

Se a tabela já tiver registros, o `popular_banco` não faz nada (para recriar, no phpMyAdmin,
aba SQL: `TRUNCATE TABLE metadados_imagem;`).

Já tem um `.sqlite` baixado? Copie para o MySQL sem baixar de novo:

```bash
python -m core.dados.importar_sqlite data/catalogo_cerrado.sqlite
```

## Páginas

- `/ordenacao` — ordena com um algoritmo, com cronômetro ao vivo e miniaturas
- `/crud` — cadastrar (com imagem), editar (metadados e, se quiser, a imagem) e excluir registros
- `/comparador` — tempo de cada algoritmo (dados aleatórios, pré-ordenados ou invertidos)

Nas duas primeiras, clique numa miniatura para ver a imagem grande (clique fora ou Esc fecha).
É possível ordenar por tamanho, data, nome, satélite ou ID (a ordem de inserção no banco).

## Estrutura

```
app.py                      servidor Flask (páginas + API)
static/                     3 páginas HTML + estilo.css + ampliar.js
core/algoritmos/            os 4 algoritmos de ordenação
core/dados/api_inpe.py      busca e download no INPE
core/dados/db.py            conexão e operações do MySQL
core/dados/popular_banco.py enche o banco
core/dados/importar_sqlite.py copia um .sqlite antigo para o MySQL
```
