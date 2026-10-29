// Clique em qualquer miniatura (imagem dentro de uma tabela) para ver a imagem grande.
// Clique em qualquer lugar ou tecle Esc para fechar.
(function () {
  const fundo = document.createElement("div");
  fundo.id = "ampliada";
  fundo.hidden = true;
  const grande = document.createElement("img");
  fundo.appendChild(grande);
  document.body.appendChild(fundo);

  function fechar() {
    fundo.hidden = true;
    grande.removeAttribute("src");
  }

  document.addEventListener("click", (e) => {
    const miniatura = e.target.closest("td img");
    if (miniatura) {
      grande.src = miniatura.src;
      fundo.hidden = false;
    } else if (!fundo.hidden) {
      fechar();
    }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") fechar(); });
})();
