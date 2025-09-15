#!/usr/bin/env python3
"""
Stock Media Manager for flomuedev.github.io

This script helps download and manage free stock media from various sources
like Unsplash, Pexels, and Pixabay for use in the website.

Usage:
    python stock_media_manager.py --source unsplash --query "technology hci" --count 5
    python stock_media_manager.py --source pexels --query "virtual reality" --count 3
"""

import os
import sys
import argparse
import requests
from urllib.parse import urlencode
import json
from pathlib import Path

class StockMediaManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.assets_dir = self.base_dir / "assets"
        self.img_dir = self.assets_dir / "img" / "stock"
        self.video_dir = self.assets_dir / "video" / "stock"
        
        # Create directories if they don't exist
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        # API configurations (these would typically be set via environment variables)
        self.apis = {
            'unsplash': {
                'base_url': 'https://api.unsplash.com',
                'key': os.environ.get('UNSPLASH_ACCESS_KEY'),
                'required': True
            },
            'pexels': {
                'base_url': 'https://api.pexels.com/v1',
                'key': os.environ.get('PEXELS_API_KEY'),
                'required': True
            },
            'pixabay': {
                'base_url': 'https://pixabay.com/api',
                'key': os.environ.get('PIXABAY_API_KEY'),
                'required': False  # Has a public tier
            }
        }

    def search_unsplash(self, query, count=5, orientation='landscape'):
        """Search for images on Unsplash"""
        if not self.apis['unsplash']['key']:
            print("Warning: No Unsplash API key found. Using sample data.")
            return self._get_sample_unsplash_data(query, count)
        
        url = f"{self.apis['unsplash']['base_url']}/search/photos"
        params = {
            'query': query,
            'per_page': min(count, 30),
            'orientation': orientation
        }
        
        headers = {
            'Authorization': f"Client-ID {self.apis['unsplash']['key']}"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching from Unsplash: {e}")
            return self._get_sample_unsplash_data(query, count)

    def search_pexels(self, query, count=5, media_type='photos'):
        """Search for media on Pexels"""
        if not self.apis['pexels']['key']:
            print("Warning: No Pexels API key found. Using sample data.")
            return self._get_sample_pexels_data(query, count, media_type)
        
        endpoint = 'search' if media_type == 'photos' else 'videos/search'
        url = f"{self.apis['pexels']['base_url']}/{endpoint}"
        
        params = {
            'query': query,
            'per_page': min(count, 80)
        }
        
        headers = {
            'Authorization': self.apis['pexels']['key']
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching from Pexels: {e}")
            return self._get_sample_pexels_data(query, count, media_type)

    def download_media(self, url, filename, media_type='image'):
        """Download media file from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            target_dir = self.img_dir if media_type == 'image' else self.video_dir
            file_path = target_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {filename}")
            return file_path
        except requests.RequestException as e:
            print(f"Error downloading {filename}: {e}")
            return None

    def curate_research_visuals(self, research_topics):
        """Curate visual content for specific research topics"""
        curated_content = {}
        
        for topic in research_topics:
            print(f"Curating content for: {topic}")
            
            # Search for relevant images
            unsplash_results = self.search_unsplash(f"{topic} technology research", count=3)
            pexels_results = self.search_pexels(f"{topic} interface design", count=2)
            
            curated_content[topic] = {
                'images': [],
                'suggested_animations': self._suggest_animations(topic),
                'color_palette': self._suggest_color_palette(topic)
            }
            
            # Process Unsplash results
            if 'results' in unsplash_results:
                for img in unsplash_results['results'][:2]:
                    curated_content[topic]['images'].append({
                        'source': 'unsplash',
                        'url': img.get('urls', {}).get('regular', ''),
                        'description': img.get('description', ''),
                        'photographer': img.get('user', {}).get('name', ''),
                        'download_url': img.get('links', {}).get('download', '')
                    })
            
            # Process Pexels results
            if 'photos' in pexels_results:
                for img in pexels_results['photos'][:1]:
                    curated_content[topic]['images'].append({
                        'source': 'pexels',
                        'url': img.get('src', {}).get('large', ''),
                        'description': img.get('alt', ''),
                        'photographer': img.get('photographer', ''),
                        'download_url': img.get('src', {}).get('original', '')
                    })
        
        return curated_content

    def _suggest_animations(self, topic):
        """Suggest animation types based on research topic"""
        animations = {
            'virtual reality': ['fade transitions', 'parallax scrolling', '3D transforms'],
            'augmented reality': ['overlay effects', 'depth transitions', 'gesture animations'],
            'human computer interaction': ['hover effects', 'progressive disclosure', 'smooth transitions'],
            'haptic feedback': ['vibration patterns', 'wave animations', 'spring physics'],
            'default': ['pan and zoom', 'fade effects', 'slide transitions']
        }
        
        for key in animations:
            if key.lower() in topic.lower():
                return animations[key]
        return animations['default']

    def _suggest_color_palette(self, topic):
        """Suggest color palettes based on research topic"""
        palettes = {
            'virtual reality': ['#6366f1', '#8b5cf6', '#06b6d4'],  # Purple-blue tech
            'augmented reality': ['#10b981', '#3b82f6', '#f59e0b'],  # Green-blue-orange
            'human computer interaction': ['#ef4444', '#f97316', '#eab308'],  # Warm spectrum
            'haptic feedback': ['#8b5cf6', '#d946ef', '#06b6d4'],  # Purple-magenta-cyan
            'default': ['#3b82f6', '#10b981', '#f59e0b']  # Blue-green-orange
        }
        
        for key in palettes:
            if key.lower() in topic.lower():
                return palettes[key]
        return palettes['default']

    def _get_sample_unsplash_data(self, query, count):
        """Provide sample data when API is not available"""
        return {
            'results': [
                {
                    'urls': {'regular': f'https://source.unsplash.com/800x600/?{query.replace(" ", ",")}&sig={i}'},
                    'description': f'Sample {query} image {i+1}',
                    'user': {'name': 'Sample Photographer'},
                    'links': {'download': f'https://source.unsplash.com/1200x800/?{query.replace(" ", ",")}&sig={i}'}
                }
                for i in range(count)
            ]
        }

    def _get_sample_pexels_data(self, query, count, media_type):
        """Provide sample data when API is not available"""
        if media_type == 'photos':
            return {
                'photos': [
                    {
                        'src': {
                            'large': f'https://picsum.photos/800/600?random={i}',
                            'original': f'https://picsum.photos/1200/800?random={i}'
                        },
                        'alt': f'Sample {query} image {i+1}',
                        'photographer': 'Sample Photographer'
                    }
                    for i in range(count)
                ]
            }
        else:
            return {'videos': []}

def main():
    parser = argparse.ArgumentParser(description='Manage stock media for the website')
    parser.add_argument('--source', choices=['unsplash', 'pexels', 'pixabay'], 
                       default='unsplash', help='Media source')
    parser.add_argument('--query', help='Search query (required unless using --curate)')
    parser.add_argument('--count', type=int, default=5, help='Number of items to fetch')
    parser.add_argument('--type', choices=['photos', 'videos'], default='photos', 
                       help='Media type')
    parser.add_argument('--download', action='store_true', 
                       help='Download the media files')
    parser.add_argument('--curate', action='store_true',
                       help='Curate content for research topics')
    
    args = parser.parse_args()
    
    manager = StockMediaManager()
    
    if args.curate:
        # Curate content for common research topics
        topics = [
            'virtual reality',
            'augmented reality', 
            'human computer interaction',
            'haptic feedback',
            'mobile interaction'
        ]
        results = manager.curate_research_visuals(topics)
        
        # Save curation results
        with open(manager.base_dir / 'curated_media.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Curated content saved to curated_media.json")
        return
    
    # Validate query for non-curate operations
    if not args.query:
        parser.error("--query is required unless using --curate")
    
    # Search for media
    if args.source == 'unsplash':
        results = manager.search_unsplash(args.query, args.count)
        if 'results' in results:
            print(f"Found {len(results['results'])} images on Unsplash")
            if args.download:
                for i, img in enumerate(results['results']):
                    url = img.get('urls', {}).get('regular', '')
                    if url:
                        filename = f"unsplash_{args.query.replace(' ', '_')}_{i+1}.jpg"
                        manager.download_media(url, filename)
    
    elif args.source == 'pexels':
        results = manager.search_pexels(args.query, args.count, args.type)
        media_key = 'photos' if args.type == 'photos' else 'videos'
        if media_key in results:
            print(f"Found {len(results[media_key])} {args.type} on Pexels")
            if args.download:
                for i, item in enumerate(results[media_key]):
                    if args.type == 'photos':
                        url = item.get('src', {}).get('large', '')
                        ext = 'jpg'
                        media_type = 'image'
                    else:
                        url = item.get('video_files', [{}])[0].get('link', '')
                        ext = 'mp4'
                        media_type = 'video'
                    
                    if url:
                        filename = f"pexels_{args.query.replace(' ', '_')}_{i+1}.{ext}"
                        manager.download_media(url, filename, media_type)

if __name__ == '__main__':
    main()