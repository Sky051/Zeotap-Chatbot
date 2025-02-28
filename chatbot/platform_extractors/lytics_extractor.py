from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
import logging
from .base_extractor import BaseExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LyticsExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://docs.lytics.com/'
        self.doc_sections = {
            'source_setup': [
                '/data-sources/',
                '/integrations/sources/',
                '/getting-started/data-collection/'
            ],
            'profile_creation': [
                '/profiles/',
                '/user-identity/',
                '/identity-resolution/'
            ],
            'audience_segment': [
                '/segments/',
                '/audiences/',
                '/behavioral-scoring/',
                '/content-affinity/'
            ],
            'data_integration': [
                '/integrations/',
                '/destinations/',
                '/apis/integrations/'
            ]
        }
        
        # Lytics-specific section markers
        self.section_markers = {
            'tutorial': ['Tutorial', 'Step-by-Step Guide', 'Walkthrough'],
            'configuration': ['Configuration', 'Settings', 'Setup'],
            'api': ['API Reference', 'API Documentation', 'Endpoints'],
            'examples': ['Examples', 'Use Cases', 'Implementations']
        }
        
        # Disable caching to always fetch fresh content.
        self.use_cache = False

    def get_base_url(self) -> str:
        return self.base_url

    def get_platform_name(self) -> str:
        return 'lytics'

    def extract_docs(self, task: str, relevant_sections: List[str]) -> List[Dict]:
        """
        Extract documentation for a specific task from Lytics' documentation.
        """
        # Always bypass cache if caching is disabled.
        cached_data = self._get_cached_data(task)
        if cached_data:
            return cached_data

        results = []
        
        # For audience segmentation, limit to the primary doc page.
        if task == 'audience_segment':
            doc_paths = [self.doc_sections[task][0]]  # Use only '/segments/'
        else:
            doc_paths = self.doc_sections.get(task, [])
        
        for path in doc_paths:
            url = self.base_url.rstrip('/') + path
            page_content = self._fetch_url(url)
            if not page_content:
                logger.warning(f"Failed to fetch content from {url}")
                continue
            
            soup = BeautifulSoup(page_content, 'html.parser')
            container = soup.find('main') or soup  # Prefer main content area
            
            # Look for headers matching the relevant sections.
            relevant_elements = []
            for section in relevant_sections:
                headers = container.find_all(
                    ['h1', 'h2', 'h3', 'h4'],
                    string=re.compile(section, re.IGNORECASE)
                )
                for header in headers:
                    content_elements = []
                    current = header.find_next_sibling()
                    while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                        if current.name in ['p', 'ul', 'ol', 'pre', 'code']:
                            content_elements.append(current)
                        elif current.name == 'div':
                            classes = current.get('class', [])
                            allowed = ['content', 'documentation', 'example', 'tutorial']
                            if not classes or any(cls in allowed for cls in classes):
                                content_elements.append(current)
                        current = current.find_next_sibling()
                    if content_elements:
                        relevant_elements.extend(content_elements)
            
            # Fallback: If no specific headers were found, extract all content elements.
            if not relevant_elements:
                relevant_elements = container.find_all(['p', 'div', 'ul', 'ol', 'pre', 'code'])
            
            # Process each found element.
            for element in relevant_elements:
                extracted_text = self._extract_text_from_html(str(element))
                # Skip snippets that seem to be from Segment documentation.
                if "segment" in extracted_text.lower() and "lytics" not in extracted_text.lower():
                    continue
                
                relevance = self._calculate_relevance(extracted_text, relevant_sections)
                if relevance > 0:
                    code_examples = self._extract_code_examples(str(element))
                    config_examples = self._extract_configuration_examples(str(element))
                    result = {
                        'content': extracted_text,
                        'url': url,
                        'relevance': relevance,
                        'section_type': self._identify_section_type(element)
                    }
                    if code_examples:
                        result['code_examples'] = code_examples
                    if config_examples:
                        result['configuration_examples'] = config_examples
                    results.append(result)
        
        if results:
            self._cache_data(task, results)
        return results

    def search(self, query: str) -> List[Dict]:
        """
        Lytics-specific search implementation.
        """
        cache_key = f"search_{hash(query)}"
        cached_results = self._get_cached_data(cache_key)
        if cached_results:
            return cached_results

        results = []
        keywords = query.lower().split()
        
        for task, paths in self.doc_sections.items():
            for path in paths:
                url = self.base_url.rstrip('/') + path
                page_content = self._fetch_url(url)
                if not page_content:
                    logger.warning(f"Failed to fetch content from {url}")
                    continue
                
                soup = BeautifulSoup(page_content, 'html.parser')
                elements = soup.find_all(['p', 'li', 'pre', 'code', 'div'])
                for element in elements:
                    if element.name == 'div':
                        classes = element.get('class', [])
                        allowed = ['content', 'documentation', 'example', 'tutorial']
                        if classes and not any(cls in allowed for cls in classes):
                            continue
                    text = self._extract_text_from_html(str(element))
                    # Skip potential Segment-related snippets in audience_segment search.
                    if "segment" in text.lower() and "lytics" not in text.lower():
                        continue
                    relevance = self._calculate_relevance(text, keywords)
                    if relevance > 0:
                        result = {
                            'content': text,
                            'url': url,
                            'relevance': relevance,
                            'section_type': self._identify_section_type(element)
                        }
                        code_examples = self._extract_code_examples(str(element))
                        config_examples = self._extract_configuration_examples(str(element))
                        if code_examples:
                            result['code_examples'] = code_examples
                        if config_examples:
                            result['configuration_examples'] = config_examples
                        results.append(result)
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        self._cache_data(cache_key, results)
        return results

    def _identify_section_type(self, element) -> str:
        """
        Identify the type of documentation section.
        """
        element_text = element.get_text().lower()
        for section_type, markers in self.section_markers.items():
            for marker in markers:
                if marker.lower() in element_text:
                    return section_type
        return 'general'

    def _extract_configuration_examples(self, html_content: str) -> List[str]:
        """
        Extract configuration examples from HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        config_blocks = []
        for config in soup.find_all(['pre', 'code', 'div'], class_=['configuration', 'config', 'json', 'yaml']):
            config_text = config.get_text().strip()
            if config_text:
                config_blocks.append(config_text)
        return config_blocks

    def _extract_code_examples(self, html_content: str) -> List[str]:
        """
        Extract code examples from HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        code_blocks = []
        for code in soup.find_all(['pre', 'code', 'div'], class_=['highlight', 'code-block', 'example']):
            code_text = code.get_text().strip()
            if code_text:
                code_blocks.append(code_text)
        return code_blocks