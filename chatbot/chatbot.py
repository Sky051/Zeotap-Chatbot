from typing import Dict, List
import re
from .docs_extractor import DocsExtractor
from .question_handler import QuestionHandler

class Chatbot:
    def __init__(self):
        self.docs_extractor = DocsExtractor()
        self.question_handler = QuestionHandler()
        self.cdp_platforms = {
            'segment': 'https://segment.com/docs/?ref=nav',
            'mparticle': 'https://docs.mparticle.com/',
            'lytics': 'https://docs.lytics.com/',
            'zeotap': 'https://docs.zeotap.com/home/en-us/'
        }

    def get_answer(self, question: str) -> Dict:
        """
        Process the user's question and return an appropriate answer
        
        Args:
            question (str): The user's question
            
        Returns:
            Dict: Contains the answer and any relevant metadata
        """
        try:
            # Normalize the question
            processed_question = self.question_handler.normalize_question(question)
            
            # Identify the CDP platform being asked about
            platform = self.identify_platform(processed_question)
            
            if not platform:
                return {
                    'answer': "I couldn't identify which CDP platform you're asking about. Please specify if your question is about Segment, mParticle, Lytics, or Zeotap.",
                    'error': 'platform_not_found'
                }
            
            # Extract the specific task or action being asked about
            task = self.question_handler.extract_task(processed_question)
            
            if not task:
                return {
                    'platform': platform,
                    'answer': f"I understand you're asking about {platform}, but could you please be more specific about what you'd like to do? For example, you can ask about setting up sources, creating profiles, building segments, or integrating data.",
                    'error': 'task_not_found'
                }
            
            # Get relevant documentation
            try:
                docs = self.docs_extractor.get_relevant_docs(platform, task)
            except Exception as e:
                # Handle documentation fetch errors
                return {
                    'platform': platform,
                    'task': task,
                    'answer': self._get_fallback_response(platform, task),
                    'error': 'docs_fetch_error'
                }
            
            if not docs:
                return {
                    'platform': platform,
                    'task': task,
                    'answer': self._get_fallback_response(platform, task),
                    'error': 'no_docs_found'
                }
            
            # Format the response
            response = {
                'platform': platform,
                'task': task,
                'answer': self.format_answer(docs),
                'source_url': self.cdp_platforms.get(platform, '')
            }
            
            return response
            
        except Exception as e:
            return {
                'answer': "I apologize, but I encountered an error while processing your question. Please try rephrasing it or ask something else.",
                'error': 'general_error'
            }

    def identify_platform(self, question: str) -> str:
        """
        Identify which CDP platform the question is about
        
        Args:
            question (str): The processed question
            
        Returns:
            str: The identified platform name
        """
        for platform in self.cdp_platforms.keys():
            if platform.lower() in question.lower():
                return platform
        return None

    def format_answer(self, docs: List[Dict]) -> str:
        """
        Format the extracted documentation into a coherent answer
        
        Args:
            docs (List[Dict]): List of relevant documentation snippets
            
        Returns:
            str: Formatted answer
        """
        if not docs:
            return "I'm sorry, I couldn't find specific information about that. Please try rephrasing your question or check the platform's documentation directly."
        
        # Combine relevant documentation snippets into a coherent answer
        answer = "Here's how you can do that:\n\n"
        for i, doc in enumerate(docs, 1):
            answer += f"{i}. {doc['content']}\n"
        
        return answer

    def _get_fallback_response(self, platform: str, task: str) -> str:
        """
        Provide a fallback response when documentation cannot be fetched
        
        Args:
            platform (str): The CDP platform
            task (str): The task type
            
        Returns:
            str: A fallback response
        """
        fallback_responses = {
            'source_setup': {
                'segment': "To set up a new source in Segment:\n1. Log in to your Segment workspace\n2. Navigate to Sources in the left sidebar\n3. Click 'Add Source'\n4. Select your source type and follow the configuration steps\n\nFor detailed instructions, please visit Segment's documentation.",
                'mparticle': "To set up a new source in mParticle:\n1. Access your mParticle dashboard\n2. Go to Setup > Inputs\n3. Choose your input type and follow the setup wizard\n\nFor detailed instructions, please refer to mParticle's documentation.",
                'lytics': "To set up a new source in Lytics:\n1. Log in to your Lytics account\n2. Navigate to the Sources section\n3. Click 'Add New Source'\n4. Follow the source-specific configuration steps\n\nFor more details, please check Lytics' documentation.",
                'zeotap': "To set up a new source in Zeotap:\n1. Access your Zeotap dashboard\n2. Go to Data Sources\n3. Click 'Add New Source'\n4. Complete the source configuration\n\nFor detailed instructions, please visit Zeotap's documentation."
            },
            'profile_creation': {
                'segment': "To create user profiles in Segment:\n1. Implement the identify call\n2. Set up user traits\n3. Configure Identity Resolution settings\n\nPlease check Segment's documentation for implementation details.",
                'mparticle': "To create user profiles in mParticle:\n1. Use the Identity API\n2. Configure user attributes\n3. Set up identity mapping\n\nRefer to mParticle's documentation for complete instructions.",
                'lytics': "To create user profiles in Lytics:\n1. Set up identity collection\n2. Configure user attributes\n3. Define identity resolution rules\n\nSee Lytics' documentation for detailed steps.",
                'zeotap': "To create user profiles in Zeotap:\n1. Configure identity parameters\n2. Set up user attributes\n3. Define identity resolution settings\n\nCheck Zeotap's documentation for full details."
            },
            'audience_segment': {
                'segment': "To build audience segments in Segment:\n1. Go to Personas\n2. Create a new audience\n3. Define segment criteria\n4. Activate the segment\n\nConsult Segment's documentation for detailed instructions.",
                'mparticle': "To create segments in mParticle:\n1. Navigate to Audience Builder\n2. Define segment criteria\n3. Set activation parameters\n\nSee mParticle's documentation for complete steps.",
                'lytics': "To build segments in Lytics:\n1. Access Audience Builder\n2. Define segment rules\n3. Set up activation\n\nRefer to Lytics' documentation for detailed guidance.",
                'zeotap': "To create segments in Zeotap:\n1. Go to Audience Builder\n2. Define segment criteria\n3. Configure activation settings\n\nCheck Zeotap's documentation for full instructions."
            },
            'data_integration': {
                'segment': "To integrate data with Segment:\n1. Choose your integration type\n2. Configure the connection\n3. Set up data mapping\n4. Test the integration\n\nRefer to Segment's documentation for specific steps.",
                'mparticle': "To integrate data with mParticle:\n1. Select integration type\n2. Configure connection settings\n3. Set up data forwarding\n\nSee mParticle's documentation for detailed instructions.",
                'lytics': "To integrate data with Lytics:\n1. Choose integration type\n2. Configure connection\n3. Set up data mapping\n\nCheck Lytics' documentation for complete steps.",
                'zeotap': "To integrate data with Zeotap:\n1. Select integration type\n2. Configure connection settings\n3. Set up data mapping\n\nRefer to Zeotap's documentation for detailed guidance."
            }
        }

        # Get the fallback response for the specific platform and task
        if task in fallback_responses and platform in fallback_responses[task]:
            return fallback_responses[task][platform]
        
        # Generic fallback response if specific one not found
        return f"I apologize, but I'm having trouble accessing the documentation for {platform} right now. Please try visiting the platform's documentation directly at {self.cdp_platforms.get(platform, '')}."
