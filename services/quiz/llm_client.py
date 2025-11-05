"""
LLM client for quiz generation using OpenRouter
"""
import logging
import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM via OpenRouter"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            base_url=self.settings.openrouter_base_url,
            api_key=self.settings.openrouter_api_key,
        )
    
    def generate_quiz(
        self,
        resource_snippets: List[Dict[str, Any]],
        num_questions: int = 5,
        difficulty: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from resource snippets
        
        Args:
            resource_snippets: List of resource snippets with content
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            List of quiz questions with citations
        """
        prompt = self._build_quiz_prompt(resource_snippets, num_questions, difficulty)
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator creating quiz questions. Every question MUST include a specific citation from the source material. Questions must be clear, unambiguous, and have only one correct answer."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000,
            )
            
            quiz_text = response.choices[0].message.content
            logger.info(f"Generated {num_questions} quiz questions")
            
            return self._parse_quiz_response(quiz_text, resource_snippets)
            
        except Exception as e:
            logger.error(f"LLM quiz generation error: {e}")
            raise
    
    def _build_quiz_prompt(
        self,
        snippets: List[Dict[str, Any]],
        num_questions: int,
        difficulty: str = None
    ) -> str:
        """Build prompt for quiz generation"""
        
        snippets_text = "\n\n".join([
            f"[Resource {i+1}: {s['resource_id']}]\nTitle: {s['title']}\nContent:\n{s['content']}"
            for i, s in enumerate(snippets)
        ])
        
        difficulty_instruction = f"\nDifficulty level: {difficulty}" if difficulty else ""
        
        prompt = f"""Generate {num_questions} multiple-choice quiz questions based on the following learning resources.

RESOURCES:
{snippets_text}

REQUIREMENTS:
1. Each question must have 4 options (A, B, C, D)
2. Only ONE option should be correct
3. Include a clear explanation for the correct answer
4. CRITICAL: Include a specific citation (quote or reference) from the source material
5. Questions should test understanding, not just memorization{difficulty_instruction}

Format your response as JSON:
{{
  "questions": [
    {{
      "question_text": "What is...",
      "options": [
        {{"id": "A", "text": "Option A"}},
        {{"id": "B", "text": "Option B"}},
        {{"id": "C", "text": "Option C"}},
        {{"id": "D", "text": "Option D"}}
      ],
      "correct_option": "A",
      "explanation": "Explanation of why A is correct",
      "source_resource_id": "resource_id",
      "citation": "Specific quote or reference from the resource"
    }}
  ]
}}

Generate exactly {num_questions} questions.
"""
        return prompt
    
    def _parse_quiz_response(
        self,
        response_text: str,
        resource_snippets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured quiz questions"""
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_text = json_match.group(0) if json_match else response_text
        
        try:
            quiz_data = json.loads(json_text)
            questions = quiz_data.get('questions', [])
            
            # Validate each question has required fields
            for q in questions:
                if not all(k in q for k in ['question_text', 'options', 'correct_option', 'explanation', 'citation']):
                    logger.warning(f"Question missing required fields: {q}")
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz JSON: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if LLM service is available"""
        try:
            response = self.client.chat.completions.create(
                model=self.settings.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False


_llm_client = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
