/**
 * Dynamic Visual Content Manager
 * Handles animations, progressive loading, and interactive visual elements
 */

class VisualContentManager {
  constructor() {
    this.intersectionObserver = null;
    this.lazyImages = [];
    this.animatedElements = [];
    this.init();
  }

  init() {
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupComponents());
    } else {
      this.setupComponents();
    }
  }

  setupComponents() {
    this.setupLazyLoading();
    this.setupAnimations();
    this.setupInteractiveGallery();
    this.setupProgressiveImages();
    this.setupResearchVisuals();
  }

  /**
   * Setup lazy loading for images and videos
   */
  setupLazyLoading() {
    if ('IntersectionObserver' in window) {
      this.intersectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadLazyElement(entry.target);
            this.intersectionObserver.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '50px'
      });

      // Observe all lazy elements
      document.querySelectorAll('[data-lazy-src]').forEach(element => {
        this.intersectionObserver.observe(element);
      });
    } else {
      // Fallback for browsers without IntersectionObserver
      document.querySelectorAll('[data-lazy-src]').forEach(element => {
        this.loadLazyElement(element);
      });
    }
  }

  /**
   * Load lazy element (image or video)
   */
  loadLazyElement(element) {
    const lazySrc = element.getAttribute('data-lazy-src');
    if (lazySrc) {
      if (element.tagName === 'IMG') {
        element.src = lazySrc;
        element.classList.add('loaded');
      } else if (element.tagName === 'VIDEO') {
        element.src = lazySrc;
        element.load();
      }
      element.removeAttribute('data-lazy-src');
    }
  }

  /**
   * Setup scroll-triggered animations
   */
  setupAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if ('IntersectionObserver' in window) {
      const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animated');
            animationObserver.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.1
      });

      animatedElements.forEach(element => {
        animationObserver.observe(element);
      });
    }
  }

  /**
   * Setup interactive gallery functionality
   */
  setupInteractiveGallery() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
      // Add click handler for full-screen view
      item.addEventListener('click', (e) => {
        this.openFullscreenView(item);
      });

      // Add keyboard navigation
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.openFullscreenView(item);
        }
      });

      // Add hover effects for videos
      const video = item.querySelector('video');
      if (video) {
        item.addEventListener('mouseenter', () => {
          video.play().catch(() => {
            // Ignore play errors (autoplay restrictions)
          });
        });

        item.addEventListener('mouseleave', () => {
          video.pause();
          video.currentTime = 0;
        });
      }
    });
  }

  /**
   * Open fullscreen view for gallery item
   */
  openFullscreenView(item) {
    const modal = this.createModal();
    const content = item.querySelector('img, video').cloneNode(true);
    const overlay = item.querySelector('.gallery-overlay');
    
    content.classList.add('fullscreen-content');
    modal.querySelector('.modal-body').appendChild(content);
    
    if (overlay) {
      const overlayClone = overlay.cloneNode(true);
      overlayClone.classList.remove('gallery-overlay');
      overlayClone.classList.add('fullscreen-overlay');
      modal.querySelector('.modal-body').appendChild(overlayClone);
    }
    
    document.body.appendChild(modal);
    modal.classList.add('show');
    
    // Focus management for accessibility
    modal.querySelector('.modal-close').focus();
  }

  /**
   * Create modal structure
   */
  createModal() {
    const modal = document.createElement('div');
    modal.className = 'fullscreen-modal';
    modal.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-content">
          <button class="modal-close" aria-label="Close fullscreen view">
            <i class="fas fa-times"></i>
          </button>
          <div class="modal-body"></div>
        </div>
      </div>
    `;
    
    // Close handlers
    modal.querySelector('.modal-close').addEventListener('click', () => {
      this.closeModal(modal);
    });
    
    modal.querySelector('.modal-backdrop').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.closeModal(modal);
      }
    });
    
    // Keyboard handler
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeModal(modal);
      }
    });
    
    return modal;
  }

  /**
   * Close modal
   */
  closeModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(modal);
    }, 300);
  }

  /**
   * Setup progressive image loading
   */
  setupProgressiveImages() {
    const progressiveImages = document.querySelectorAll('.progressive-image img');
    
    progressiveImages.forEach(img => {
      const container = img.closest('.progressive-image');
      
      if (img.complete) {
        container.classList.remove('loading');
      } else {
        container.classList.add('loading');
        
        img.addEventListener('load', () => {
          container.classList.remove('loading');
        });
        
        img.addEventListener('error', () => {
          container.classList.remove('loading');
          container.classList.add('error');
        });
      }
    });
  }

  /**
   * Setup research visual interactions
   */
  setupResearchVisuals() {
    const topicCards = document.querySelectorAll('.topic-card');
    
    topicCards.forEach(card => {
      card.addEventListener('click', () => {
        this.showTopicDetails(card);
      });
    });
  }

  /**
   * Show topic details (placeholder for future AI integration)
   */
  showTopicDetails(card) {
    const topic = card.querySelector('h5').textContent;
    const description = card.querySelector('p').textContent;
    
    // For now, show a simple alert
    // In the future, this could trigger AI content generation
    console.log(`Topic: ${topic}\nDescription: ${description}`);
    
    // Placeholder for AI-generated content
    this.showTopicModal(topic, description);
  }

  /**
   * Show topic modal with details
   */
  showTopicModal(topic, description) {
    const modal = document.createElement('div');
    modal.className = 'topic-modal';
    modal.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-content">
          <div class="modal-header">
            <h3>${topic}</h3>
            <button class="modal-close" aria-label="Close">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <p>${description}</p>
            <div class="ai-content-placeholder">
              <i class="fas fa-robot fa-2x mb-3"></i>
              <p class="text-muted">AI-generated visual content and insights would appear here when OpenAI API is configured.</p>
              <div class="research-papers">
                <h5>Related Research</h5>
                <p class="text-muted">Related papers and projects would be automatically curated here.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Close handlers
    modal.querySelector('.modal-close').addEventListener('click', () => {
      this.closeModal(modal);
    });
    
    modal.querySelector('.modal-backdrop').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.closeModal(modal);
      }
    });
    
    document.body.appendChild(modal);
    modal.classList.add('show');
  }

  /**
   * Generate dynamic visual content for research papers
   */
  generatePaperVisuals(paperData) {
    // This would integrate with OpenAI API in the future
    const visualElement = document.createElement('div');
    visualElement.className = 'generated-visual';
    
    // For now, create placeholder content based on keywords
    const keywords = paperData.keywords || [];
    const theme = this.detectResearchTheme(keywords);
    
    visualElement.innerHTML = `
      <div class="visual-content ${theme}">
        <div class="visual-icon">
          ${this.getThemeIcon(theme)}
        </div>
        <div class="visual-text">
          <h4>${paperData.title}</h4>
          <p>${paperData.abstract.substring(0, 150)}...</p>
        </div>
      </div>
    `;
    
    return visualElement;
  }

  /**
   * Detect research theme from keywords
   */
  detectResearchTheme(keywords) {
    const keywordString = keywords.join(' ').toLowerCase();
    
    if (keywordString.includes('virtual reality') || keywordString.includes('vr')) {
      return 'vr';
    } else if (keywordString.includes('augmented reality') || keywordString.includes('ar')) {
      return 'ar';
    } else if (keywordString.includes('haptic') || keywordString.includes('touch')) {
      return 'haptics';
    } else {
      return 'hci';
    }
  }

  /**
   * Get icon for research theme
   */
  getThemeIcon(theme) {
    const icons = {
      'vr': '<i class="fas fa-vr-cardboard"></i>',
      'ar': '<i class="fas fa-cube"></i>',
      'haptics': '<i class="fas fa-hand-paper"></i>',
      'hci': '<i class="fas fa-laptop"></i>'
    };
    
    return icons[theme] || icons['hci'];
  }

  /**
   * Add pan and zoom effect to images
   */
  addPanZoomEffect(imageSelector) {
    const images = document.querySelectorAll(imageSelector);
    
    images.forEach(img => {
      img.classList.add('pan-zoom-image');
      
      // Add container if not present
      if (!img.parentElement.classList.contains('image-container')) {
        const container = document.createElement('div');
        container.className = 'image-container';
        img.parentNode.insertBefore(container, img);
        container.appendChild(img);
      }
    });
  }
}

// Initialize when the script loads
const visualManager = new VisualContentManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VisualContentManager;
} else if (typeof window !== 'undefined') {
  window.VisualContentManager = VisualContentManager;
  window.visualManager = visualManager;
}

// Add modal styles if not present
if (!document.querySelector('#visual-modal-styles')) {
  const styles = document.createElement('style');
  styles.id = 'visual-modal-styles';
  styles.textContent = `
    .fullscreen-modal,
    .topic-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 9999;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
    }
    
    .fullscreen-modal.show,
    .topic-modal.show {
      opacity: 1;
      visibility: visible;
    }
    
    .modal-backdrop {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .modal-content {
      position: relative;
      max-width: 90vw;
      max-height: 90vh;
      background: white;
      border-radius: 12px;
      overflow: hidden;
    }
    
    .fullscreen-modal .modal-content {
      background: transparent;
    }
    
    .modal-close {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: rgba(0, 0, 0, 0.5);
      color: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 10;
      transition: background 0.3s ease;
    }
    
    .modal-close:hover {
      background: rgba(0, 0, 0, 0.7);
    }
    
    .fullscreen-content {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    
    .fullscreen-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
      color: white;
      padding: 2rem;
      transform: none;
    }
    
    .topic-modal .modal-header {
      padding: 1.5rem;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .topic-modal .modal-body {
      padding: 1.5rem;
    }
    
    .ai-content-placeholder {
      background: #f8fafc;
      border-radius: 8px;
      padding: 2rem;
      text-align: center;
      margin-top: 1.5rem;
    }
    
    .animate-on-scroll {
      opacity: 0;
      transform: translateY(30px);
      transition: all 0.6s ease;
    }
    
    .animate-on-scroll.animated {
      opacity: 1;
      transform: translateY(0);
    }
  `;
  document.head.appendChild(styles);
}