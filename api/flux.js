// api/flux.js — Vercel Serverless Function: proxy para a API DeepSeek
//
// SETUP:
// 1. No painel do Vercel, vá em Settings > Environment Variables
// 2. Adicione: DEEPSEEK_API_KEY = sua_chave (https://platform.deepseek.com → API Keys)
// 3. Faça redeploy — pronto, o Flux já funciona com DeepSeek
//
// Aceita o body {system, messages, model?, max_tokens?} que o front-end já envia
// e responde no formato {content:[{type:'text', text}]} (Anthropic-like) para o
// flux-chat.js não precisar mudar a leitura da resposta.

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { system, messages = [], model, max_tokens } = req.body || {};

    // Monta no formato OpenAI/DeepSeek: o system vira a 1ª mensagem.
    const chat = [];
    if (system) chat.push({ role: 'system', content: system });
    for (const m of messages) chat.push({ role: m.role, content: m.content });

    const upstream = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
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
      return res.status(upstream.status).json({ error: 'deepseek_error', detail: data });
    }

    const text = (data && data.choices && data.choices[0] && data.choices[0].message)
      ? data.choices[0].message.content
      : '';

    // Resposta no formato que o front-end já espera.
    return res.status(200).json({ content: [{ type: 'text', text }] });

  } catch (err) {
    return res.status(500).json({ error: 'proxy_error', message: err.message });
  }
};
