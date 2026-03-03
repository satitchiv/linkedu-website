/* ============================================================
   LINKEDU — Main JavaScript
   Language toggle + Mobile nav + FAQ accordion + Utils
   ============================================================ */

(function () {
  'use strict';

  /* --- Language Toggle -------------------------------------- */
  function initLanguage() {
    const stored = localStorage.getItem('linkedu-lang') || 'th';
    setLang(stored);

    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        setLang(btn.dataset.lang);
      });
    });
  }

  function setLang(lang) {
    document.documentElement.setAttribute('lang', lang);
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    localStorage.setItem('linkedu-lang', lang);
  }

  /* --- Mobile Menu ----------------------------------------- */
  function initMobileMenu() {
    var btn = document.querySelector('.hamburger');
    var menu = document.querySelector('.mobile-nav');
    if (!btn || !menu) return;

    btn.addEventListener('click', function () {
      btn.classList.toggle('open');
      menu.classList.toggle('open');
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !menu.contains(e.target)) {
        btn.classList.remove('open');
        menu.classList.remove('open');
      }
    });
  }

  /* --- Sticky Header Shadow --------------------------------- */
  function initHeaderScroll() {
    var header = document.querySelector('.site-header');
    if (!header) return;

    window.addEventListener('scroll', function () {
      if (window.scrollY > 8) {
        header.style.boxShadow = '0 2px 24px rgba(0,0,0,0.35)';
      } else {
        header.style.boxShadow = 'none';
      }
    }, { passive: true });
  }

  /* --- FAQ Accordion --------------------------------------- */
  function initFaq() {
    document.querySelectorAll('.faq-question').forEach(function (q) {
      q.addEventListener('click', function () {
        var item = q.closest('.faq-item');
        var isOpen = item.classList.contains('open');

        // Close all
        document.querySelectorAll('.faq-item.open').forEach(function (el) {
          el.classList.remove('open');
        });

        // Open clicked unless it was already open
        if (!isOpen) item.classList.add('open');
      });
    });
  }

  /* --- Active Nav Link ------------------------------------- */
  function initActiveNav() {
    var path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-link').forEach(function (link) {
      var href = link.getAttribute('href') || '';
      if (href && (href === path || href.replace('./', '') === path)) {
        link.classList.add('active');
      }
    });
  }

  /* --- School Filter (schools.html) ------------------------ */
  function initSchoolFilter() {
    var searchEl = document.querySelector('.filter-search');
    var cards = document.querySelectorAll('.school-card');
    var countEl = document.querySelector('.filter-count');
    if (!searchEl || !cards.length) return;

    function updateCount(n) {
      if (countEl) {
        countEl.textContent = n + ' schools';
      }
    }

    searchEl.addEventListener('input', function () {
      var q = searchEl.value.trim().toLowerCase();
      var visible = 0;
      cards.forEach(function (card) {
        var name = (card.querySelector('.school-card-name') || card).textContent.toLowerCase();
        var show = !q || name.includes(q);
        card.parentElement.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      updateCount(visible);
    });
  }

  /* --- Smooth anchor scroll -------------------------------- */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        var target = document.querySelector(link.getAttribute('href'));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  /* --- Init ------------------------------------------------ */
  document.addEventListener('DOMContentLoaded', function () {
    initLanguage();
    initMobileMenu();
    initHeaderScroll();
    initFaq();
    initActiveNav();
    initSchoolFilter();
    initSmoothScroll();
  });

})();
