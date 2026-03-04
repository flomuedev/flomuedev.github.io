---
layout: default
title: Visual Stories
permalink: /visual-stories/
description: Engaging visual narratives for HCI research
---

<div class="post">
  <div class="header-bar">
    <h1>Visual Research Stories</h1>
    <h2>Bringing HCI Research to Life Through Engaging Visuals</h2>
  </div>

  <!-- Featured Visual Story -->
  <div class="featured-story mb-5">
    <div class="featured-image-container">
      <img src="{{ '/assets/img/florian_profile_square.jpg' | relative_url }}" 
           alt="Mobile Human-Computer Interaction Research" 
           class="featured-image">
      <div class="video-overlay">
        <div>
          <h3 class="mb-3">Seamless Mobile Interaction in Extended Reality</h3>
          <p class="lead">Exploring the future where digital information, AI agents, and physical environments merge into unified experiences.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Interactive Research Gallery -->
  <div class="interactive-gallery">
    {% assign selected_papers = site.data.cv.publications | where: "selected", true %}
    {% for paper in selected_papers limit: 6 %}
    <div class="gallery-item" tabindex="0">
      {% if paper.image %}
        <img src="{{ paper.image | relative_url }}" alt="{{ paper.title }}">
      {% else %}
        <!-- Generate a visual based on research area -->
        {% if paper.title contains "Virtual Reality" or paper.title contains "VR" %}
          <div class="research-visual vr-visual">
            <div class="visual-content">
              <i class="fas fa-vr-cardboard fa-3x"></i>
              <span class="topic-tag vr">VR</span>
            </div>
          </div>
        {% elsif paper.title contains "Augmented Reality" or paper.title contains "AR" %}
          <div class="research-visual ar-visual">
            <div class="visual-content">
              <i class="fas fa-cube fa-3x"></i>
              <span class="topic-tag ar">AR</span>
            </div>
          </div>
        {% elsif paper.title contains "Haptic" or paper.title contains "Touch" %}
          <div class="research-visual haptics-visual">
            <div class="visual-content">
              <i class="fas fa-hand-paper fa-3x"></i>
              <span class="topic-tag haptics">Haptics</span>
            </div>
          </div>
        {% else %}
          <div class="research-visual hci-visual">
            <div class="visual-content">
              <i class="fas fa-laptop fa-3x"></i>
              <span class="topic-tag hci">HCI</span>
            </div>
          </div>
        {% endif %}
      {% endif %}
      
      <div class="gallery-overlay">
        <h4>{{ paper.title | truncate: 60 }}</h4>
        <p>{{ paper.abstract | truncate: 120 }}</p>
        {% if paper.url %}
          <a href="{{ paper.url }}" class="btn btn-outline-light btn-sm">Read More</a>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- Research Topics Visual Guide -->
  <div class="research-topics mt-5">
    <h3>Research Areas</h3>
    <div class="row">
      <div class="col-md-6 col-lg-3 mb-4">
        <div class="topic-card">
          <div class="topic-icon vr">
            <i class="fas fa-vr-cardboard fa-2x"></i>
          </div>
          <h5>Virtual Reality</h5>
          <p>Immersive experiences and spatial interaction design</p>
          <div class="topic-keywords">
            <span class="topic-tag vr">Locomotion</span>
            <span class="topic-tag vr">Presence</span>
            <span class="topic-tag vr">Immersion</span>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-4">
        <div class="topic-card">
          <div class="topic-icon ar">
            <i class="fas fa-cube fa-2x"></i>
          </div>
          <h5>Augmented Reality</h5>
          <p>Blending digital content with physical environments</p>
          <div class="topic-keywords">
            <span class="topic-tag ar">Spatial Computing</span>
            <span class="topic-tag ar">Mixed Reality</span>
            <span class="topic-tag ar">Context Awareness</span>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-4">
        <div class="topic-card">
          <div class="topic-icon haptics">
            <i class="fas fa-hand-paper fa-2x"></i>
          </div>
          <h5>Haptic Interfaces</h5>
          <p>Touch and force feedback for enhanced interaction</p>
          <div class="topic-keywords">
            <span class="topic-tag haptics">Tactile Feedback</span>
            <span class="topic-tag haptics">Force Feedback</span>
            <span class="topic-tag haptics">Multimodal</span>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-4">
        <div class="topic-card">
          <div class="topic-icon hci">
            <i class="fas fa-laptop fa-2x"></i>
          </div>
          <h5>Mobile HCI</h5>
          <p>Seamless interaction with mobile and ubiquitous computing</p>
          <div class="topic-keywords">
            <span class="topic-tag hci">Urban Interaction</span>
            <span class="topic-tag hci">Ubiquitous Computing</span>
            <span class="topic-tag hci">AI Collaboration</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Interactive Timeline (placeholder for future AI-generated content) -->
  <div class="research-timeline mt-5">
    <h3>Research Journey</h3>
    <div class="timeline-container">
      <div class="timeline-note">
        <i class="fas fa-robot"></i>
        <p class="text-muted">Future: This section will feature AI-generated visual timelines of research milestones and discoveries.</p>
      </div>
    </div>
  </div>
</div>

<style>
.research-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: white;
  font-size: 1.2rem;
  position: relative;
}

.vr-visual {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.ar-visual {
  background: linear-gradient(135deg, #10b981, #3b82f6);
}

.haptics-visual {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
}

.hci-visual {
  background: linear-gradient(135deg, #ef4444, #f97316);
}

.visual-content {
  text-align: center;
}

.visual-content i {
  display: block;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.topic-card {
  background: white;
  border-radius: 12px;
  padding: 2rem 1.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  height: 100%;
}

.topic-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.topic-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: white;
}

.topic-icon.vr {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.topic-icon.ar {
  background: linear-gradient(135deg, #10b981, #3b82f6);
}

.topic-icon.haptics {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
}

.topic-icon.hci {
  background: linear-gradient(135deg, #ef4444, #f97316);
}

.topic-keywords {
  margin-top: 1rem;
}

.timeline-container {
  background: #f8fafc;
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
}

.timeline-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.timeline-note i {
  font-size: 2rem;
  color: #6b7280;
}
</style>