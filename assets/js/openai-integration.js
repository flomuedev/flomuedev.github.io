/**
 * OpenAI Integration for flomuedev.github.io
 * This module provides client-side utilities for integrating with OpenAI API
 * Note: API key should be provided via environment variables or secure configuration
 */

class OpenAIIntegration {
  constructor(apiKey = null) {
    this.apiKey = apiKey || process.env.OPENAI_API_KEY;
    this.baseURL = 'https://api.openai.com/v1';
  }

  /**
   * Generate image using DALL-E
   * @param {string} prompt - The prompt for image generation
   * @param {Object} options - Additional options for image generation
   * @returns {Promise<Object>} - Generated image data
   */
  async generateImage(prompt, options = {}) {
    if (!this.apiKey) {
      throw new Error('OpenAI API key not provided');
    }

    const requestBody = {
      prompt: prompt,
      model: options.model || 'dall-e-3',
      size: options.size || '1024x1024',
      quality: options.quality || 'standard',
      n: options.n || 1
    };

    try {
      const response = await fetch(`${this.baseURL}/images/generations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating image:', error);
      throw error;
    }
  }

  /**
   * Generate text content using GPT
   * @param {string} prompt - The prompt for text generation
   * @param {Object} options - Additional options for text generation
   * @returns {Promise<Object>} - Generated text data
   */
  async generateText(prompt, options = {}) {
    if (!this.apiKey) {
      throw new Error('OpenAI API key not provided');
    }

    const requestBody = {
      model: options.model || 'gpt-3.5-turbo',
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: options.max_tokens || 150,
      temperature: options.temperature || 0.7
    };

    try {
      const response = await fetch(`${this.baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating text:', error);
      throw error;
    }
  }

  /**
   * Generate visual storytelling content for research papers
   * @param {Object} paperData - Paper metadata (title, abstract, keywords)
   * @returns {Promise<Object>} - Generated content suggestions
   */
  async generateResearchVisuals(paperData) {
    const prompt = `
    Create visual storytelling suggestions for a research paper titled "${paperData.title}".
    Abstract: ${paperData.abstract}
    Keywords: ${paperData.keywords?.join(', ') || 'N/A'}
    
    Generate:
    1. A compelling visual narrative outline
    2. Suggested image descriptions for key concepts
    3. Animation/transition ideas for presentations
    4. Color palette suggestions
    
    Focus on making complex HCI/AR/VR concepts accessible and engaging.
    `;

    return await this.generateText(prompt, {
      max_tokens: 500,
      temperature: 0.8
    });
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OpenAIIntegration;
} else if (typeof window !== 'undefined') {
  window.OpenAIIntegration = OpenAIIntegration;
}