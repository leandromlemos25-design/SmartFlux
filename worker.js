// worker.js — Cloudflare Worker: proxy para a API DeepSeek
// (Alternativa ao api/flux.js da Vercel — use UM dos dois.)
//
// SETUP (5 minutos):
// 1. Acesse https://workers.cloudflare.com e crie uma conta gratuita
// 2. Crie um novo Worker e cole todo o conteúdo deste arquivo
// 3. Em "Settings > Variables > Secrets", adicione:
//    Nome: DEEPSEEK_API_KEY   Valor: sua chave (https://platform.deepseek.com)
// 4. Clique em Deploy e copie a URL gerada (termina em .workers.dev)
// 5. Aponte FLUX_WORKER_URL em assets/js/flux-chat.js para essa URL
//
// Aceita {system, messages, model?, max_tokens?} e responde {content:[{text}]}.

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders() });
    }

    try {
      const { system, messages = [], model, max_tokens } = await request.json();

      const chat = [];
      if (system) chat.push({ role: 'system', content: system });
      for (const m of messages) chat.push({ role: m.role, content: m.content });

      const upstream = await fetch('https://api.deepseek.com/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
        },
        body: JSON.stringify({
          model: model || 'deepseek-chat',
          messages: chat,
          max_tokens: max_tokens || 512,
          stream: false,
        }),
      });

      const data = await upstream.json();
      if (!upstream.ok) {
        return json({ error: 'deepseek_error', detail: data }, upstream.status);
      }

      const text = (data && data.choices && data.choices[0] && data.choices[0].message)
        ? data.choices[0].message.content
        : '';

      return json({ content: [{ type: 'text', text }] }, 200);

    } catch (err) {
      return json({ error: 'worker_error', message: err.message }, 500);
    }
  },
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders() },
  });
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
