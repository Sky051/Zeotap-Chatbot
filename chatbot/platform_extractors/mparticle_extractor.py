from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
from .base_extractor import BaseExtractor

class MParticleExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://docs.mparticle.com/'
        self.doc_sections = {
            'source_setup': [
                '/developers/sdk/',
                '/integrations/data-sources/',
                '/guides/platform-guide/data-sources/'
            ],
            'profile_creation': [
                '/guides/platform-guide/profiles/',
                '/guides/platform-guide/users/',
                '/guides/platform-guide/identity/'
            ],
            'audience_segment': [
                '/guides/platform-guide/audiences/',
                '/guides/platform-guide/segments/',
                '/guides/platform-guide/calculated-attributes/'
            ],
            'data_integration': [
                '/integrations/',
                '/developers/integration/',
                '/guides/platform-guide/connections/'
            ]
        }

    def get_base_url(self) -> str:
        return self.base_url

    def get_platform_name(self) -> str:
        return 'mparticle'

    def extract_docs(self, task: str, relevant_sections: List[str]) -> List[Dict]:
        """
        Extract documentation for a specific task from mParticle's documentation
        
        Args:
            task (str): The task type
            relevant_sections (List[str]): List of relevant section keywords
            
        Returns:
            List[Dict]: List of relevant documentation snippets
        """
        # Check cache first
        cached_data = self._get_cached_data(task)
        if cached_data:
            return cached_data

        results = []
        
        # Get the relevant documentation paths for the task
        doc_paths = self.doc_sections.get(task, [])
        
        for path in doc_paths:
            url = self.base_url.rstrip('/') + path
            content = self._fetch_url(url)
            
            if not content:
                continue
            
            # Parse the HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find relevant sections based on headers and content
            relevant_elements = []
            
            # Look for headers and their associated content
            for section in relevant_sections:
                # Find headers that match our relevant sections
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4'], 
                                     string=re.compile(section, re.IGNORECASE))
                
                for header in headers:
                    # Get the content following this header until the next header
                    content_elements = []
                    current = header.find_next()
                    
                    while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                        if current.name in ['p', 'ul', 'ol', 'pre', 'code', 'div']:
                            # Check if it's a relevant div (e.g., content blocks in mParticle docs)
                            if current.name != 'div' or current.get('class', [''])[0] in ['content', 'description']:
                                content_elements.append(current)
                        current = current.find_next()
                    
                    if content_elements:
                        relevant_elements.extend(content_elements)
            
            # Process found elements
            for element in relevant_elements:
                content = self._extract_text_from_html(str(element))
                
                # Calculate relevance based on keyword matches
                relevance = self._calculate_relevance(content, relevant_sections)
                
                if relevance > 0:
                    # Extract any code examples if present
                    code_examples = self._extract_code_examples(str(element))
                    
                    result = {
                        'content': content,
                        'url': url,
                        'relevance': relevance
                    }
                    
                    if code_examples:
                        result['code_examples'] = code_examples
                    
                    results.append(result)
        
        # Cache the results
        if results:
            self._cache_data(task, results)
        
        return results

    def search(self, query: str) -> List[Dict]:
        """
        mParticle-specific search implementation
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: Relevant documentation snippets
        """
        # First try to get cached search results
        cache_key = f"search_{hash(query)}"
        cached_results = self._get_cached_data(cache_key)
        if cached_results:
            return cached_results

        # If not in cache, perform the search
        results = []
        keywords = query.lower().split()
        
        # Search through all known documentation sections
        for task, paths in self.doc_sections.items():
            for path in paths:
                url = self.base_url.rstrip('/') + path
                content = self._fetch_url(url)
                
                if not content:
                    continue
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find content elements including mParticle-specific content blocks
                elements = soup.find_all(['p', 'li', 'pre', 'code', 'div'])
                
                for element in elements:
                    # Only process divs that are content blocks
                    if element.name == 'div' and element.get('class', [''])[0] not in ['content', 'description']:
                        continue
                    
                    text = self._extract_text_from_html(str(element))
                    relevance = self._calculate_relevance(text, keywords)
                    
                    if relevance > 0:
                        result = {
                            'content': text,
                            'url': url,
                            'relevance': relevance
                        }
                        
                        # Add code examples if present
                        code_examples = self._extract_code_examples(str(element))
                        if code_examples:
                            result['code_examples'] = code_examples
                        
                        results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Cache the results
        self._cache_data(cache_key, results)
        
        return results

    def _extract_code_examples(self, html_content: str) -> List[str]:
        """
        Extract code examples from HTML content
        
        Args:
            html_content (str): HTML content
            
        Returns:
            List[str]: List of code examples
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        code_blocks = []
        
        # Find all code blocks, including mParticle-specific code containers
        for code in soup.find_all(['pre', 'code', 'div'], class_=['highlight', 'code-block']):
            code_text = code.get_text().strip()
            if code_text:
                code_blocks.append(code_text)
        
        return code_blocks
