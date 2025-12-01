"""
LLM client for plan generation using OpenRouter
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from config import get_settings

logger = logging.getLogger(__name__)

# --- Pydantic Models for LLM Validation ---

class LLMResource(BaseModel):
    resource_id: str
    why_included: str
    order: int

class LLMMilestone(BaseModel):
    title: str
    description: str
    resources: List[LLMResource]
    skills_gained: List[str]
    order: int

class LLMPlanResponse(BaseModel):
    milestones: List[LLMMilestone]
    reasoning: str

# ------------------------------------------

class LLMClient:
    """Client for interacting with LLM via OpenRouter"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            base_url=self.settings.openrouter_base_url,
            api_key=self.settings.openrouter_api_key,
        )
    
    def generate_plan(
        self,
        goal: str,
        current_skills: List[str],
        available_resources: List[Dict[str, Any]],
        time_budget_hours: int,
        hours_per_week: int,
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a learning plan using LLM with retries and validation
        
        Args:
            goal: Learning goal description
            current_skills: List of current skill names
            available_resources: List of resources from RAG search
            time_budget_hours: Total time budget
            hours_per_week: Hours per week available
            preferences: User preferences
            
        Returns:
            Structured plan as dict
        """
        # Build prompt
        initial_prompt = self._build_plan_prompt(
            goal, current_skills, available_resources,
            time_budget_hours, hours_per_week, preferences
        )
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert learning path designer. Create structured, achievable learning plans that respect prerequisites and time constraints."
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
                logger.info(f"LLM generation attempt {attempt + 1}/{max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.settings.default_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000,
                )
                
                plan_text = response.choices[0].message.content
                
                # Parse and Validate
                validated_plan = self._parse_and_validate_response(plan_text)
                
                # If successful, enrich with resource data and return
                return self._enrich_plan_data(validated_plan, available_resources)
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Validation failed on attempt {attempt + 1}: {e}")
                last_error = e
                
                # Add error feedback to messages for next attempt
                error_message = f"The previous response was invalid. Error: {str(e)}. Please correct the JSON to match the schema exactly."
                messages.append({"role": "assistant", "content": plan_text})
                messages.append({"role": "user", "content": error_message})
                
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                raise
        
        # If we run out of retries
        logger.error(f"Failed to generate valid plan after {max_retries} attempts")
        if last_error:
            raise last_error
        raise Exception("Failed to generate plan")
    
    def _build_plan_prompt(
        self,
        goal: str,
        current_skills: List[str],
        resources: List[Dict[str, Any]],
        time_budget: int,
        hours_per_week: int,
        preferences: Dict[str, Any] = None
    ) -> str:
        """Build the prompt for plan generation"""
        
        resources_text = "\n".join([
            f"- [{r['resource_id']}] {r['title']} ({r.get('duration_min', 0)} min, Level: {r.get('level', 'N/A')})\n  URL: {r['url']}\n  Skills: {', '.join(r.get('skills', []))}"
            for r in resources[:30]  # Limit to top 30 resources
        ])
        
        prompt = f"""Create a learning plan for the following goal:

GOAL: {goal}

CURRENT SKILLS: {', '.join(current_skills) if current_skills else 'None specified'}

TIME BUDGET: {time_budget} hours total, {hours_per_week} hours per week

AVAILABLE RESOURCES:
{resources_text}

PREFERENCES: {preferences if preferences else 'None specified'}

Create a structured learning plan with the following:
1. Break the goal into 3-5 milestones
2. Assign resources to each milestone in logical order
3. Respect prerequisites (beginner → intermediate → advanced)
4. Stay within the time budget
5. Explain why each resource is included

Format your response as strictly valid JSON with this exact structure:
{{
  "milestones": [
    {{
      "title": "Milestone name",
      "description": "What will be learned",
      "resources": [
        {{
          "resource_id": "id from list",
          "why_included": "explanation",
          "order": 1
        }}
      ],
      "skills_gained": ["skill1", "skill2"],
      "order": 1
    }}
  ],
  "reasoning": "Overall explanation of the plan structure and progression"
}}

Ensure the total duration of selected resources fits within {time_budget} hours. Do not wrap the JSON in markdown code blocks.
"""
        return prompt
    
    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response text and validate against schema"""
        
        # Extract JSON from response (handle markdown code blocks if present)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_text = json_match.group(0) if json_match else response_text
        
        # Parse JSON (will raise JSONDecodeError if invalid)
        data = json.loads(json_text)
        
        # Validate against Pydantic model (will raise ValidationError if invalid)
        validated_model = LLMPlanResponse(**data)
        
        return validated_model.model_dump()

    def _enrich_plan_data(self, plan_data: Dict[str, Any], available_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enrich validated plan data with full resource details"""
        # Enrich with full resource data
        resource_map = {r['resource_id']: r for r in available_resources}
        
        for milestone in plan_data.get('milestones', []):
            for resource in milestone.get('resources', []):
                resource_id = resource.get('resource_id')
                if resource_id in resource_map:
                    full_resource = resource_map[resource_id]
                    resource.update({
                        'title': full_resource['title'],
                        'url': full_resource['url'],
                        'duration_min': full_resource.get('duration_min', 0),
                        'level': full_resource.get('level'),
                        'skills': full_resource.get('skills', [])
                    })
        return plan_data
    
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
