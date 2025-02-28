
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    def __init__(self):
        self.cache_dir = 'cache'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        self.use_cache = False  # Disable caching to always perform a fresh search.
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for the platform's documentation."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name."""
        pass

    @abstractmethod
    def extract_docs(self, task: str, relevant_sections: List[str]) -> List[Dict]:
        """
        Extract documentation for a specific task.
        
        Args:
            task (str): The task type.
            relevant_sections (List[str]): List of relevant section keywords.
            
        Returns:
            List[Dict]: List of relevant documentation snippets.
        """
        pass

    def _get_cache_path(self, identifier: str) -> str:
        """Get the cache file path for a given identifier."""
        return os.path.join(self.cache_dir, f"{self.get_platform_name()}_{identifier}.json")

    def _cache_data(self, identifier: str, data: Any) -> None:
        """Cache data with a timestamp (only if caching is enabled)."""
        if not self.use_cache:
            return
        cache_content = {
            'timestamp': time.time(),
            'data': data
        }
        cache_path = self._get_cache_path(identifier)
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_content, f)
            logger.info(f"Cached data for identifier: {identifier}")
        except Exception as e:
            logger.error(f"Error caching data to {cache_path}: {e}")

    def _get_cached_data(self, identifier: str) -> Optional[Any]:
        """Return cached data if caching is enabled and data is still valid; otherwise, return None."""
        if not self.use_cache:
            return None
        cache_path = self._get_cache_path(identifier)
        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_content = json.load(f)
                if time.time() - cache_content.get('timestamp', 0) < self.cache_duration:
                    return cache_content.get('data')
                else:
                    logger.info(f"Cache expired for identifier: {identifier}")
                    return None
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.error(f"Error reading cache file {cache_path}: {e}")
            return None

    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from URL with error handling and rate limiting.
        
        Args:
            url (str): URL to fetch.
            
        Returns:
            Optional[str]: HTML content if successful, None otherwise.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html (str): HTML content.
            
        Returns:
            str: Clean text.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

    def _calculate_relevance(self, content: str, keywords: List[str]) -> float:
        """
        Calculate relevance score based on keyword matches.
        
        Args:
            content (str): Content to analyze.
            keywords (List[str]): Keywords to match.
            
        Returns:
            float: Relevance score between 0 and 1.
        """
        if not keywords:
            return 0.0

        content = content.lower()
        score = 0
        for keyword in keywords:
            # Prioritize exact matches
            count = len(re.findall(rf'\b{re.escape(keyword.lower())}\b', content))
            score += 1 - (0.5 ** count)
        return min(score / len(keywords), 1.0) if keywords else 0.0

    def search(self, query: str) -> List[Dict]:
        """
        Search documentation using a free-text query.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: Relevant documentation snippets.
        """
        keywords = query.lower().split()
        cached_data = self._get_cached_data('full_docs')
        
        if not cached_data:
            return []
        
        results = []
        for doc in cached_data:
            relevance = self._calculate_relevance(doc['content'], keywords)
            if relevance > 0:
                results.append({
                    'content': doc['content'],
                    'url': doc.get('url', ''),
                    'relevance': relevance
                })
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)

    def refresh_cache(self) -> None:
        """Clear the documentation cache."""
        cache_path = self._get_cache_path('full_docs')
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info(f"Cleared cache for identifier: full_docs")

    def clear_cache_directory(self) -> None:
        """Clear the entire cache directory."""
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        logger.info(f"Deleted cache file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting cache file {file_path}: {e}")
            logger.info("Cleared entire cache directory.")
