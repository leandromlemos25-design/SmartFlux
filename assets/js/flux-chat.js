/* ============ FLUX — SmartFlux AI Chat Widget ============ */

// Vercel Serverless Function no mesmo domínio — sem CORS
const FLUX_WORKER_URL = '/api/flux';

const FLUX_SYSTEM = `Você é o Flux, assistente de IA da SmartFlux. Seu papel é tirar dúvidas sobre CRM Kommo, WhatsApp Business, automações, funis de vendas e o método SmartFlux.

Personalidade:
- Fale de forma descontraída e direta, como um amigo que entende do assunto
- Linguagem simples, sem jargão técnico desnecessário
- Seja objetivo: responda o que foi perguntado sem enrolação
- Use emojis com moderação (1-2 por mensagem quando fizer sentido)
- Nunca prometa resultados específicos de vendas
- Se a dúvida for muito específica sobre a operação da pessoa, sugira o diagnóstico gratuito pelo WhatsApp

Sobre a SmartFlux:
- Parceiros oficiais Kommo no Brasil
- Fazemos diagnóstico da operação antes de indicar qualquer plano
- 3 pacotes: Organização Inicial (R$497+), Atendimento Inteligente (R$1.497+) e Operação Completa (R$3.000+)
- Atendemos pequenas e médias empresas em todo o Brasil
- WhatsApp para diagnóstico: +55 34 99271-0008

Quando alguém quiser contratar ou tiver dúvida específica sobre a operação deles, incentive o contato pelo WhatsApp para o diagnóstico gratuito.`;

const QUICK_REPLIES_INITIAL = [
  'O que é CRM?',
  'Qual plano me serve?',
  'Como funciona o diagnóstico?',
  'Preciso do plano Pro?',
];

(function () {
  'use strict';

  const btn      = document.getElementById('flux-btn');
  const panel    = document.getElementById('flux-panel');
  const closeBtn = document.getElementById('flux-close');
  const messages = document.getElementById('flux-messages');
  const textarea = document.getElementById('flux-textarea');
  const sendBtn  = document.getElementById('flux-send');
  const badge    = document.getElementById('flux-badge');

  if (!btn || !panel) return;

  let history   = [];
  let isOpen    = false;
  let isLoading = false;

  // ── Toggle ────────────────────────────────────────────────
  function togglePanel() {
    isOpen = !isOpen;
    btn.classList.toggle('open', isOpen);
    panel.classList.toggle('open', isOpen);
    if (isOpen) {
      badge.classList.add('hidden');
      textarea.focus();
      if (history.length === 0) showWelcome();
    }
  }

  btn.addEventListener('click', togglePanel);
  closeBtn.addEventListener('click', togglePanel);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && isOpen) togglePanel(); });

  setTimeout(() => { if (!isOpen) badge.classList.remove('hidden'); }, 4000);

  // ── Welcome ───────────────────────────────────────────────
  function showWelcome() {
    addBotMessage('Oi! Sou o Flux, assistente da SmartFlux 👋 Como posso te ajudar hoje?');
    showQuickReplies(QUICK_REPLIES_INITIAL);
  }

  // ── Render helpers ────────────────────────────────────────
  function addBotMessage(text) {
    removeQuickReplies();
    const wrap = document.createElement('div');
    wrap.className = 'flux-msg bot';
    wrap.innerHTML =
      '<div class="flux-msg-av">F</div>' +
      '<div class="flux-bubble">' + escHtml(text).replace(/\n/g, '<br>') + '</div>';
    messages.appendChild(wrap);
    scrollBottom();
    return wrap.querySelector('.flux-bubble');
  }

  function addUserMessage(text) {
    const wrap = document.createElement('div');
    wrap.className = 'flux-msg user';
    wrap.innerHTML = '<div class="flux-bubble">' + escHtml(text).replace(/\n/g, '<br>') + '</div>';
    messages.appendChild(wrap);
    scrollBottom();
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'flux-typing-wrap';
    el.id = 'flux-typing';
    el.innerHTML =
      '<div class="flux-msg-av">F</div>' +
      '<div class="flux-typing-bubble"><span></span><span></span><span></span></div>';
    messages.appendChild(el);
    scrollBottom();
  }

  function removeTyping() {
    const el = document.getElementById('flux-typing');
    if (el) el.remove();
  }

  function showQuickReplies(replies) {
    removeQuickReplies();
    const wrap = document.createElement('div');
    wrap.className = 'flux-quick';
    wrap.id = 'flux-quick';
    replies.forEach(r => {
      const b = document.createElement('button');
      b.textContent = r;
      b.addEventListener('click', () => sendMessage(r));
      wrap.appendChild(b);
    });
    messages.appendChild(wrap);
    scrollBottom();
  }

  function removeQuickReplies() {
    const el = document.getElementById('flux-quick');
    if (el) el.remove();
  }

  function showCtaButton(bubble) {
    if (!bubble || bubble.querySelector('.flux-cta-inline')) return;
    const a = document.createElement('a');
    a.className = 'flux-cta-inline';
    a.href = 'https://wa.me/5534992710008?text=Quero%20fazer%20um%20diagn%C3%B3stico%20SmartFlux';
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = '→ Diagnóstico gratuito no WhatsApp';
    bubble.appendChild(document.createElement('br'));
    bubble.appendChild(a);
  }

  function scrollBottom() {
    requestAnimationFrame(() => { messages.scrollTop = messages.scrollHeight; });
  }

  function escHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Send ──────────────────────────────────────────────────
  async function sendMessage(text) {
    text = (text || textarea.value).trim();
    if (!text || isLoading) return;

    textarea.value = '';
    autoResize();
    addUserMessage(text);
    history.push({ role: 'user', content: text });

    isLoading = true;
    sendBtn.disabled = true;
    textarea.disabled = true;
    showTyping();

    try {
      const res = await fetch(FLUX_WORKER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-haiku-4-5-20251001',
          max_tokens: 512,
          system: FLUX_SYSTEM,
          messages: history,
        }),
      });

      if (!res.ok) throw new Error('api_error');
      const data = await res.json();
      const reply = (data && data.content && data.content[0] && data.content[0].text)
        ? data.content[0].text
        : 'Opa, tive um probleminha aqui. Tenta de novo!';

      history.push({ role: 'assistant', content: reply });
      removeTyping();
      const bubble = addBotMessage(reply);

      if (/diagn[oó]stico|whatsapp|contato|falar|ligar/i.test(reply)) {
        setTimeout(() => showCtaButton(bubble), 400);
      }

    } catch (e) {
      removeTyping();
      const bubble = addBotMessage('Opa, não consegui responder agora. Fala direto pelo WhatsApp! 👇');
      setTimeout(() => showCtaButton(bubble), 300);
    } finally {
      isLoading = false;
      sendBtn.disabled = false;
      textarea.disabled = false;
      textarea.focus();
    }
  }

  // ── Input handlers ────────────────────────────────────────
  sendBtn.addEventListener('click', () => sendMessage());

  textarea.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  function autoResize() {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 96) + 'px';
  }
  textarea.addEventListener('input', autoResize);

})();
