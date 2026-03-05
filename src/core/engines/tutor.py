from typing import List, Dict, Any
from src.llm.ollama_client import OllamaClient
from src.core.plugin.interfaces import ContentItem

class TutorEngine:
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    def _construct_system_prompt(self, context_data: Dict[str, Any], content: ContentItem) -> str:
        return f"""You are an adaptive AI Tutor for {content.metadata.get('domain', 'General Learning')}.
        
        Current Lesson Content:
        {content.text}
        
        Learner State:
        - Mastery Level: {context_data.get('mastery_score', 0.5):.2f}
        - Strategy: {context_data.get('strategy', 'standard')}
        
        Instructions:
        - Act as a supportive tutor.
        - Use the provided lesson content to guide the user.
        - If the user makes a mistake, explain it gently based on the content.
        - Keep responses concise and encouraging.
        """

    async def generate_reply(
        self, 
        user_message: str, 
        history: List[Dict[str, str]], 
        context_data: Dict[str, Any],
        current_content: ContentItem
    ) -> str:
        
        system_prompt = self._construct_system_prompt(context_data, current_content)
        
        # Build message chain
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add last few messages from history for context (e.g., last 4)
        messages.extend(history[-4:])
        
        # Add current user message if not already in history (it usually isn't)
        messages.append({"role": "user", "content": user_message})
        
        response = await self.llm.generate_chat_completion(messages)
        return response
