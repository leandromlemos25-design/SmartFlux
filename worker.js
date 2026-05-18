// worker.js — Cloudflare Worker: proxy para a API Anthropic
//
// SETUP (5 minutos):
// 1. Acesse https://workers.cloudflare.com e crie uma conta gratuita
// 2. Crie um novo Worker e cole todo o conteúdo deste arquivo
// 3. Em "Settings > Variables > Secrets", adicione:
//    Nome: ANTHROPIC_API_KEY   Valor: sua chave da API Claude
// 4. Clique em Deploy e copie a URL gerada (termina em .workers.dev)
// 5. Cole essa URL em assets/js/flux-chat.js na constante FLUX_WORKER_URL

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders() });
    }

    try {
      const body = await request.json();

      const upstream = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify(body),
      });

      const data = await upstream.json();
      return new Response(JSON.stringify(data), {
        status: upstream.status,
        headers: { 'Content-Type': 'application/json', ...corsHeaders() },
      });

    } catch (err) {
      return new Response(
        JSON.stringify({ error: 'worker_error', message: err.message }),
        { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
      );
    }
  },
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
