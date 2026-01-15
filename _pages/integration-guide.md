---
layout: page
title: Site Integration Guide
permalink: /integration-guide/
description: How to integrate the new visual enhancements into your existing Jekyll site
---

# Integration Guide for Visual Enhancements

This guide shows how to integrate the new visual enhancement features into your existing Jekyll site.

## Step 1: Include CSS and JavaScript Files

Add these lines to your main layout files (e.g., `_layouts/default.html` or `_includes/head.html`):

```html
<!-- Add to the <head> section -->
<link rel="stylesheet" href="{{ '/assets/css/visual-enhancements.css' | relative_url }}">

<!-- Add before closing </body> tag -->
<script src="{{ '/assets/js/visual-content-manager.js' | relative_url }}"></script>
<script src="{{ '/assets/js/openai-integration.js' | relative_url }}"></script>
```

## Step 2: Update Publication Templates

Enhance your publication display by modifying `_layouts/bib.html` or similar templates:

```html
{% raw %}
<!-- Enhanced publication preview -->
<div class="paper-preview animate-on-scroll">
  {% if entry.preview %}
    <div class="progressive-image loading">
      <img src="{{ entry.preview | relative_url }}" 
           alt="{{ entry.title }}" 
           class="paper-preview-image">
    </div>
  {% else %}
    <!-- Auto-generate visual based on research area -->
    <div class="research-visual {% if entry.title contains 'VR' or entry.title contains 'Virtual Reality' %}vr-visual{% elsif entry.title contains 'AR' or entry.title contains 'Augmented Reality' %}ar-visual{% elsif entry.title contains 'haptic' or entry.title contains 'touch' %}haptics-visual{% else %}hci-visual{% endif %}">
      <div class="visual-content">
        {% if entry.title contains 'VR' or entry.title contains 'Virtual Reality' %}
          <i class="fas fa-vr-cardboard fa-2x"></i>
          <span class="topic-tag vr">Virtual Reality</span>
        {% elsif entry.title contains 'AR' or entry.title contains 'Augmented Reality' %}
          <i class="fas fa-cube fa-2x"></i>
          <span class="topic-tag ar">Augmented Reality</span>
        {% elsif entry.title contains 'haptic' or entry.title contains 'touch' %}
          <i class="fas fa-hand-paper fa-2x"></i>
          <span class="topic-tag haptics">Haptic Interfaces</span>
        {% else %}
          <i class="fas fa-laptop fa-2x"></i>
          <span class="topic-tag hci">HCI Research</span>
        {% endif %}
      </div>
    </div>
  {% endif %}
  
  <div class="paper-content">
    <h4>{{ entry.title }}</h4>
    <p>{{ entry.abstract | truncate: 150 }}</p>
    
    <!-- Enhanced buttons with visual indicators -->
    <div class="paper-actions">
      {% if entry.html %}
        <a href="{{ entry.html }}" class="btn btn-sm btn-outline-primary">
          <i class="fas fa-globe"></i> Paper
        </a>
      {% endif %}
      
      {% if entry.video %}
        <a href="{{ entry.video }}" class="btn btn-sm btn-outline-success">
          <i class="fas fa-play"></i> Video
        </a>
      {% endif %}
      
      {% if entry.code %}
        <a href="{{ entry.code }}" class="btn btn-sm btn-outline-info">
          <i class="fas fa-code"></i> Code
        </a>
      {% endif %}
    </div>
  </div>
</div>
{% endraw %}
```

## Step 3: Enhance Project Pages

Update your project layouts to use the new interactive gallery:

```html
{% raw %}
<!-- Interactive project gallery -->
<div class="interactive-gallery">
  {% for project in site.projects %}
    <div class="gallery-item" tabindex="0">
      {% if project.img %}
        <img src="{{ project.img | relative_url }}" 
             alt="{{ project.title }}" 
             class="pan-zoom-image">
      {% endif %}
      
      <div class="gallery-overlay">
        <h4>{{ project.title }}</h4>
        <p>{{ project.description | truncate: 100 }}</p>
        <a href="{{ project.url | relative_url }}" class="btn btn-outline-light btn-sm">
          Learn More
        </a>
      </div>
    </div>
  {% endfor %}
</div>
{% endraw %}
```

## Step 4: Add Navigation Menu Item

Add the Visual Stories page to your navigation in `_includes/header.html`:

```html
{% raw %}
<li class="nav-item {% if page.url contains 'visual-stories' %}active{% endif %}">
  <a class="nav-link" href="{{ '/visual-stories/' | relative_url }}">
    {% if page.url contains 'visual-stories' %}
      <span>Visual Stories <span class="sr-only">(current)</span></span>
    {% else %}
      Visual Stories
    {% endif %}
  </a>
</li>
{% endraw %}
```

## Step 5: Configure OpenAI Integration (Optional)

If you want to use AI-generated content, add your API key as an environment variable:

### For GitHub Pages (using Secrets):
1. Go to your repository Settings > Secrets and variables > Actions
2. Add a new secret named `OPENAI_API_KEY` with your API key
3. Update your deployment workflow to include the environment variable

### For local development:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### In your JavaScript:
```javascript
// Initialize OpenAI integration
const openai = new OpenAIIntegration();

// Example: Generate visuals for a research paper
const paperData = {
  title: "Your Research Title",
  abstract: "Your abstract text...",
  keywords: ["VR", "interaction", "design"]
};

openai.generateResearchVisuals(paperData)
  .then(result => {
    console.log("Generated visual suggestions:", result);
    // Process and display the generated content
  })
  .catch(error => {
    console.error("Error generating content:", error);
  });
```

## Step 6: Enhance About Page

Update your about page to include research topic indicators:

```html
{% raw %}
<!-- Research expertise visual indicators -->
<div class="research-expertise mt-4">
  <h4>Research Areas</h4>
  <div class="expertise-tags">
    <span class="topic-tag vr">Virtual Reality</span>
    <span class="topic-tag ar">Augmented Reality</span>
    <span class="topic-tag hci">Human-Computer Interaction</span>
    <span class="topic-tag haptics">Haptic Interfaces</span>
  </div>
</div>

<!-- Featured research with enhanced visuals -->
<div class="featured-research mt-5">
  <h4>Featured Research</h4>
  <div class="featured-image-container">
    <img src="{{ '/assets/img/your-research-image.jpg' | relative_url }}" 
         alt="Featured Research" 
         class="featured-image">
    <div class="video-overlay">
      <div class="text-center">
        <h5>Your Research Focus</h5>
        <p class="lead">Compelling description of your research vision</p>
      </div>
    </div>
  </div>
</div>
{% endraw %}
```

## Step 7: Stock Media Integration

To use the stock media manager for content curation:

```bash
# Curate research-relevant images
python stock_media_manager.py --curate

# Download specific images
python stock_media_manager.py --source unsplash --query "virtual reality research" --count 5 --download

# Download videos
python stock_media_manager.py --source pexels --query "technology innovation" --type videos --count 3 --download
```

## Step 8: Performance Optimization

Add these meta tags for better performance:

```html
<!-- Preload critical CSS -->
<link rel="preload" href="{{ '/assets/css/visual-enhancements.css' | relative_url }}" as="style">

<!-- Optimize images -->
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- Progressive Web App features -->
<meta name="theme-color" content="#3b82f6">
```

## Step 9: Accessibility Enhancements

Ensure your content is accessible:

```html
<!-- Add skip links -->
<a class="sr-only sr-only-focusable" href="#main-content">Skip to main content</a>

<!-- Proper heading hierarchy -->
<main id="main-content" role="main">
  <!-- Your content here -->
</main>

<!-- Image alt text -->
<img src="image.jpg" alt="Descriptive text for screen readers">

<!-- Video captions -->
<video controls>
  <source src="video.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English">
</video>
```

## Step 10: Testing and Validation

Test your implementation:

1. **Visual Testing**: Check that animations work smoothly
2. **Performance Testing**: Verify load times with new assets
3. **Accessibility Testing**: Use screen readers and keyboard navigation
4. **Mobile Testing**: Ensure responsive design works on all devices
5. **Cross-browser Testing**: Test on different browsers

## Troubleshooting

### Common Issues:

1. **CSS not loading**: Check file paths and Jekyll asset compilation
2. **JavaScript errors**: Verify script loading order and dependencies
3. **Images not displaying**: Check file permissions and paths
4. **Animations not working**: Verify intersection observer support
5. **API errors**: Check OpenAI API key configuration

### Debug Mode:

Add this to enable debug logging:

```javascript
// Enable debug mode
window.DEBUG_VISUAL_ENHANCEMENTS = true;

// Check console for detailed logs
console.log("Visual enhancements loaded:", window.visualManager);
```

## Next Steps

1. Customize colors and animations to match your brand
2. Add more research-specific visual indicators
3. Implement AI-generated content workflows
4. Create interactive research timelines
5. Add collaborative features for research sharing

For more detailed documentation, see [VISUAL_ENHANCEMENTS.md](VISUAL_ENHANCEMENTS.md).