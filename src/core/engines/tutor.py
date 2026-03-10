from typing import Any
from src.llm.providers.base import LLMProvider
from src.core.plugin.interfaces import ContentItem
from src.config import get_settings

settings = get_settings()

class TutorEngine:
    """
    Modernized TutorEngine responsible for pedagogical dialogue generation.
    It encapsulates all prompt engineering and strategy injection logic.
    """
    
    def __init__(self, llm_client: LLMProvider):
        self.llm = llm_client

    def _construct_system_prompt(self, context_data: dict[str, Any], content: ContentItem | None) -> str:
        # Extract strategy safely (handle dict or str)
        raw_strategy = context_data.get('strategy', 'standard')
        if isinstance(raw_strategy, dict):
            # If strategy is a dict (e.g. from RL), use 'source' or a default key
            strategy = raw_strategy.get('source', 'standard')
        else:
            strategy = str(raw_strategy)

        mastery = context_data.get('mastery_score', 0.5)
        rl_info = context_data.get('rl_info', {})
        
        domain = content.metadata.get('domain', 'General Learning') if content else "General Learning"
        content_text = content.text if content else "No specific lesson content provided. Answer based on general knowledge."
        
        base_prompt = f"""You are an adaptive AI Tutor for {domain}.
        
        Current Lesson Content:
        {content_text}
        
        Learner State:
        - Mastery Level: {mastery:.2f}
        - Current Strategy: {strategy}
        """
        
        if rl_info:
             base_prompt += f"\n- RL Agent Suggestion: {rl_info.get('desc', 'None')}\n"
        
        # Strategy-specific instructions map (could be moved to config/yaml)
        strategies = {
            "socratic": """
            STRATEGY: SOCRATIC METHOD
            - Do NOT provide the direct answer.
            - Ask guiding questions to lead the student to the answer.
            - If the student is wrong, ask a question that highlights their misconception.
            - Encourage critical thinking.
            """,
            "socratic_challenge": """
            STRATEGY: SOCRATIC CHALLENGE
            - The student is doing well. Challenge them with a deeper question.
            - Ask "Why?" or "What if?" questions.
            - Encourage them to connect this concept to other topics.
            """,
            "feynman": """
            STRATEGY: FEYNMAN TECHNIQUE
            - Ask the student to explain the concept in their own words as if teaching a beginner.
            - Identify gaps in their explanation and ask them to clarify those specific parts.
            - Use analogies to simplify complex ideas.
            """,
            "scaffolding": """
            STRATEGY: SCAFFOLDING (SUPPORT)
            - The student is stuck. Break the problem down into smaller, manageable steps.
            - Provide a hint for the immediate next step only.
            - Use simple language and encouraging tone.
            - Validate partially correct understanding before correcting errors.
            """,
            "standard": """
            STRATEGY: DIRECT INSTRUCTION
            - Act as a supportive tutor.
            - Use the provided lesson content to guide the user.
            - If the user makes a mistake, explain it gently based on the content.
            - Keep responses concise and encouraging.
            """
        }
        
        # Fallback to standard if strategy not found
        strategy_instruction = strategies.get(strategy, strategies["standard"])
            
        return base_prompt + "\n" + strategy_instruction

    async def generate_reply(
        self, 
        user_message: str, 
        history: list[dict[str, str]], 
        context_data: dict[str, Any],
        current_content: ContentItem | None = None
    ) -> str:
        
        system_prompt = self._construct_system_prompt(context_data, current_content)
        
        # Build message chain
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add last N messages from history for context
        if history:
             # Ensure history elements are dicts and have 'role' and 'content'
             clean_history = [
                 {"role": msg.get("role"), "content": msg.get("content")} 
                 for msg in history 
                 if isinstance(msg, dict) and msg.get("role") in ("user", "assistant")
             ]
             # Assuming settings.VECTOR_SEARCH_LIMIT is available, otherwise default to 5
             limit = getattr(settings, 'VECTOR_SEARCH_LIMIT', 5)
             messages.extend(clean_history[-limit:])
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        response = await self.llm.generate_chat(messages)
        return response
