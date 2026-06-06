/* =================================================================
   SmartFlux — Cotação do dólar (USD→BRL) para a licença Kommo
   A licença é vendida em dólar; os valores em real seguem a cotação
   do dia. Roda no navegador do visitante, busca a cotação na
   AwesomeAPI (dólar comercial, sem chave, com CORS), faz cache 1x/dia
   e tem fallback caso a API falhe.
   Elementos com [data-usd] recebem o valor em R$ = usd * cotação.
   ================================================================= */
(function () {
  var API = "https://economia.awesomeapi.com.br/last/USD-BRL";
  var FALLBACK = 5.40;                 // usado só se a API falhar
  var KEY = "sf_usdbrl_v1";
  var els = Array.prototype.slice.call(document.querySelectorAll("[data-usd]"));
  if (!els.length) return;

  function brl(v) { return "R$" + Math.round(v).toLocaleString("pt-BR"); }

  function apply(rate, whenLabel, aprox) {
    els.forEach(function (el) {
      var usd = parseFloat(el.getAttribute("data-usd"));
      if (!isNaN(usd)) {
        el.textContent = brl(usd * rate);
        el.setAttribute("title", "US$" + usd + " × R$" + rate.toFixed(2).replace(".", ","));
      }
    });
    var note = document.getElementById("cotacao-note");
    if (note) {
      note.innerHTML =
        "<strong>Cotação do dólar:</strong> R$" +
        rate.toFixed(2).replace(".", ",") +
        (aprox ? " (aproximada) · " : " · atualizado em ") +
        whenLabel +
        ". A licença Kommo é em dólar — o valor em real acompanha a cotação.";
    }
  }

  function today() { return new Date().toISOString().slice(0, 10); }

  // cache: evita refazer fetch no mesmo dia
  try {
    var c = JSON.parse(localStorage.getItem(KEY) || "null");
    if (c && c.date === today() && c.rate) {
      apply(c.rate, c.when, false);
      return;
    }
  } catch (e) {}

  fetch(API, { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var rate = parseFloat(d && d.USDBRL && d.USDBRL.bid);
      if (!rate || isNaN(rate)) throw new Error("sem cotação");
      var when = new Date().toLocaleDateString("pt-BR");
      apply(rate, when, false);
      try {
        localStorage.setItem(KEY, JSON.stringify({ rate: rate, date: today(), when: when }));
      } catch (e) {}
    })
    .catch(function () {
      apply(FALLBACK, new Date().toLocaleDateString("pt-BR"), true);
    });
})();
