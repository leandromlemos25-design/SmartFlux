/* SmartFlux v2 — Engine */
(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ===== Year ===== */
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ===== Tweaks ===== */
  var apply = function (k) {
    var d = document.documentElement.dataset;
    d.accent  = k.accent || 'cyan';
    d.density = k.density || 'comfortable';
    d.serif   = String(k.displaySerif !== false);
    d.grain   = String(k.grain !== false);
  };
  apply(window.TWEAK_DEFAULTS || {});

  /* ===== Nav scroll ===== */
  var nav = document.getElementById('nav');
  var onScroll = function () { nav.classList.toggle('scrolled', scrollY > 8); };
  onScroll();
  addEventListener('scroll', onScroll, { passive: true });

  /* ===== Scroll progress ===== */
  var prog = document.getElementById('scroll-progress');
  if (prog) {
    var updateProg = function () {
      var total = document.body.scrollHeight - innerHeight;
      if (total > 0) prog.style.width = (scrollY / total * 100).toFixed(1) + '%';
    };
    addEventListener('scroll', updateProg, { passive: true });
    updateProg();
  }

  /* ===== Hamburger ===== */
  var ham = document.getElementById('navHamburger');
  var mob = document.getElementById('navMobile');
  if (ham && mob) {
    var toggle = function (open) {
      mob.classList.toggle('open', open);
      ham.classList.toggle('active', open);
      ham.setAttribute('aria-expanded', String(open));
      document.body.classList.toggle('menu-open', open);
    };
    ham.addEventListener('click', function () { toggle(!mob.classList.contains('open')); });
    mob.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { toggle(false); }); });
    document.addEventListener('click', function (e) {
      if (mob.classList.contains('open') && !mob.contains(e.target) && !ham.contains(e.target)) toggle(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mob.classList.contains('open')) { toggle(false); ham.focus(); }
    });
  }

  /* ===== Scroll reveals (staggered) ===== */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.04 });
  document.querySelectorAll('[data-reveal]').forEach(function (el) { io.observe(el); });

  /* ===== Magnetic buttons ===== */
  if (!reduce) {
    document.querySelectorAll('.magnetic').forEach(function (el) {
      var raf = null, tx = 0, ty = 0, cx = 0, cy = 0;
      var tick = function () {
        cx += (tx - cx) * 0.15;
        cy += (ty - cy) * 0.15;
        el.style.transform = 'translate(' + cx.toFixed(2) + 'px,' + cy.toFixed(2) + 'px)';
        if (Math.abs(tx - cx) > 0.08 || Math.abs(ty - cy) > 0.08) raf = requestAnimationFrame(tick);
        else { raf = null; if (tx === 0 && ty === 0) el.style.transform = ''; }
      };
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        tx = ((e.clientX - r.left) / r.width - 0.5) * 14;
        ty = ((e.clientY - r.top) / r.height - 0.5) * 14;
        if (!raf) raf = requestAnimationFrame(tick);
      });
      el.addEventListener('mouseleave', function () { tx = 0; ty = 0; if (!raf) raf = requestAnimationFrame(tick); });
    });
  }

  /* ===== Stage tilt ===== */
  var stage = document.getElementById('stage');
  if (stage && !reduce && matchMedia('(min-width:980px)').matches) {
    var raf2 = null, ttx = 0, tty = 0, ctx2 = 0, cty = 0;
    var tick2 = function () {
      ctx2 += (ttx - ctx2) * 0.06;
      cty += (tty - cty) * 0.06;
      stage.style.setProperty('--tilt-x', cty.toFixed(2) + 'deg');
      stage.style.setProperty('--tilt-y', ctx2.toFixed(2) + 'deg');
      if (Math.abs(ttx - ctx2) > 0.04 || Math.abs(tty - cty) > 0.04) raf2 = requestAnimationFrame(tick2);
      else raf2 = null;
    };
    stage.addEventListener('mousemove', function (e) {
      var r = stage.getBoundingClientRect();
      ttx = ((e.clientX - r.left) / r.width - 0.5) * 6;
      tty = -((e.clientY - r.top) / r.height - 0.5) * 4;
      if (!raf2) raf2 = requestAnimationFrame(tick2);
    });
    stage.addEventListener('mouseleave', function () { ttx = 0; tty = 0; if (!raf2) raf2 = requestAnimationFrame(tick2); });
  }

  /* ===== Typing animation ===== */
  var phrases = [
    "Tenho um número de WhatsApp e leads somem depois do orçamento.",
    "Recebo contato por Insta e WA, equipe se perde.",
    "Quero IA, mas não sei por onde começar.",
    "Faço anúncios e os leads não viram cliente."
  ];
  var tEl = document.getElementById('typingText');
  if (tEl && !reduce) {
    var pi = 0, ci = 0, deleting = false;
    var step = function () {
      var cur = phrases[pi];
      if (!deleting) {
        ci++;
        tEl.textContent = cur.slice(0, ci);
        if (ci === cur.length) { deleting = true; return setTimeout(step, 2200); }
        setTimeout(step, 32 + Math.random() * 28);
      } else {
        ci -= 2;
        if (ci < 0) ci = 0;
        tEl.textContent = cur.slice(0, ci);
        if (ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; return setTimeout(step, 400); }
        setTimeout(step, 14);
      }
    };
    step();
  } else if (tEl) {
    tEl.textContent = phrases[0];
  }

  /* ===== KPI count-up ===== */
  var ku = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      document.querySelectorAll('[data-count]').forEach(function (el) {
        var target = +el.dataset.count;
        var unit = el.querySelector('.unit');
        var t0 = performance.now(), dur = 1600;
        var run = function (t) {
          var k = Math.min(1, (t - t0) / dur);
          var ease = 1 - Math.pow(1 - k, 4);
          var val = Math.round(target * ease);
          el.firstChild.nodeValue = val;
          if (unit) el.appendChild(unit);
          if (k < 1) requestAnimationFrame(run);
        };
        requestAnimationFrame(run);
      });
      ku.disconnect();
    });
  }, { threshold: 0.25 });
  if (stage) ku.observe(stage);

  /* ===== Results count-up ===== */
  var resultEls = document.querySelectorAll('[data-result-count]');
  if (resultEls.length && !reduce) {
    var rio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var target = +el.dataset.resultCount;
        var suffix = el.dataset.resultSuffix || '';
        var t0 = performance.now(), dur = 1600;
        var run = function (t) {
          var k = Math.min(1, (t - t0) / dur);
          var val = Math.round(target * (1 - Math.pow(1 - k, 4)));
          el.textContent = val + (k >= 1 ? suffix : '');
          if (k < 1) requestAnimationFrame(run);
        };
        requestAnimationFrame(run);
        rio.unobserve(el);
      });
    }, { threshold: 0.35 });
    resultEls.forEach(function (el) { rio.observe(el); });
  }

  /* ===== Table filters ===== */
  var filterBtns = document.querySelectorAll('.filter');
  filterBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      filterBtns.forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      var cat = b.dataset.filter;
      document.querySelectorAll('tbody tr').forEach(function (r) {
        r.style.display = (cat === 'all' || r.dataset.cat === cat) ? '' : 'none';
      });
    });
  });

  /* ===== Particles (minimal) ===== */
  var cvs = document.getElementById('particles');
  if (cvs && !reduce) {
    var c = cvs.getContext('2d');
    var W, H;
    var resize = function () { W = cvs.width = innerWidth; H = cvs.height = innerHeight; };
    resize();
    addEventListener('resize', resize);
    var N = 35;
    var pts = [];
    for (var i = 0; i < N; i++) {
      pts.push({
        x: Math.random() * innerWidth,
        y: Math.random() * innerHeight,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.8 + 0.4,
        a: Math.random() * 0.25 + 0.08
      });
    }
    var draw = function () {
      c.clearRect(0, 0, W, H);
      for (var j = 0; j < N; j++) {
        var p = pts[j];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
        c.beginPath();
        c.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        c.fillStyle = '#00e5b8';
        c.globalAlpha = p.a;
        c.fill();
      }
      for (var a2 = 0; a2 < N; a2++) {
        for (var b2 = a2 + 1; b2 < N; b2++) {
          var dx = pts[a2].x - pts[b2].x;
          var dy = pts[a2].y - pts[b2].y;
          var d2 = dx * dx + dy * dy;
          if (d2 < 18000) {
            c.beginPath();
            c.moveTo(pts[a2].x, pts[a2].y);
            c.lineTo(pts[b2].x, pts[b2].y);
            c.strokeStyle = '#00e5b8';
            c.globalAlpha = (1 - d2 / 18000) * 0.04;
            c.lineWidth = 0.5;
            c.stroke();
          }
        }
      }
      c.globalAlpha = 1;
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  }

  /* ===== Cursor glow ===== */
  var glow = document.getElementById('cursorGlow');
  if (glow && !reduce && matchMedia('(hover:hover)').matches) {
    var active = false;
    document.addEventListener('mousemove', function (e) {
      if (!active) { glow.classList.add('active'); active = true; }
      glow.style.left = e.clientX + 'px';
      glow.style.top = e.clientY + 'px';
    });
    document.addEventListener('mouseleave', function () { glow.classList.remove('active'); active = false; });
  }

  /* ===== 3D Tilt cards ===== */
  if (!reduce) {
    document.querySelectorAll('.tilt-card').forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width;
        var y = (e.clientY - r.top) / r.height;
        var tX = (y - 0.5) * -10;
        var tY = (x - 0.5) * 10;
        card.style.transform = 'perspective(800px) rotateX(' + tX.toFixed(1) + 'deg) rotateY(' + tY.toFixed(1) + 'deg) translateY(-8px) scale(1.02)';
        card.style.setProperty('--mx', (x * 100) + '%');
        card.style.setProperty('--my', (y * 100) + '%');
        card.style.setProperty('--glow-opacity', '1');
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
        card.style.setProperty('--glow-opacity', '0');
      });
    });
  }

  /* ===== Node highlight cycle ===== */
  var nodes = document.querySelectorAll('.node');
  if (nodes.length) {
    var cIdx = 0;
    var connActives = document.querySelectorAll('.conn-active');
    var cycle = function () {
      nodes.forEach(function (n) { n.classList.remove('active'); });
      if (!reduce) connActives.forEach(function (c2) { c2.classList.remove('fire'); });
      nodes[cIdx].classList.add('active');
      if (!reduce && connActives[cIdx]) {
        connActives[cIdx].classList.remove('fire');
        void connActives[cIdx].offsetWidth;
        connActives[cIdx].classList.add('fire');
      }
      cIdx = (cIdx + 1) % nodes.length;
    };
    cycle();
    setInterval(cycle, 2600);
  }

  /* ===== Pipeline animation ===== */
  var pTrack = document.getElementById('pipelineTrack');
  if (pTrack) {
    var stageNames = ['Novo contato', 'Qualificado', 'Proposta', 'Ganho'];
    var stageColors = ['var(--a1)', 'var(--a2)', '#ffcc66', '#3ee083'];
    var leadCards = pTrack.querySelectorAll('.lead-card');
    var stagePills = document.querySelectorAll('.pipeline-stage');
    setTimeout(function () {
      leadCards.forEach(function (c2, i2) { setTimeout(function () { c2.classList.add('visible'); }, i2 * 280); });
    }, 500);
    var advance = function () {
      leadCards.forEach(function (card) {
        var s = (parseInt(card.dataset.stage) + 1) % 4;
        card.dataset.stage = s;
        var sl = card.querySelector('.lead-stage');
        var dot = card.querySelector('.lead-status');
        if (sl) sl.textContent = stageNames[s];
        if (dot) { dot.style.background = stageColors[s]; dot.style.boxShadow = '0 0 6px ' + stageColors[s]; }
        card.style.opacity = '0'; card.style.transform = 'translateX(8px)';
        setTimeout(function () { card.style.opacity = '1'; card.style.transform = 'translateX(0)'; }, 180);
      });
      stagePills.forEach(function (p) { p.classList.remove('active'); });
      var as = parseInt(leadCards[0].dataset.stage);
      if (stagePills[as]) stagePills[as].classList.add('active');
    };
    setInterval(advance, 4000);
  }

  /* ===== Analysis items cycle ===== */
  var aItems = document.querySelectorAll('.a-item');
  if (aItems.length && !reduce) {
    var aIdx = 0;
    var cycleA = function () {
      aItems.forEach(function (el) { el.classList.remove('a-active'); });
      aItems[aIdx].classList.add('a-active');
      aIdx = (aIdx + 1) % aItems.length;
    };
    cycleA();
    setInterval(cycleA, 2600);
  }

  /* ===== Toast notifications ===== */
  var toastArea = document.getElementById('toastArea');
  if (toastArea) {
    var toasts = [
      { text: 'Lead qualificado → proposta', dot: '' },
      { text: 'Follow-up automático enviado', dot: 't-blue' },
      { text: 'Novo lead via WhatsApp', dot: '' },
      { text: 'Bot coletou informações', dot: 't-blue' },
      { text: 'Tarefa criada para vendedor', dot: 't-warn' },
      { text: 'Lead movido: Qualif. → Proposta', dot: '' },
      { text: 'IA analisou intenção de compra', dot: 't-blue' },
      { text: 'Agendamento confirmado', dot: '' },
      { text: 'Risco de perda detectado', dot: 't-warn' }
    ];
    var tIdx = 0;
    var showToast = function () {
      var t = toasts[tIdx % toasts.length];
      var el = document.createElement('div');
      el.className = 'toast';
      var now = new Date();
      var time = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
      el.innerHTML = '<span class="t-dot ' + t.dot + '"></span>' + t.text + '<span class="t-time">' + time + '</span>';
      toastArea.appendChild(el);
      requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add('show'); }); });
      setTimeout(function () { el.classList.remove('show'); setTimeout(function () { el.remove(); }, 500); }, 3500);
      while (toastArea.children.length > 3) toastArea.children[0].remove();
      tIdx++;
    };
    setTimeout(function () { showToast(); setInterval(showToast, 3200); }, 1800);
  }

  /* ===== Parallax ===== */
  if (!reduce && matchMedia('(min-width:720px)').matches) {
    var pEls = document.querySelectorAll('[data-speed]');
    var pTick = false;
    var runP = function () {
      var sy = scrollY;
      pEls.forEach(function (el) {
        var spd = parseFloat(el.dataset.speed) || 0;
        el.style.transform = 'translateY(' + (sy * spd).toFixed(1) + 'px)';
      });
      pTick = false;
    };
    addEventListener('scroll', function () { if (!pTick) { pTick = true; requestAnimationFrame(runP); } }, { passive: true });
  }

  /* ===== Pricing simulator ===== */
  var userBtns = document.querySelectorAll('[data-users]');
  var priceCards = document.querySelectorAll('.price[data-base][data-extra]');
  var brl = function (n) { return 'R$' + Math.round(n).toLocaleString('pt-BR'); };
  var updatePrices = function (users) {
    userBtns.forEach(function (btn) { btn.classList.toggle('on', Number(btn.dataset.users) === users); });
    priceCards.forEach(function (card) {
      var base = Number(card.dataset.base || 0);
      var extra = Number(card.dataset.extra || 0);
      var total = base + Math.max(0, users - 1) * extra;
      var priceEl = card.querySelector('[data-price]');
      var wrap = card.querySelector('[data-price-wrap]');
      var line = card.querySelector('[data-user-line]');
      if (wrap) wrap.classList.add('updating');
      setTimeout(function () {
        if (priceEl) priceEl.textContent = brl(total);
        if (line) line.textContent = (card.dataset.plan === 'completa' ? 'projeto' : 'implantação') + ' · ' + users + (users === 1 ? ' usuário' : ' usuários') + (card.dataset.plan === 'completa' ? ' · escopo guiado' : ' · pagamento único');
        if (wrap) wrap.classList.remove('updating');
      }, 150);
    });
  };
  userBtns.forEach(function (btn) {
    btn.addEventListener('click', function () { updatePrices(Number(btn.dataset.users || 1)); });
  });
})();
