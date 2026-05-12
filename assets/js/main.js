// Configurações visuais padrão da landing page.
window.TWEAK_DEFAULTS = {
    "accent": "cyan",
    "density": "comfortable",
    "displaySerif": true,
    "grain": true
  };

(function(){
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Year
  document.getElementById('year').textContent = new Date().getFullYear();

  // Apply persisted tweaks on load
  const apply = (k) => {
    document.documentElement.dataset.accent   = k.accent || 'cyan';
    document.documentElement.dataset.density  = k.density || 'comfortable';
    document.documentElement.dataset.serif    = String(k.displaySerif !== false);
    document.documentElement.dataset.grain    = String(k.grain !== false);
  };
  apply(window.TWEAK_DEFAULTS || {});

  // Nav scroll state
  const nav = document.getElementById('nav');
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 8);
  onScroll(); addEventListener('scroll', onScroll, {passive:true});

  // Reveal observer
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
  }, {rootMargin:'0px 0px -10% 0px', threshold:0.05});
  document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));

  // Magnetic buttons
  if (!reduce) {
    document.querySelectorAll('.magnetic').forEach(el => {
      let raf=null, tx=0, ty=0, cx=0, cy=0;
      const tick = () => {
        cx += (tx-cx)*0.18; cy += (ty-cy)*0.18;
        el.style.transform = `translate(${cx.toFixed(2)}px, ${cy.toFixed(2)}px)`;
        if (Math.abs(tx-cx)>.1 || Math.abs(ty-cy)>.1) raf = requestAnimationFrame(tick);
        else { raf=null; if (tx===0 && ty===0) el.style.transform=''; }
      };
      el.addEventListener('mousemove', (e) => {
        const r = el.getBoundingClientRect();
        tx = ((e.clientX - r.left)/r.width - .5) * 12;
        ty = ((e.clientY - r.top)/r.height - .5) * 12;
        if (!raf) raf = requestAnimationFrame(tick);
      });
      el.addEventListener('mouseleave', () => {
        tx=0; ty=0;
        if (!raf) raf = requestAnimationFrame(tick);
      });
    });
  }

  // Stage tilt
  const stage = document.getElementById('stage');
  if (stage && !reduce && matchMedia('(min-width: 980px)').matches) {
    let raf=null, ttx=0, tty=0, ctx=0, cty=0;
    const tick = () => {
      ctx += (ttx-ctx)*0.08; cty += (tty-cty)*0.08;
      stage.style.setProperty('--tilt-x', cty.toFixed(2)+'deg');
      stage.style.setProperty('--tilt-y', ctx.toFixed(2)+'deg');
      if (Math.abs(ttx-ctx)>.05 || Math.abs(tty-cty)>.05) raf = requestAnimationFrame(tick);
      else raf = null;
    };
    stage.addEventListener('mousemove', (e) => {
      const r = stage.getBoundingClientRect();
      ttx = ((e.clientX - r.left)/r.width - .5) * 8;
      tty = -((e.clientY - r.top)/r.height - .5) * 5;
      if (!raf) raf = requestAnimationFrame(tick);
    });
    stage.addEventListener('mouseleave', () => {
      ttx=0; tty=0; if (!raf) raf = requestAnimationFrame(tick);
    });
  }

  // Typing demo (loops)
  const phrases = [
    "Tenho um número de WhatsApp e leads somem depois do orçamento.",
    "Recebo contato por Insta e WA, equipe se perde.",
    "Quero IA, mas não sei por onde começar.",
    "Faço anúncios e os leads não viram cliente."
  ];
  const tEl = document.getElementById('typingText');
  if (tEl && !reduce) {
    let pi=0, ci=0, deleting=false;
    const speed = () => deleting ? 22 : 38;
    const step = () => {
      const cur = phrases[pi];
      if (!deleting) {
        ci++;
        tEl.textContent = cur.slice(0, ci);
        if (ci === cur.length) { deleting = true; return setTimeout(step, 1800); }
      } else {
        ci--;
        tEl.textContent = cur.slice(0, ci);
        if (ci === 0) { deleting = false; pi = (pi+1) % phrases.length; return setTimeout(step, 360); }
      }
      setTimeout(step, speed());
    };
    step();
  } else if (tEl) {
    tEl.textContent = phrases[0];
  }

  // KPI count-up when stage visible
  const ku = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      document.querySelectorAll('[data-count]').forEach(el => {
        const target = +el.dataset.count;
        const unit = el.querySelector('.unit');
        const t0 = performance.now(), dur = 1400;
        const run = (t) => {
          const k = Math.min(1, (t-t0)/dur);
          const e = 1 - Math.pow(1-k, 3);
          const val = Math.round(target*e);
          el.firstChild.nodeValue = val;
          if (unit) el.appendChild(unit);
          if (k<1) requestAnimationFrame(run);
        };
        requestAnimationFrame(run);
      });
      ku.disconnect();
    });
  }, {threshold:0.3});
  if (stage) ku.observe(stage);

  // Table filters
  const filterBtns = document.querySelectorAll('.filter');
  filterBtns.forEach(b => {
    b.addEventListener('click', () => {
      filterBtns.forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      const cat = b.dataset.filter;
      document.querySelectorAll('tbody tr').forEach(r => {
        r.style.display = (cat==='all' || r.dataset.cat===cat) ? '' : 'none';
      });
    });
  });

  // ============ PARTICLE SYSTEM (Canvas) ============
  const cvs = document.getElementById('particles');
  if (cvs && !reduce) {
    const ctx2 = cvs.getContext('2d');
    let W, H;
    const resizeCvs = () => { W = cvs.width = innerWidth; H = cvs.height = innerHeight; };
    resizeCvs(); addEventListener('resize', resizeCvs);
    const N = 55;
    const pts = [];
    for (let i = 0; i < N; i++) {
      pts.push({
        x: Math.random() * innerWidth,
        y: Math.random() * innerHeight,
        vx: (Math.random() - .5) * .35,
        vy: (Math.random() - .5) * .35,
        r: Math.random() * 2.2 + .6,
        a: Math.random() * .35 + .12,
      });
    }
    const drawParticles = () => {
      ctx2.clearRect(0, 0, W, H);
      for (const p of pts) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
        ctx2.beginPath();
        ctx2.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx2.fillStyle = '#00e5b8';
        ctx2.globalAlpha = p.a;
        ctx2.fill();
      }
      // connections
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const dx = pts[i].x - pts[j].x;
          const dy = pts[i].y - pts[j].y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 20000) {
            ctx2.beginPath();
            ctx2.moveTo(pts[i].x, pts[i].y);
            ctx2.lineTo(pts[j].x, pts[j].y);
            ctx2.strokeStyle = '#00e5b8';
            ctx2.globalAlpha = (1 - d2 / 20000) * .07;
            ctx2.lineWidth = .6;
            ctx2.stroke();
          }
        }
      }
      ctx2.globalAlpha = 1;
      requestAnimationFrame(drawParticles);
    };
    requestAnimationFrame(drawParticles);
  }

  // ============ CURSOR GLOW FOLLOWER ============
  const glow = document.getElementById('cursorGlow');
  if (glow && !reduce && matchMedia('(hover:hover)').matches) {
    let glowActive = false;
    document.addEventListener('mousemove', (e) => {
      if (!glowActive) { glow.classList.add('active'); glowActive = true; }
      glow.style.left = e.clientX + 'px';
      glow.style.top = e.clientY + 'px';
    });
    document.addEventListener('mouseleave', () => {
      glow.classList.remove('active'); glowActive = false;
    });
  }

  // ============ 3D TILT CARDS WITH GLOW ============
  if (!reduce) {
    document.querySelectorAll('.tilt-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;
        const y = (e.clientY - r.top) / r.height;
        const tiltX = (y - .5) * -12;
        const tiltY = (x - .5) * 12;
        card.style.transform =
          'perspective(800px) rotateX(' + tiltX.toFixed(1) + 'deg) rotateY(' + tiltY.toFixed(1) + 'deg) translateY(-8px) scale(1.025)';
        card.style.setProperty('--mx', (x * 100) + '%');
        card.style.setProperty('--my', (y * 100) + '%');
        card.style.setProperty('--glow-opacity', '1');
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
        card.style.setProperty('--glow-opacity', '0');
      });
    });
  }

  // ============ NODE HIGHLIGHT CYCLE ============
  const nodes = document.querySelectorAll('.node');
  if (nodes.length) {
    let currentNode = 0;
    const connActives = document.querySelectorAll('.conn-active');
    const cycleNode = () => {
      nodes.forEach(n => n.classList.remove('active'));
      if (!reduce) connActives.forEach(c => c.classList.remove('fire'));
      nodes[currentNode].classList.add('active');
      if (!reduce && connActives[currentNode]) {
        connActives[currentNode].classList.remove('fire');
        void connActives[currentNode].offsetWidth;
        connActives[currentNode].classList.add('fire');
      }
      currentNode = (currentNode + 1) % nodes.length;
    };
    cycleNode();
    setInterval(cycleNode, 2200);
  }

  // ============ PIPELINE CRM ANIMATION ============
  const pTrack = document.getElementById('pipelineTrack');
  if (pTrack) {
    const stageNames = ['Novo contato', 'Qualificado', 'Proposta', 'Ganho'];
    const stageColors = ['var(--a1)', 'var(--a2)', '#ffcc66', '#3ee083'];
    const leadCards = pTrack.querySelectorAll('.lead-card');
    const stagePills = document.querySelectorAll('.pipeline-stage');

    // Show cards initially
    setTimeout(() => {
      leadCards.forEach((c, i) => setTimeout(() => c.classList.add('visible'), i * 300));
    }, 600);

    // Cycle: advance each lead to next stage every few seconds
    const advanceLead = () => {
      leadCards.forEach(card => {
        let s = parseInt(card.dataset.stage);
        s = (s + 1) % 4;
        card.dataset.stage = s;
        const stageLabel = card.querySelector('.lead-stage');
        const dot = card.querySelector('.lead-status');
        if (stageLabel) stageLabel.textContent = stageNames[s];
        if (dot) {
          dot.style.background = stageColors[s];
          dot.style.boxShadow = '0 0 8px ' + stageColors[s];
        }
        // Animate: brief fade-shift
        card.style.opacity = '0';
        card.style.transform = 'translateX(10px)';
        setTimeout(() => {
          card.style.opacity = '1';
          card.style.transform = 'translateX(0)';
        }, 200);
      });
      // Highlight active stage column
      stagePills.forEach(p => p.classList.remove('active'));
      const activeStage = parseInt(leadCards[0].dataset.stage);
      if (stagePills[activeStage]) stagePills[activeStage].classList.add('active');
    };
    setInterval(advanceLead, 3500);
  }

  // ============ NOTIFICATION TOASTS ============
  const toastArea = document.getElementById('toastArea');
  if (toastArea) {
    const toasts = [
      { text: 'Lead qualificado → proposta', dot: '' },
      { text: 'Follow-up automático enviado', dot: 't-blue' },
      { text: 'Novo lead via WhatsApp', dot: '' },
      { text: 'Bot coletou informações', dot: 't-blue' },
      { text: 'Tarefa criada para vendedor', dot: 't-warn' },
      { text: 'Lead movido: Qualificado → Proposta', dot: '' },
      { text: 'IA analisou intenção de compra', dot: 't-blue' },
      { text: 'Agendamento confirmado', dot: '' },
      { text: 'Risco de perda detectado', dot: 't-warn' },
      { text: 'Canal Instagram conectado', dot: 't-blue' },
    ];
    let toastIdx = 0;
    const showToast = () => {
      const t = toasts[toastIdx % toasts.length];
      const el = document.createElement('div');
      el.className = 'toast';
      const now = new Date();
      const time = String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
      el.innerHTML = '<span class="t-dot ' + t.dot + '"></span>' + t.text + '<span class="t-time">' + time + '</span>';
      toastArea.appendChild(el);
      requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('show')));
      // Remove after 3s
      setTimeout(() => {
        el.classList.remove('show');
        setTimeout(() => el.remove(), 600);
      }, 3000);
      // Max 3 visible
      while (toastArea.children.length > 3) toastArea.children[0].remove();
      toastIdx++;
    };
    // First toast after 1.5s, then every 2.8s
    setTimeout(() => { showToast(); setInterval(showToast, 2800); }, 1500);
  }

  // ============ PARALLAX SCROLL ============
  if (!reduce && matchMedia('(min-width:720px)').matches) {
    const pEls = document.querySelectorAll('[data-speed]');
    let pTick = false;
    const runParallax = () => {
      const sy = scrollY;
      pEls.forEach(el => {
        const spd = parseFloat(el.dataset.speed) || 0;
        el.style.transform = 'translateY(' + (sy * spd).toFixed(1) + 'px)';
      });
      pTick = false;
    };
    addEventListener('scroll', () => { if (!pTick) { pTick = true; requestAnimationFrame(runParallax); } }, { passive: true });
  }

  // ============ V14 PRICING USER SIMULATOR ============
  const pricingControls = document.querySelector('.pricing-controls');
  const userButtons = document.querySelectorAll('[data-users]');
  const priceCards = document.querySelectorAll('.price[data-base][data-extra]');
  const brl = (n) => 'R$' + Math.round(n).toLocaleString('pt-BR');
  const updatePrices = (users) => {
    userButtons.forEach(btn => btn.classList.toggle('on', Number(btn.dataset.users) === users));
    priceCards.forEach(card => {
      const base = Number(card.dataset.base || 0);
      const extra = Number(card.dataset.extra || 0);
      const total = base + Math.max(0, users - 1) * extra;
      const priceEl = card.querySelector('[data-price]');
      const wrap = card.querySelector('[data-price-wrap]');
      const line = card.querySelector('[data-user-line]');
      if (wrap) wrap.classList.add('updating');
      setTimeout(() => {
        if (priceEl) priceEl.textContent = brl(total);
        if (line) line.textContent = (card.dataset.plan === 'completa' ? 'projeto' : 'implantação') + ' · ' + users + (users === 1 ? ' usuário' : ' usuários') + (card.dataset.plan === 'completa' ? ' · escopo guiado' : ' · pagamento único');
        if (wrap) wrap.classList.remove('updating');
      }, 130);
    });
    if (pricingControls) pricingControls.style.setProperty('--pcx', (users * 18) + '%');
  };
  userButtons.forEach(btn => btn.addEventListener('click', () => updatePrices(Number(btn.dataset.users || 1))));

})();
