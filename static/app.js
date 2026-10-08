// app.js — consome a API Flask e preenche a tabela de imagens e o gráfico de benchmark.

const estado = {
  pagina: 1,
  totalPaginas: 1,
};

const elementos = {
  campoOrdenacao: document.getElementById("campo-ordenacao"),
  algoritmoEscolhido: document.getElementById("algoritmo-escolhido"),
  formFiltros: document.getElementById("form-filtros"),
  statusImagens: document.getElementById("status-imagens"),
  corpoTabela: document.getElementById("corpo-tabela"),
  btnAnterior: document.getElementById("btn-anterior"),
  btnProxima: document.getElementById("btn-proxima"),
  infoPagina: document.getElementById("info-pagina"),

  formBenchmark: document.getElementById("form-benchmark"),
  benchTamanho: document.getElementById("bench-tamanho"),
  benchCampo: document.getElementById("bench-campo"),
  benchCenario: document.getElementById("bench-cenario"),
  statusBenchmark: document.getElementById("status-benchmark"),
  graficoBenchmark: document.getElementById("grafico-benchmark"),
};

// ---------------------------------------------------------------------------
// Imagens
// ---------------------------------------------------------------------------

async function carregarImagens() {
  const campo = elementos.campoOrdenacao.value;
  const algoritmo = elementos.algoritmoEscolhido.value;

  elementos.statusImagens.textContent = "Carregando...";

  const url = `/api/imagens?pagina=${estado.pagina}&por_pagina=20&ordenar_por=${campo}&algoritmo=${algoritmo}`;

  try {
    const resposta = await fetch(url);
    const dados = await resposta.json();

    if (!resposta.ok) {
      elementos.statusImagens.textContent = `Erro: ${dados.erro || "falha ao carregar"}`;
      elementos.corpoTabela.innerHTML = "";
      return;
    }

    estado.totalPaginas = Math.max(dados.total_paginas, 1);
    preencherTabela(dados.itens);

    elementos.statusImagens.textContent =
      dados.total === 0
        ? "Nenhuma imagem real encontrada no banco. Rode o modo 'misto' em popular_banco.py."
        : `${dados.total} imagem(ns) real(is) encontradas — ordenadas com ${dados.algoritmo}.`;

    elementos.infoPagina.textContent = `Página ${dados.pagina} de ${estado.totalPaginas}`;
    elementos.btnAnterior.disabled = dados.pagina <= 1;
    elementos.btnProxima.disabled = dados.pagina >= estado.totalPaginas;
  } catch (erro) {
    elementos.statusImagens.textContent = "Erro ao conectar com a API.";
    console.error(erro);
  }
}

function preencherTabela(itens) {
  elementos.corpoTabela.innerHTML = "";

  for (const item of itens) {
    const linha = document.createElement("tr");

    const celulaThumb = document.createElement("td");
    if (item.thumbnail_base64) {
      const img = document.createElement("img");
      img.src = `data:image/jpeg;base64,${item.thumbnail_base64}`;
      img.alt = item.nome_arquivo;
      celulaThumb.appendChild(img);
    } else {
      const placeholder = document.createElement("div");
      placeholder.className = "sem-thumbnail";
      placeholder.textContent = "sem img";
      celulaThumb.appendChild(placeholder);
    }
    linha.appendChild(celulaThumb);

    linha.appendChild(celulaTexto(item.nome_arquivo));
    linha.appendChild(celulaTexto(item.satelite || "-"));
    linha.appendChild(celulaTexto(item.data_captura || "-"));
    linha.appendChild(celulaTexto(item.tamanho_bytes?.toLocaleString("pt-BR") || "-"));

    elementos.corpoTabela.appendChild(linha);
  }
}

function celulaTexto(texto) {
  const td = document.createElement("td");
  td.textContent = texto;
  return td;
}

elementos.formFiltros.addEventListener("submit", (evento) => {
  evento.preventDefault();
  estado.pagina = 1;
  carregarImagens();
});

elementos.btnAnterior.addEventListener("click", () => {
  if (estado.pagina > 1) {
    estado.pagina -= 1;
    carregarImagens();
  }
});

elementos.btnProxima.addEventListener("click", () => {
  if (estado.pagina < estado.totalPaginas) {
    estado.pagina += 1;
    carregarImagens();
  }
});

// ---------------------------------------------------------------------------
// Benchmark
// ---------------------------------------------------------------------------

const CORES_ALGORITMOS = {
  bubble: "#c0533e",
  insertion: "#c99a3e",
  merge: "#3e7ac9",
  quick: "#4a7a52",
  radix: "#8a4ac9",
};

async function rodarBenchmark() {
  const tamanho = elementos.benchTamanho.value;
  const campo = elementos.benchCampo.value;
  const cenario = elementos.benchCenario.value;

  elementos.statusBenchmark.textContent = "Rodando benchmark...";
  elementos.graficoBenchmark.innerHTML = "";

  try {
    const url = `/api/benchmark?tamanho=${tamanho}&campo=${campo}&cenario=${cenario}`;
    const resposta = await fetch(url);
    const dados = await resposta.json();

    if (!resposta.ok) {
      elementos.statusBenchmark.textContent = `Erro: ${dados.erro || "falha ao rodar benchmark"}`;
      return;
    }

    elementos.statusBenchmark.textContent =
      `${dados.tamanho} registros, campo "${dados.campo}", cenário "${dados.cenario}".`;

    desenharGrafico(dados.tempos_segundos);
  } catch (erro) {
    elementos.statusBenchmark.textContent = "Erro ao conectar com a API.";
    console.error(erro);
  }
}

function desenharGrafico(tempos) {
  elementos.graficoBenchmark.innerHTML = "";

  const valores = Object.values(tempos);
  const maximo = Math.max(...valores, 0.000001);

  for (const [algoritmo, tempo] of Object.entries(tempos)) {
    const alturaPercentual = (tempo / maximo) * 100;

    const container = document.createElement("div");
    container.className = "barra-container";

    const valor = document.createElement("div");
    valor.className = "barra-valor";
    valor.textContent = `${tempo.toFixed(4)}s`;

    const barra = document.createElement("div");
    barra.className = "barra";
    barra.style.height = `${alturaPercentual}%`;
    barra.style.background = CORES_ALGORITMOS[algoritmo] || "#4a7a52";

    const rotulo = document.createElement("div");
    rotulo.className = "barra-rotulo";
    rotulo.textContent = algoritmo;

    container.appendChild(valor);
    container.appendChild(barra);
    container.appendChild(rotulo);
    elementos.graficoBenchmark.appendChild(container);
  }
}

elementos.formBenchmark.addEventListener("submit", (evento) => {
  evento.preventDefault();
  rodarBenchmark();
});

// ---------------------------------------------------------------------------
// Carga inicial
// ---------------------------------------------------------------------------

carregarImagens();
rodarBenchmark();
