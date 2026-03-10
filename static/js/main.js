/* ==========================================================================
   main.js — flomue.com interactions
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // ---- Scroll-based header shadow ----
  const header = document.getElementById('site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('scrolled', window.scrollY > 20);
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

  // ---- Publication search / filter ----
  const searchInput = document.getElementById('pub-search');
  const pubCards = document.querySelectorAll('.pub-card');
  const yearGroups = document.querySelectorAll('.pub-year-group');
  const pubCount = document.getElementById('pub-count');

  if (searchInput && pubCards.length > 0) {
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase().trim();
      let visibleCount = 0;

      pubCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const match = !query || text.includes(query);
        card.style.display = match ? '' : 'none';
        if (match) visibleCount++;
      });

      // Hide year groups with no visible cards
      yearGroups.forEach(group => {
        const visibleCards = group.querySelectorAll('.pub-card:not([style*="display: none"])');
        group.style.display = visibleCards.length > 0 ? '' : 'none';
      });

      if (pubCount) {
        pubCount.textContent = `${visibleCount} publication${visibleCount !== 1 ? 's' : ''}`;
      }
    });
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

    document.querySelectorAll('.bibtex-trigger').forEach(btn => {
      btn.addEventListener('click', () => openBibtex(btn.getAttribute('data-bibtex')));
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
