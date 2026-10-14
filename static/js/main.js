/* ==========================================================================
   main.js — flomue.com interactions
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // ---- Scroll-based header shadow ----
  const header = document.getElementById('site-header');
  if (header) {
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          header.classList.toggle('scrolled', window.scrollY > 20);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ---- Theme toggle (light / dark) ----
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const isDark = () => (document.documentElement.dataset.theme || (darkQuery.matches ? 'dark' : 'light')) === 'dark';
    const syncLabel = () => {
      themeToggle.setAttribute('aria-label', isDark() ? 'Switch to light theme' : 'Switch to dark theme');
    };
    themeToggle.addEventListener('click', () => {
      const next = isDark() ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (e) { /* storage blocked */ }
      syncLabel();
    });
    darkQuery.addEventListener('change', syncLabel);
    syncLabel();
  }

  // ---- Mobile nav toggle ----
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');
  if (navToggle && navLinks) {
    const setNavOpen = (open) => {
      navLinks.classList.toggle('open', open);
      navToggle.classList.toggle('active', open);
      navToggle.setAttribute('aria-expanded', String(open));
    };
    navToggle.addEventListener('click', () => {
      setNavOpen(!navLinks.classList.contains('open'));
    });
    // Close on link click
    navLinks.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => setNavOpen(false));
    });
  }

  // ---- Fade-in on scroll (Intersection Observer) ----
  const fadeEls = document.querySelectorAll('.fade-in');
  if (!('IntersectionObserver' in window)) {
    // No observer: reveal everything instead of leaving it hidden
    document.querySelectorAll('.fade-in, .stagger > *').forEach(el => el.classList.add('visible'));
  }
  if (fadeEls.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );
    fadeEls.forEach(el => observer.observe(el));
  }

  // ---- Stagger children animation ----
  const staggerContainers = document.querySelectorAll('.stagger');
  if (staggerContainers.length > 0 && 'IntersectionObserver' in window) {
    const staggerObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const children = entry.target.children;
            Array.from(children).forEach((child, i) => {
              setTimeout(() => {
                child.classList.add('visible');
              }, i * 80);
            });
            staggerObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05 }
    );
    staggerContainers.forEach(el => staggerObserver.observe(el));
  }

  // ---- Publication search + filters (state mirrored in the URL) ----
  // URL params: q, pillar, venue, since, has (comma-separated: pdf,video,code,data)
  const searchInput = document.getElementById('pub-search');
  const pubCards = document.querySelectorAll('.pub-card');
  const yearGroups = document.querySelectorAll('.pub-year-group');
  const pubCount = document.getElementById('pub-count');
  const pillarButtons = document.querySelectorAll('.pillar-filter-btn');
  const venueSelect = document.getElementById('pub-venue');
  const sinceSelect = document.getElementById('pub-since');
  const hasButtons = document.querySelectorAll('.pub-has-btn');
  const resetButton = document.getElementById('pub-reset');

  if (pubCards.length > 0) {
    const state = { q: '', pillar: '', venue: '', since: '', has: [] };
    const optionValues = sel => sel ? Array.from(sel.options, o => o.value).filter(Boolean) : [];
    const validPillars = Array.from(pillarButtons, b => b.dataset.pillarFilter).filter(Boolean);
    const validHas = Array.from(hasButtons, b => b.dataset.has);

    // Read and validate the initial state from the URL
    const params = new URLSearchParams(window.location.search);
    const pick = (name, allowed) => (allowed.includes(params.get(name)) ? params.get(name) : '');
    state.q = (params.get('q') || '').trim();
    state.pillar = pick('pillar', validPillars);
    state.venue = pick('venue', optionValues(venueSelect));
    state.since = pick('since', optionValues(sinceSelect));
    state.has = (params.get('has') || '').split(',').filter(h => validHas.includes(h));

    function isFiltered() {
      return Boolean(state.q || state.pillar || state.venue || state.since || state.has.length);
    }

    function syncControls() {
      if (searchInput) searchInput.value = state.q;
      if (venueSelect) venueSelect.value = state.venue;
      if (sinceSelect) sinceSelect.value = state.since;
      pillarButtons.forEach(b => {
        const active = b.dataset.pillarFilter === state.pillar;
        b.classList.toggle('active', active);
        b.setAttribute('aria-pressed', String(active));
      });
      hasButtons.forEach(b => {
        const active = state.has.includes(b.dataset.has);
        b.classList.toggle('active', active);
        b.setAttribute('aria-pressed', String(active));
      });
      if (resetButton) resetButton.hidden = !isFiltered();
    }

    function writeUrl() {
      const p = new URLSearchParams();
      if (state.q) p.set('q', state.q);
      if (state.pillar) p.set('pillar', state.pillar);
      if (state.venue) p.set('venue', state.venue);
      if (state.since) p.set('since', state.since);
      if (state.has.length) p.set('has', state.has.join(','));
      const qs = p.toString();
      history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname);
    }

    function applyFilters() {
      const query = state.q.toLowerCase();
      const since = state.since ? Number(state.since) : 0;
      let visibleCount = 0;
      pubCards.forEach(card => {
        const has = (card.dataset.has || '').split(' ');
        const show = (!query || card.textContent.toLowerCase().includes(query))
          && (!state.pillar || (card.dataset.pillar || '').split(' ').includes(state.pillar))
          && (!state.venue || card.dataset.venue === state.venue)
          && (!since || Number(card.dataset.year) >= since)
          && state.has.every(h => has.includes(h));
        card.hidden = !show;
        if (show) visibleCount++;
      });
      yearGroups.forEach(group => {
        group.hidden = !group.querySelector('.pub-card:not([hidden])');
      });
      if (pubCount) pubCount.textContent = `${visibleCount} publication${visibleCount !== 1 ? 's' : ''}`;
    }

    function update() {
      syncControls();
      applyFilters();
      writeUrl();
    }

    pillarButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const pillar = btn.dataset.pillarFilter;
        state.pillar = state.pillar === pillar ? '' : pillar;
        update();
      });
    });
    hasButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const h = btn.dataset.has;
        state.has = state.has.includes(h) ? state.has.filter(x => x !== h) : [...state.has, h];
        update();
      });
    });
    if (venueSelect) venueSelect.addEventListener('change', () => { state.venue = venueSelect.value; update(); });
    if (sinceSelect) sinceSelect.addEventListener('change', () => { state.since = sinceSelect.value; update(); });
    if (searchInput) searchInput.addEventListener('input', () => { state.q = searchInput.value.trim(); update(); });
    if (resetButton) {
      resetButton.addEventListener('click', () => {
        Object.assign(state, { q: '', pillar: '', venue: '', since: '', has: [] });
        update();
        if (searchInput) searchInput.focus();
      });
    }

    syncControls();
    if (isFiltered()) {
      applyFilters();
      document.querySelector('.pillar-filters')?.scrollIntoView({ block: 'start' });
    }
  }

  // ---- BibTeX Modal ----
  const bibtexModal = document.getElementById('bibtex-modal');
  if (bibtexModal) {
    const bibtexContent = document.getElementById('bibtex-modal-content');
    const bibtexCopyBtn = bibtexModal.querySelector('.bibtex-copy-btn');
    const bibtexClose = bibtexModal.querySelector('.bibtex-modal-close');
    const bibtexOverlay = bibtexModal.querySelector('.bibtex-modal-overlay');
    let lastFocused = null;

    function openBibtex(text) {
      lastFocused = document.activeElement;
      bibtexContent.textContent = text;
      bibtexModal.hidden = false;
      document.body.style.overflow = 'hidden';
      bibtexCopyBtn.textContent = 'Copy to clipboard';
      bibtexCopyBtn.classList.remove('copied');
      bibtexCopyBtn.focus();
    }

    function closeBibtex() {
      if (bibtexModal.hidden) return;
      bibtexModal.hidden = true;
      document.body.style.overflow = '';
      if (lastFocused) lastFocused.focus();
    }

    // Keep Tab focus inside the dialog while it is open
    bibtexModal.addEventListener('keydown', e => {
      if (e.key !== 'Tab') return;
      const focusable = [bibtexClose, bibtexCopyBtn];
      const i = focusable.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); focusable[focusable.length - 1].focus(); }
      else if (!e.shiftKey && i === focusable.length - 1) { e.preventDefault(); focusable[0].focus(); }
    });

    let bibCache = null;
    async function fetchBib(key) {
      if (!bibCache) {
        const r = await fetch('/bib.json');
        bibCache = await r.json();
      }
      return bibCache[key] || '';
    }

    document.querySelectorAll('.bibtex-trigger').forEach(btn => {
      btn.addEventListener('click', async () => {
        const text = await fetchBib(btn.dataset.key);
        openBibtex(text);
      });
    });

    bibtexClose.addEventListener('click', closeBibtex);
    bibtexOverlay.addEventListener('click', closeBibtex);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeBibtex(); });

    bibtexCopyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(bibtexContent.textContent).then(() => {
        bibtexCopyBtn.textContent = 'Copied!';
        bibtexCopyBtn.classList.add('copied');
        setTimeout(() => {
          bibtexCopyBtn.textContent = 'Copy to clipboard';
          bibtexCopyBtn.classList.remove('copied');
        }, 2000);
      });
    });
  }

  // ---- GDPR Video Embeds ----
  const videoContainers = document.querySelectorAll('.gdpr-video-container');
  videoContainers.forEach(container => {
    const playBtn = container.querySelector('.btn-play-video');
    const overlay = container.querySelector('.gdpr-overlay');

    if (playBtn && overlay) {
      playBtn.addEventListener('click', () => {
        const youtubeId = container.getAttribute('data-youtube-id');
        if (youtubeId) {
          // Remove the overlay
          overlay.remove();

          // Create and inject the iframe
          const iframe = document.createElement('iframe');
          iframe.src = `https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1`;
          iframe.title = container.dataset.title || 'YouTube video player';
          iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
          iframe.setAttribute('allowfullscreen', 'true');

          container.appendChild(iframe);
          iframe.focus();
        }
      });
    }
  });
});
