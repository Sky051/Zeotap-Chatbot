from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
from .platform_extractors.segment_extractor import SegmentExtractor
from .platform_extractors.mparticle_extractor import MParticleExtractor
from .platform_extractors.lytics_extractor import LyticsExtractor
from .platform_extractors.zeotap_extractor import ZeotapExtractor

class DocsExtractor:
    def __init__(self):
        self.extractors = {
            'segment': SegmentExtractor(),
            'mparticle': MParticleExtractor(),
            'lytics': LyticsExtractor(),
            'zeotap': ZeotapExtractor()
        }
        
        # Cache for storing documentation content
        self.docs_cache = {}
        
        # Mapping of common tasks to relevant documentation sections
        self.task_mappings = {
            'source_setup': {
                'segment': ['sources', 'setup', 'configuration'],
                'mparticle': ['sources', 'inputs', 'data-sources'],
                'lytics': ['sources', 'connections', 'inputs'],
                'zeotap': ['sources', 'integrations', 'inputs']
            },
            'profile_creation': {
                'segment': ['profiles', 'identity', 'users'],
                'mparticle': ['profiles', 'identity', 'users'],
                'lytics': ['profiles', 'identity', 'users'],
                'zeotap': ['profiles', 'identity', 'users']
            },
            'audience_segment': {
                'segment': ['audiences', 'segments', 'targeting'],
                'mparticle': ['audiences', 'segments', 'targeting'],
                'lytics': ['audiences', 'segments', 'targeting'],
                'zeotap': ['audiences', 'segments', 'targeting']
            },
            'data_integration': {
                'segment': ['integrations', 'destinations', 'connections'],
                'mparticle': ['integrations', 'outputs', 'destinations'],
                'lytics': ['integrations', 'destinations', 'connections'],
                'zeotap': ['integrations', 'destinations', 'connections']
            }
        }

    def get_relevant_docs(self, platform: str, task: str) -> List[Dict]:
        """
        Get relevant documentation for a specific platform and task
        
        Args:
            platform (str): The CDP platform name
            task (str): The task type
            
        Returns:
            List[Dict]: List of relevant documentation snippets
        """
        if not platform or not task:
            return []

        # Get the appropriate extractor
        extractor = self.extractors.get(platform)
        if not extractor:
            return []

        # Get relevant documentation sections based on task
        relevant_sections = self.task_mappings.get(task, {}).get(platform, [])
        
        # Use platform-specific extractor to get documentation
        docs = extractor.extract_docs(task, relevant_sections)
        
        return self._process_docs(docs)

    def _process_docs(self, docs: List[Dict]) -> List[Dict]:
        """
        Process and clean the extracted documentation
        
        Args:
            docs (List[Dict]): Raw documentation snippets
            
        Returns:
            List[Dict]: Processed documentation snippets
        """
        processed_docs = []
        
        for doc in docs:
            # Clean HTML tags if present
            content = BeautifulSoup(doc['content'], 'html.parser').get_text()
            
            # Remove extra whitespace
            content = ' '.join(content.split())
            
            # Add processed content
            processed_docs.append({
                'content': content,
                'relevance': doc.get('relevance', 1.0),
                'url': doc.get('url', '')
            })
        
        # Sort by relevance
        processed_docs.sort(key=lambda x: x['relevance'], reverse=True)
        
        return processed_docs

    def refresh_cache(self, platform: str = None):
        """
        Refresh the documentation cache for a specific platform or all platforms
        
        Args:
            platform (str, optional): Platform to refresh. If None, refreshes all platforms
        """
        if platform:
            if platform in self.extractors:
                self.extractors[platform].refresh_cache()
        else:
            for extractor in self.extractors.values():
                extractor.refresh_cache()

    def search_docs(self, query: str, platform: str = None) -> List[Dict]:
        """
        Search through documentation using a free-text query
        
        Args:
            query (str): Search query
            platform (str, optional): Limit search to specific platform
            
        Returns:
            List[Dict]: Relevant documentation snippets
        """
        results = []
        
        # Determine which platforms to search
        platforms = [platform] if platform else self.extractors.keys()
        
        # Search each platform
        for p in platforms:
            extractor = self.extractors.get(p)
            if extractor:
                platform_results = extractor.search(query)
                results.extend(platform_results)
        
        # Sort results by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return self._process_docs(results)
