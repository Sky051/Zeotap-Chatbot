import re
from typing import Dict, List, Optional

class QuestionHandler:
    def __init__(self):
        self.common_patterns = {
            'how_to': r'how\s+(?:do|can|should|would|to)\s+(?:i|we|you)',
            'what_is': r'what\s+(?:is|are)',
            'setup': r'set\s*up|configure|install',
            'create': r'create|make|build|establish',
            'integrate': r'integrate|connect|link|sync',
        }
        
        self.task_patterns = {
            'source_setup': [
                r'set\s*up.*source',
                r'add.*source',
                r'create.*source',
                r'configure.*source'
            ],
            'profile_creation': [
                r'create.*profile',
                r'set\s*up.*profile',
                r'build.*profile',
                r'establish.*profile'
            ],
            'audience_segment': [
                r'build.*segment',
                r'create.*segment',
                r'define.*segment',
                r'set\s*up.*segment'
            ],
            'data_integration': [
                r'integrate.*data',
                r'connect.*data',
                r'sync.*data',
                r'link.*data'
            ]
        }

    def normalize_question(self, question: str) -> str:
        """
        Normalize the question by converting to lowercase, removing extra whitespace,
        and standardizing common phrases
        
        Args:
            question (str): The original question
            
        Returns:
            str: The normalized question
        """
        # Convert to lowercase
        normalized = question.lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Standardize common variations
        normalized = re.sub(r'how\s+do\s+you', 'how to', normalized)
        normalized = re.sub(r'how\s+can\s+i', 'how to', normalized)
        normalized = re.sub(r'how\s+do\s+i', 'how to', normalized)
        
        return normalized

    def extract_task(self, question: str) -> Optional[str]:
        """
        Extract the specific task being asked about from the question
        
        Args:
            question (str): The normalized question
            
        Returns:
            Optional[str]: The identified task type, or None if no task is identified
        """
        # Check each task pattern
        for task_type, patterns in self.task_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return task_type
        
        # If no specific task is identified, try to extract the general action
        for action_type, pattern in self.common_patterns.items():
            if re.search(pattern, question, re.IGNORECASE):
                return action_type
        
        return None

    def get_question_type(self, question: str) -> str:
        """
        Determine the type of question being asked
        
        Args:
            question (str): The normalized question
            
        Returns:
            str: The question type ('how_to', 'what_is', etc.)
        """
        for q_type, pattern in self.common_patterns.items():
            if re.search(pattern, question, re.IGNORECASE):
                return q_type
        return 'general'

    def extract_keywords(self, question: str) -> List[str]:
        """
        Extract important keywords from the question
        
        Args:
            question (str): The normalized question
            
        Returns:
            List[str]: List of important keywords
        """
        # Remove common stop words and extract key terms
        stop_words = {'how', 'to', 'do', 'can', 'i', 'you', 'the', 'a', 'an', 'in', 'on', 'at', 'with'}
        words = question.lower().split()
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
