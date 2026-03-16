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

  // ---- Mobile nav toggle ----
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      navToggle.classList.toggle('active');
    });
    // Close on link click
    navLinks.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        navToggle.classList.remove('active');
      });
    });
  }

  // ---- Fade-in on scroll (Intersection Observer) ----
  const fadeEls = document.querySelectorAll('.fade-in');
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

  // ---- Publication search + pillar filter ----
  const searchInput = document.getElementById('pub-search');
  const pubCards = document.querySelectorAll('.pub-card');
  const yearGroups = document.querySelectorAll('.pub-year-group');
  const pubCount = document.getElementById('pub-count');
  const pillarButtons = document.querySelectorAll('.pillar-filter-btn');

  if (pubCards.length > 0) {
    let activePillar = '';

    function applyFilters() {
      const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
      let visibleCount = 0;
      pubCards.forEach(card => {
        const textMatch = !query || card.textContent.toLowerCase().includes(query);
        const pillarMatch = !activePillar || (card.dataset.pillar || '').split(' ').includes(activePillar);
        const show = textMatch && pillarMatch;
        card.style.display = show ? '' : 'none';
        if (show) visibleCount++;
      });
      yearGroups.forEach(group => {
        const visible = group.querySelectorAll('.pub-card:not([style*="display: none"])');
        group.style.display = visible.length > 0 ? '' : 'none';
      });
      if (pubCount) pubCount.textContent = `${visibleCount} publication${visibleCount !== 1 ? 's' : ''}`;
    }

    // Read URL param on page load
    const validPillars = ['xr', 'mobile', 'embodied', 'ai'];
    const urlPillar = validPillars.includes(new URLSearchParams(window.location.search).get('pillar'))
      ? new URLSearchParams(window.location.search).get('pillar') : '';
    if (urlPillar) {
      activePillar = urlPillar;
      const activeBtn = document.querySelector(`[data-pillar-filter="${urlPillar}"]`);
      if (activeBtn) activeBtn.classList.add('active');
      document.querySelector('.pillar-filter-btn--all')?.classList.remove('active');
      applyFilters();
      document.querySelector('.pillar-filters')?.scrollIntoView({ block: 'start' });
    } else {
      document.querySelector('.pillar-filter-btn--all')?.classList.add('active');
    }

    // Pillar button clicks
    pillarButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const pillar = btn.dataset.pillarFilter;
        activePillar = activePillar === pillar ? '' : pillar;
        pillarButtons.forEach(b => b.classList.remove('active'));
        const nextActive = activePillar
          ? document.querySelector(`[data-pillar-filter="${activePillar}"]`)
          : document.querySelector('[data-pillar-filter=""]');
        if (nextActive) nextActive.classList.add('active');
        history.replaceState(null, '', activePillar ? `?pillar=${activePillar}` : window.location.pathname);
        applyFilters();
      });
    });

    if (searchInput) searchInput.addEventListener('input', applyFilters);
  }

  // ---- BibTeX Modal ----
  const bibtexModal = document.getElementById('bibtex-modal');
  if (bibtexModal) {
    const bibtexContent = document.getElementById('bibtex-modal-content');
    const bibtexCopyBtn = bibtexModal.querySelector('.bibtex-copy-btn');
    const bibtexClose = bibtexModal.querySelector('.bibtex-modal-close');
    const bibtexOverlay = bibtexModal.querySelector('.bibtex-modal-overlay');

    function openBibtex(text) {
      bibtexContent.textContent = text;
      bibtexModal.hidden = false;
      document.body.style.overflow = 'hidden';
      bibtexCopyBtn.textContent = 'Copy to clipboard';
      bibtexCopyBtn.classList.remove('copied');
    }

    function closeBibtex() {
      bibtexModal.hidden = true;
      document.body.style.overflow = '';
    }

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
          iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
          iframe.setAttribute('allowfullscreen', 'true');

          container.appendChild(iframe);
        }
      });
    }
  });
});
