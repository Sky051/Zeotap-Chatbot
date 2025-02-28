from typing import Dict, List, Optional
from venv import logger
import requests
from bs4 import BeautifulSoup
import re
from .base_extractor import BaseExtractor

class SegmentExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://segment.com/docs/'
        self.doc_sections = {
            'source_setup': ['/getting-started/sources/'],
            'profile_creation': ['/profiles/', '/personas/', '/identity-resolution/'],
            'audience_segment': ['/audiences/', '/computed-traits/', '/personas/audiences/'],
            'data_integration': ['/connections/destinations/', '/destinations/', '/integrations/']
        }
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
        }

    def get_base_url(self) -> str:
        return self.base_url

    def get_platform_name(self) -> str:
        return 'segment'

    def _fetch_url(self, url: str) -> Optional[str]:
        if "segment.com" in url:
            return self._fetch_url_with_selenium(url)  # Use Selenium for Segment
        else:
            # Use requests for other platforms
            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

    def extract_source_setup_instructions(self) -> List[Dict]:
        url = self.base_url.rstrip('/') + '/getting-started/sources/'
        html_content = self._fetch_url(url)
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, 'html.parser')

        # Search for relevant content
        keywords = ['add source', 'set up', 'create source', 'configure source']
        relevant_elements = soup.find_all(
            ['h1', 'h2', 'h3', 'p', 'li'],
            string=re.compile('|'.join(keywords), re.IGNORECASE)
        )

        instructions = []
        for element in relevant_elements:
            content_parts = []
            current = element
            while current and current.name not in ['h1', 'h2', 'h3']:
                if current.name in ['p', 'ul', 'ol']:
                    content_parts.append(current.get_text(separator=" ", strip=True))
                current = current.find_next_sibling()
            instructions.extend(content_parts)

        if not instructions:
            main_content = soup.find('main') or soup
            instructions = [main_content.get_text(separator="\n", strip=True)]

        if instructions:
            return [{
                'content': "\n\n".join(instructions),
                'url': url,
                'relevance': 100
            }]
        return []

    def extract_docs(self, task: str, relevant_sections: List[str]) -> List[Dict]:
        """
        Extract documentation for a specific task from Segment's documentation.
        
        For the 'source_setup' task, we use the specialized extraction method.
        For other tasks, the generic extraction logic is used.
        
        Args:
            task (str): The task type.
            relevant_sections (List[str]): List of relevant section keywords.
            
        Returns:
            List[Dict]: List of relevant documentation snippets.
        """
        # Check cache first
        cached_data = self._get_cached_data(task)
        if cached_data:
            return cached_data
        
        results = []
        if task == 'source_setup':
            results = self.extract_source_setup_instructions()
            if results:
                self._cache_data(task, results)
            return results
        
        # Generic extraction for other tasks
        doc_paths = self.doc_sections.get(task, [])
        for path in doc_paths:
            url = self.base_url.rstrip('/') + path
            html_content = self._fetch_url(url)
            if not html_content:
                continue
            soup = BeautifulSoup(html_content, 'html.parser')
            relevant_elements = []
            for section in relevant_sections:
                headers = soup.find_all(
                    ['h1', 'h2', 'h3', 'h4'], 
                    string=re.compile(section, re.IGNORECASE)
                )
                for header in headers:
                    content_elements = []
                    current = header.find_next()
                    while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                        if current.name in ['p', 'ul', 'ol', 'pre', 'code']:
                            content_elements.append(current)
                        current = current.find_next()
                    if content_elements:
                        relevant_elements.extend(content_elements)
            for element in relevant_elements:
                snippet_text = self._extract_text_from_html(str(element))
                relevance = self._calculate_relevance(snippet_text, relevant_sections)
                if relevance > 0:
                    results.append({
                        'content': snippet_text,
                        'url': url,
                        'relevance': relevance
                    })
        if results:
            self._cache_data(task, results)
        return results

    def search(self, query: str) -> List[Dict]:
        """
        Segment-specific search implementation.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: Relevant documentation snippets.
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
                html_content = self._fetch_url(url)
                if not html_content:
                    continue
                soup = BeautifulSoup(html_content, 'html.parser')
                elements = soup.find_all(['p', 'li', 'pre', 'code'])
                for element in elements:
                    snippet_text = self._extract_text_from_html(str(element))
                    relevance = self._calculate_relevance(snippet_text, keywords)
                    if relevance > 0:
                        results.append({
                            'content': snippet_text,
                            'url': url,
                            'relevance': relevance
                        })
        results.sort(key=lambda x: x['relevance'], reverse=True)
        self._cache_data(cache_key, results)
        return results

    def _extract_code_examples(self, html_content: str) -> List[str]:
        """
        Extract code examples from HTML content.
        
        Args:
            html_content (str): HTML content.
            
        Returns:
            List[str]: List of code examples.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        code_blocks = []
        for code in soup.find_all(['pre', 'code']):
            code_text = code.get_text().strip()
            if code_text:
                code_blocks.append(code_text)
        return code_blocks

    
