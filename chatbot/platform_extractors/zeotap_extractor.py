from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
from .base_extractor import BaseExtractor

class ZeotapExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://docs.zeotap.com/'
        self.doc_sections = {
            'source_setup': [
                '/data-onboarding/',
                '/data-ingestion/',
                '/getting-started/data-sources/'
            ],
            'profile_creation': [
                '/identity/',
                '/user-profiles/',
                '/identity-resolution/'
            ],
            'audience_segment': [
                '/audience-builder/',
                '/segments/',
                '/targeting-rules/'
            ],
            'data_integration': [
                '/integrations/',
                '/connections/',
                '/destinations/'
            ]
        }
        
        # Zeotap-specific content identifiers
        self.content_identifiers = {
            'tutorial': {
                'classes': ['tutorial', 'guide', 'walkthrough'],
                'headers': ['Tutorial', 'Guide', 'Step by Step']
            },
            'api': {
                'classes': ['api', 'endpoint', 'reference'],
                'headers': ['API Reference', 'Endpoints', 'Methods']
            },
            'configuration': {
                'classes': ['configuration', 'settings', 'setup'],
                'headers': ['Configuration', 'Settings', 'Setup']
            }
        }

    def get_base_url(self) -> str:
        return self.base_url

    def get_platform_name(self) -> str:
        return 'zeotap'

    def extract_docs(self, task: str, relevant_sections: List[str]) -> List[Dict]:
        """
        Extract documentation for a specific task from Zeotap's documentation
        
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
            
            # Look for Zeotap-specific documentation patterns
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
                            # Check for Zeotap-specific content classes
                            if self._is_relevant_element(current):
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
                    result = {
                        'content': content,
                        'url': url,
                        'relevance': relevance,
                        'content_type': self._identify_content_type(element)
                    }
                    
                    # Add specific examples if present
                    code_examples = self._extract_code_examples(str(element))
                    if code_examples:
                        result['code_examples'] = code_examples
                    
                    api_details = self._extract_api_details(str(element))
                    if api_details:
                        result['api_details'] = api_details
                    
                    results.append(result)
        
        # Cache the results
        if results:
            self._cache_data(task, results)
        
        return results

    def search(self, query: str) -> List[Dict]:
        """
        Zeotap-specific search implementation
        
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
                
                # Find content elements including Zeotap-specific content blocks
                elements = soup.find_all(['p', 'li', 'pre', 'code', 'div'])
                
                for element in elements:
                    if not self._is_relevant_element(element):
                        continue
                    
                    text = self._extract_text_from_html(str(element))
                    relevance = self._calculate_relevance(text, keywords)
                    
                    if relevance > 0:
                        result = {
                            'content': text,
                            'url': url,
                            'relevance': relevance,
                            'content_type': self._identify_content_type(element)
                        }
                        
                        # Add specific examples if present
                        code_examples = self._extract_code_examples(str(element))
                        if code_examples:
                            result['code_examples'] = code_examples
                        
                        api_details = self._extract_api_details(str(element))
                        if api_details:
                            result['api_details'] = api_details
                        
                        results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Cache the results
        self._cache_data(cache_key, results)
        
        return results

    def _is_relevant_element(self, element) -> bool:
        """
        Check if an element is relevant based on Zeotap-specific criteria
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            bool: Whether the element is relevant
        """
        if element.name == 'div':
            element_classes = element.get('class', [])
            # Check against all known content identifier classes
            for content_type in self.content_identifiers.values():
                if any(cls in element_classes for cls in content_type['classes']):
                    return True
            return False
        return True

    def _identify_content_type(self, element) -> str:
        """
        Identify the type of content based on Zeotap-specific patterns
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            str: Content type
        """
        element_classes = element.get('class', [])
        element_text = element.get_text().lower()
        
        for content_type, identifiers in self.content_identifiers.items():
            # Check classes
            if any(cls in element_classes for cls in identifiers['classes']):
                return content_type
            
            # Check headers
            if any(header.lower() in element_text for header in identifiers['headers']):
                return content_type
        
        return 'general'

    def _extract_api_details(self, html_content: str) -> Optional[Dict]:
        """
        Extract API-specific details from HTML content
        
        Args:
            html_content (str): HTML content
            
        Returns:
            Optional[Dict]: API details if found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        api_blocks = soup.find_all(['div', 'pre', 'code'], 
                                 class_=['api', 'endpoint', 'method'])
        
        if not api_blocks:
            return None
        
        api_details = {}
        
        for block in api_blocks:
            text = block.get_text().strip()
            
            # Try to identify endpoint information
            endpoint_match = re.search(r'(GET|POST|PUT|DELETE)\s+(/[^\s]+)', text)
            if endpoint_match:
                api_details['method'] = endpoint_match.group(1)
                api_details['endpoint'] = endpoint_match.group(2)
            
            # Look for request/response examples
            if 'request' in text.lower():
                api_details['request_example'] = text
            elif 'response' in text.lower():
                api_details['response_example'] = text
        
        return api_details if api_details else None

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
        
        # Find all code blocks, including Zeotap-specific code containers
        for code in soup.find_all(['pre', 'code', 'div'], 
                                class_=['code', 'example', 'snippet', 'highlight']):
            code_text = code.get_text().strip()
            if code_text:
                code_blocks.append(code_text)
        
        return code_blocks
