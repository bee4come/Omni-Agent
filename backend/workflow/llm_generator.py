"""
LLM-based Output Generator for Workflow Steps.

Generates realistic content for each workflow step using LLM.
Falls back to mock data if LLM is unavailable.
"""

from typing import Dict, Any, Optional
from functools import lru_cache
import hashlib
import json

# Import LLM utility
try:
    from agents.utils import get_llm_instance
except ImportError:
    get_llm_instance = None


# Role-specific prompts
ROLE_PROMPTS = {
    "writer": """You are a professional content writer. Generate a short marketing draft.

Topic: {topic}
Previous step output: {input_summary}

Generate a 3-paragraph marketing draft with:
1. An attention-grabbing opening
2. Key benefits and features
3. A call to action

Keep it concise (200-300 words). Output as JSON:
{{
    "title": "Article title",
    "content": "Full article text...",
    "sections": ["Section 1 title", "Section 2 title", "Section 3 title"],
    "word_count": 250,
    "key_points": ["Point 1", "Point 2", "Point 3"]
}}""",

    "designer": """You are a creative designer. Describe visual assets for a marketing campaign.

Topic: {topic}
Content from writer: {input_summary}

Describe 3 visual assets that would complement this content. Output as JSON:
{{
    "theme": "Modern/Professional/Playful/etc",
    "color_palette": ["#hex1", "#hex2", "#hex3"],
    "assets": [
        {{"type": "hero_banner", "description": "Description of the banner...", "dimensions": "1200x600"}},
        {{"type": "infographic", "description": "Description...", "dimensions": "800x1200"}},
        {{"type": "social_card", "description": "Description...", "dimensions": "1080x1080"}}
    ],
    "style_notes": "Brief style guidelines..."
}}""",

    "reviewer": """You are a quality assurance reviewer. Review the content and provide feedback.

Content to review: {input_summary}

Provide a quality review with specific, actionable feedback. Output as JSON:
{{
    "score": 85,
    "approved": true,
    "summary": "Brief overall assessment",
    "strengths": ["Strength 1", "Strength 2"],
    "improvements": ["Improvement 1", "Improvement 2"],
    "final_verdict": "Ready for publication / Needs revision"
}}""",

    "collector": """You are a data collector. Summarize the data collection results.

Task: Collect data for {topic}
Parameters: {input_summary}

Describe the data collection results. Output as JSON:
{{
    "records_collected": 1250,
    "sources": ["Source 1", "Source 2", "Source 3"],
    "time_range": "Last 24 hours",
    "data_quality": "High/Medium/Low",
    "sample_records": [
        {{"id": 1, "type": "event", "value": "sample"}},
        {{"id": 2, "type": "metric", "value": 42}}
    ],
    "collection_notes": "Brief notes about the collection process"
}}""",

    "analyzer": """You are a data analyst. Analyze the collected data and provide insights.

Data summary: {input_summary}

Provide analysis with actionable insights. Output as JSON:
{{
    "key_metrics": {{
        "total_records": 1250,
        "success_rate": 0.95,
        "trend": "increasing"
    }},
    "insights": [
        "Key insight 1 with specific numbers",
        "Key insight 2 with comparison",
        "Key insight 3 with recommendation"
    ],
    "anomalies": ["Any unusual patterns detected"],
    "recommendations": ["Actionable recommendation 1", "Actionable recommendation 2"]
}}""",

    "reporter": """You are a report writer. Create an executive summary report.

Analysis results: {input_summary}

Create a brief executive report. Output as JSON:
{{
    "report_title": "Executive Summary: Topic",
    "executive_summary": "2-3 sentence overview of key findings",
    "key_findings": [
        {{"finding": "Finding 1", "impact": "High/Medium/Low"}},
        {{"finding": "Finding 2", "impact": "High/Medium/Low"}}
    ],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "next_steps": ["Next step 1", "Next step 2"]
}}"""
}


# Fallback mock outputs (used when LLM unavailable)
MOCK_OUTPUTS = {
    "writer": {
        "title": "AI-Powered Agent Payments: The Future of Automation",
        "content": """The landscape of AI automation is evolving rapidly. With MNEE-powered agent payments, we're witnessing a paradigm shift in how AI systems collaborate and transact.

Our platform enables seamless micro-payments between AI agents, creating a true marketplace for machine intelligence. Each transaction is secured through smart contracts, ensuring trustless execution.

Ready to revolutionize your AI infrastructure? Join thousands of developers building on MNEE Nexus today.""",
        "sections": ["Introduction", "Key Benefits", "Call to Action"],
        "word_count": 78,
        "key_points": ["Seamless payments", "Smart contract security", "Agent marketplace"]
    },
    "designer": {
        "theme": "Modern Tech",
        "color_palette": ["#6366f1", "#10b981", "#1e293b"],
        "assets": [
            {"type": "hero_banner", "description": "Dynamic visualization of AI agents exchanging MNEE tokens", "dimensions": "1200x600"},
            {"type": "infographic", "description": "Flow diagram showing escrow-verify-release process", "dimensions": "800x1200"},
            {"type": "social_card", "description": "Key stats with gradient background", "dimensions": "1080x1080"}
        ],
        "style_notes": "Clean, minimal design with subtle gradients and data visualization elements"
    },
    "reviewer": {
        "score": 92,
        "approved": True,
        "summary": "Excellent content quality with clear messaging",
        "strengths": ["Clear value proposition", "Strong technical credibility", "Compelling CTA"],
        "improvements": ["Could add more specific use cases", "Consider adding testimonials"],
        "final_verdict": "Ready for publication"
    },
    "collector": {
        "records_collected": 1250,
        "sources": ["API logs", "Transaction history", "User events"],
        "time_range": "Last 24 hours",
        "data_quality": "High",
        "sample_records": [
            {"id": 1, "type": "transaction", "value": "2.5 MNEE"},
            {"id": 2, "type": "agent_call", "value": "image_gen"}
        ],
        "collection_notes": "All data sources responded successfully"
    },
    "analyzer": {
        "key_metrics": {
            "total_records": 1250,
            "success_rate": 0.95,
            "trend": "increasing"
        },
        "insights": [
            "Transaction volume increased 15% over previous period",
            "Designer agent shows highest utilization at 78%",
            "Average transaction cost: 1.25 MNEE"
        ],
        "anomalies": ["Spike in activity at 14:00 UTC"],
        "recommendations": ["Consider auto-scaling during peak hours", "Optimize batch processing"]
    },
    "reporter": {
        "report_title": "MNEE Nexus Performance Report",
        "executive_summary": "System performance exceeds targets with 95% success rate. Agent utilization is healthy across all roles.",
        "key_findings": [
            {"finding": "15% increase in transaction volume", "impact": "High"},
            {"finding": "Designer agent most cost-effective", "impact": "Medium"}
        ],
        "recommendations": ["Scale infrastructure for growth", "Add more workflow templates"],
        "next_steps": ["Deploy auto-scaling", "Launch marketing campaign"]
    }
}


class LLMOutputGenerator:
    """Generates step outputs using LLM with fallback to mocks."""

    def __init__(self, llm=None):
        self.llm = llm
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, role: str, topic: str, input_data: Dict) -> str:
        """Generate cache key for output."""
        data = f"{role}:{topic}:{json.dumps(input_data, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def _summarize_input(self, input_data: Dict[str, Any]) -> str:
        """Create a brief summary of input data for the prompt."""
        if not input_data:
            return "No previous input"

        # Extract key fields
        summary_parts = []
        for key in ["title", "content", "summary", "topic", "key_points", "insights"]:
            if key in input_data:
                val = input_data[key]
                if isinstance(val, list):
                    summary_parts.append(f"{key}: {', '.join(str(v) for v in val[:3])}")
                elif isinstance(val, str) and len(val) > 200:
                    summary_parts.append(f"{key}: {val[:200]}...")
                else:
                    summary_parts.append(f"{key}: {val}")

        return "; ".join(summary_parts) if summary_parts else str(input_data)[:500]

    def generate(
        self,
        role: str,
        topic: str = "AI Agent Payments",
        input_data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate output for a workflow step.

        Args:
            role: Step role (writer, designer, reviewer, etc.)
            topic: Topic for content generation
            input_data: Output from previous step
            use_cache: Whether to use cached results

        Returns:
            Generated output as dict
        """
        role_lower = role.lower()
        input_data = input_data or {}

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(role_lower, topic, input_data)
            if cache_key in self._cache:
                print(f"[LLM_GEN] Using cached output for {role}")
                return self._cache[cache_key]

        # Try LLM generation
        if self.llm and role_lower in ROLE_PROMPTS:
            try:
                prompt = ROLE_PROMPTS[role_lower].format(
                    topic=topic,
                    input_summary=self._summarize_input(input_data)
                )

                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)

                # Parse JSON from response
                # Find JSON in response (handle markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                output = json.loads(content.strip())
                output["_generated_by"] = "llm"
                output["_role"] = role
                output["status"] = f"{role_lower}_complete"

                # Cache result
                if use_cache:
                    self._cache[cache_key] = output

                print(f"[LLM_GEN] Generated LLM output for {role}")
                return output

            except Exception as e:
                print(f"[LLM_GEN] LLM generation failed for {role}: {e}")

        # Fallback to mock
        print(f"[LLM_GEN] Using mock output for {role}")
        mock = MOCK_OUTPUTS.get(role_lower, {
            "content_type": "generic",
            "status": "complete",
            "data": input_data
        }).copy()
        mock["_generated_by"] = "mock"
        mock["_role"] = role
        mock["status"] = f"{role_lower}_complete"

        return mock


# Global instance
_generator: Optional[LLMOutputGenerator] = None


def get_llm_generator() -> LLMOutputGenerator:
    """Get or create the global LLM generator."""
    global _generator
    if _generator is None:
        llm = None
        if get_llm_instance:
            llm = get_llm_instance()
        _generator = LLMOutputGenerator(llm)
    return _generator
