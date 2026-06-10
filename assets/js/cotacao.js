/* =================================================================
   SmartFlux — Cotação do dólar (USD→BRL) + simulador de usuários
   A licença Kommo é vendida em dólar e POR USUÁRIO. Os cards de
   plano (Basic/Advanced/Pro) multiplicam pelo nº de usuários (1–5);
   a tabela de referência fica sempre em "por usuário" (1×).
   Cotação: AwesomeAPI (dólar comercial), cache 1x/dia, fallback,
   + spread de câmbio configurável.
   ================================================================= */
(function () {
  var API = "https://economia.awesomeapi.com.br/last/USD-BRL";
  var FALLBACK = 5.40;        // usado só se a API falhar
  var SPREAD = 0.03;          // custo de câmbio sobre o dólar comercial (3%)
  var KEY = "sf_usdbrl_v1";

  var els = Array.prototype.slice.call(document.querySelectorAll("[data-usd]"));
  if (!els.length) return;

  var users = 1;
  var rate = null, whenLabel = "", aprox = false;

  function brl(v) { return "R$" + Math.round(v).toLocaleString("pt-BR"); }
  function isCard(el) { return !!(el.closest && el.closest(".price")); }

  function render() {
    if (rate == null) return;
    var eff = rate * (1 + SPREAD);
    els.forEach(function (el) {
      var usd = parseFloat(el.getAttribute("data-usd"));
      if (isNaN(usd)) return;
      var card = isCard(el);
      var mult = card ? users : 1;
      el.textContent = brl(usd * mult * eff);
      el.setAttribute(
        "title",
        "US$" + usd + (mult > 1 ? " × " + mult + " usuários" : "") +
        " × R$" + eff.toFixed(2).replace(".", ",") +
        " (comercial + " + Math.round(SPREAD * 100) + "%)"
      );
      if (card && el.parentElement) {
        var u = el.parentElement.querySelector(".u");
        if (u) u.textContent = (users === 1)
          ? "/6 meses · por usuário"
          : "/6 meses · " + users + " usuários";
      }
    });
    var note = document.getElementById("cotacao-note");
    if (note) {
      note.innerHTML =
        "<strong>Cotação do dólar comercial:</strong> R$" +
        rate.toFixed(2).replace(".", ",") +
        (aprox ? " (aproximada) · " : " · atualizado em ") + whenLabel +
        ". A licença Kommo é em dólar — o valor em real acompanha a cotação e já inclui o custo de câmbio (" +
        Math.round(SPREAD * 100) + "%).";
    }
  }

  function setRate(r, w, a) { rate = r; whenLabel = w; aprox = a; render(); }

  // Simulador 1–5 usuários (multiplica só os cards de plano)
  var userBtns = Array.prototype.slice.call(document.querySelectorAll("[data-users]"));
  userBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      users = Number(btn.getAttribute("data-users")) || 1;
      userBtns.forEach(function (b) { b.classList.toggle("on", b === btn); });
      render();
    });
  });

  function today() { return new Date().toISOString().slice(0, 10); }

  // cache: 1 fetch por dia
  try {
    var c = JSON.parse(localStorage.getItem(KEY) || "null");
    if (c && c.date === today() && c.rate) { setRate(c.rate, c.when, false); return; }
  } catch (e) {}

  fetch(API, { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var rt = parseFloat(d && d.USDBRL && d.USDBRL.bid);
      if (!rt || isNaN(rt)) throw new Error("sem cotação");
      var when = new Date().toLocaleDateString("pt-BR");
      setRate(rt, when, false);
      try { localStorage.setItem(KEY, JSON.stringify({ rate: rt, date: today(), when: when })); } catch (e) {}
    })
    .catch(function () { setRate(FALLBACK, new Date().toLocaleDateString("pt-BR"), true); });
})();
