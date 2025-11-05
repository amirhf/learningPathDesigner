"""
LLM client for plan generation using OpenRouter
"""
import logging
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
        Generate a learning plan using LLM
        
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
        prompt = self._build_plan_prompt(
            goal, current_skills, available_resources,
            time_budget_hours, hours_per_week, preferences
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning path designer. Create structured, achievable learning plans that respect prerequisites and time constraints."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            
            plan_text = response.choices[0].message.content
            logger.info(f"Generated plan for goal: {goal[:50]}...")
            
            # Parse the response (in production, use structured output or JSON mode)
            return self._parse_plan_response(plan_text, available_resources)
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
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

Format your response as JSON with this structure:
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

Ensure the total duration of selected resources fits within {time_budget} hours.
"""
        return prompt
    
    def _parse_plan_response(
        self,
        response_text: str,
        available_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parse LLM response into structured plan"""
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_text = json_match.group(0) if json_match else response_text
        
        try:
            plan_data = json.loads(json_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using fallback structure")
            plan_data = {
                "milestones": [],
                "reasoning": "Failed to parse LLM response"
            }
        
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
