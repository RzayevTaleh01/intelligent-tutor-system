from typing import List, Dict, Any
from src.llm.ollama_client import OllamaClient
from src.core.plugin.interfaces import ContentItem

class TutorEngine:
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    def _construct_system_prompt(self, context_data: Dict[str, Any], content: ContentItem) -> str:
        strategy = context_data.get('strategy', 'standard')
        mastery = context_data.get('mastery_score', 0.5)
        
        base_prompt = f"""You are an adaptive AI Tutor for {content.metadata.get('domain', 'General Learning')}.
        
        Current Lesson Content:
        {content.text}
        
        Learner State:
        - Mastery Level: {mastery:.2f}
        - Current Strategy: {strategy}
        """
        
        # Strategy-specific instructions
        if strategy in ["socratic", "socratic_challenge"]:
            strategy_instruction = """
            STRATEGY: SOCRATIC METHOD
            - Do NOT provide the direct answer.
            - Ask guiding questions to lead the student to the answer.
            - If the student is wrong, ask a question that highlights their misconception.
            - Encourage critical thinking.
            """
        elif strategy == "feynman":
            strategy_instruction = """
            STRATEGY: FEYNMAN TECHNIQUE
            - Ask the student to explain the concept in their own words as if teaching a beginner.
            - Identify gaps in their explanation and ask them to clarify those specific parts.
            - Use analogies to simplify complex ideas.
            """
        elif strategy == "scaffolding":
            strategy_instruction = """
            STRATEGY: SCAFFOLDING (SUPPORT)
            - The student is stuck. Break the problem down into smaller, manageable steps.
            - Provide a hint for the immediate next step only.
            - Use simple language and encouraging tone.
            - Validate partially correct understanding before correcting errors.
            """
        else: # Standard, drill, explain
            strategy_instruction = """
            STRATEGY: DIRECT INSTRUCTION
            - Act as a supportive tutor.
            - Use the provided lesson content to guide the user.
            - If the user makes a mistake, explain it gently based on the content.
            - Keep responses concise and encouraging.
            """
            
        return base_prompt + "\n" + strategy_instruction

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
