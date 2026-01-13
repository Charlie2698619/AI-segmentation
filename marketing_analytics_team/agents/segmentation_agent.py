"""
Customer Segmentation Analyst Agent
====================================

Provides insights on K-means cluster characteristics and marketing strategies.
"""

import json
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


SEGMENTATION_PROMPT = """You are a Customer Segmentation Analyst with skills in behavioral analytics, lifecycle marketing, and data-driven cohort design. You analyze customer segments to provide 
marketing insights and strategies for each segment.

The 5 Customer Segments (ranked by engagement):
{segment_info}

Based on this data, provide insights on:
1. What defines each segment behaviorally
2. Recommended marketing approaches for each
3. Conversion potential and prioritization
4. Re-engagement strategies for lower segments

Be specific and actionable in your recommendations.
"""


def create_segmentation_agent(llm, data_path: Path):
    """Create the segmentation analyst agent node function."""
    
    # Load segment descriptions
    segment_file = data_path / "segment_descriptions.json"
    if segment_file.exists():
        with open(segment_file) as f:
            segment_info = json.load(f)
    else:
        # Fallback with 5 segments
        segment_info = {
            "Champions": {"avg_engagement": 0.35, "conversion_rate": 0.65},
            "Highly Engaged": {"avg_engagement": 0.25, "conversion_rate": 0.50},
            "Potential Loyalists": {"avg_engagement": 0.15, "conversion_rate": 0.35},
            "At Risk": {"avg_engagement": 0.08, "conversion_rate": 0.25},
            "Low Value": {"avg_engagement": 0.03, "conversion_rate": 0.15}
        }
    
    def segmentation_agent_node(state: AgentState) -> dict:
        """Analyze segments and provide marketing insights."""
        
        messages = state.get("messages", [])
        
        # Get the user's question
        user_question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break
        
        # Format segment info for prompt
        segment_str = json.dumps(segment_info, indent=2)
        
        # Generate analysis
        response = llm.invoke([
            SystemMessage(content=SEGMENTATION_PROMPT.format(segment_info=segment_str)),
            HumanMessage(content=f"Analyze segments for this request: {user_question}")
        ])
        
        analysis = response.content
        
        return {
            "messages": [AIMessage(content=f"[Segmentation Analyst]\n{analysis}")],
            "segment_analysis": analysis
        }
    
    return segmentation_agent_node
