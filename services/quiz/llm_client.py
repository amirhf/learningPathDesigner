"""
LLM client for quiz generation using OpenRouter
"""
import logging
import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from config import get_settings

logger = logging.getLogger(__name__)

# --- Pydantic Models for LLM Validation ---

class LLMQuizOption(BaseModel):
    id: str
    text: str

class LLMQuizQuestion(BaseModel):
    question_text: str
    options: List[LLMQuizOption]
    correct_option: str
    explanation: str
    source_resource_id: str
    citation: str

class LLMQuizResponse(BaseModel):
    questions: List[LLMQuizQuestion]

# ------------------------------------------

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
        initial_prompt = self._build_quiz_prompt(resource_snippets, num_questions, difficulty)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert educator creating quiz questions. Every question MUST include a specific citation from the source material. Questions must be clear, unambiguous, and have only one correct answer."
            },
            {
                "role": "user",
                "content": initial_prompt
            }
        ]
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM quiz generation attempt {attempt + 1}/{max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.settings.default_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=3000,
                )
                
                quiz_text = response.choices[0].message.content
                
                # Parse and Validate
                validated_response = self._parse_and_validate_response(quiz_text)
                
                # Return as list of dicts
                return [q.model_dump() for q in validated_response.questions]
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Validation failed on attempt {attempt + 1}: {e}")
                last_error = e
                
                # Add error feedback to messages for next attempt
                error_message = f"The previous response was invalid. Error: {str(e)}. Please correct the JSON to match the schema exactly."
                messages.append({"role": "assistant", "content": quiz_text})
                messages.append({"role": "user", "content": error_message})
                
            except Exception as e:
                logger.error(f"LLM quiz generation error: {e}")
                raise
        
        logger.error(f"Failed to generate valid quiz after {max_retries} attempts")
        if last_error:
            raise last_error
        return []
    
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

Format your response as strictly valid JSON with this exact structure:
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

Generate exactly {num_questions} questions. Do not wrap the JSON in markdown code blocks.
"""
        return prompt
    
    def _parse_and_validate_response(self, response_text: str) -> LLMQuizResponse:
        """Parse LLM response into structured quiz questions"""
        
        if not response_text or not response_text.strip():
            raise ValueError("Empty response from LLM")
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_text = json_match.group(0) if json_match else response_text
        
        # Parse JSON
        data = json.loads(json_text)
        
        # Validate against Pydantic model
        return LLMQuizResponse(**data)
    
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
