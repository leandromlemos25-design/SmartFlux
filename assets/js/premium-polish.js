(function () {
  'use strict';

  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ============ SCROLL PROGRESS BAR ============
  var progressBar = document.getElementById('scroll-progress');
  if (progressBar) {
    var updateProgress = function () {
      var total = document.body.scrollHeight - innerHeight;
      if (total > 0) progressBar.style.width = (scrollY / total * 100).toFixed(1) + '%';
    };
    addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  }

  // ============ HAMBURGER MENU ============
  var hamburgerBtn = document.getElementById('navHamburger');
  var mobileNav = document.getElementById('navMobile');
  if (hamburgerBtn && mobileNav) {
    var toggleMenu = function (open) {
      mobileNav.classList.toggle('open', open);
      hamburgerBtn.classList.toggle('active', open);
      hamburgerBtn.setAttribute('aria-expanded', String(open));
      document.body.classList.toggle('menu-open', open);
    };
    hamburgerBtn.addEventListener('click', function () {
      toggleMenu(!mobileNav.classList.contains('open'));
    });
    mobileNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { toggleMenu(false); });
    });
    document.addEventListener('click', function (e) {
      if (
        mobileNav.classList.contains('open') &&
        !mobileNav.contains(e.target) &&
        !hamburgerBtn.contains(e.target)
      ) {
        toggleMenu(false);
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileNav.classList.contains('open')) {
        toggleMenu(false);
        hamburgerBtn.focus();
      }
    });
  }

  // ============ RESULTS COUNT-UP ============
  var resultCountEls = document.querySelectorAll('[data-result-count]');
  if (resultCountEls.length && !reduce) {
    var rio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var target = +el.dataset.resultCount;
        var suffix = el.dataset.resultSuffix || '';
        var t0 = performance.now();
        var dur = 1400;
        var run = function (t) {
          var k = Math.min(1, (t - t0) / dur);
          var val = Math.round(target * (1 - Math.pow(1 - k, 3)));
          el.textContent = val + (k >= 1 ? suffix : '');
          if (k < 1) requestAnimationFrame(run);
        };
        requestAnimationFrame(run);
        rio.unobserve(el);
      });
    }, { threshold: 0.4 });
    resultCountEls.forEach(function (el) { rio.observe(el); });
  }

}());
