"""
Supervisor Agent
================

Routes user requests to the appropriate sub-agent with multi-step support.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


def create_supervisor(llm):
    """Create the supervisor node function."""
    
    def supervisor_node(state: AgentState) -> dict:
        """Route to the appropriate sub-agent based on user request."""
        
        messages = state.get("messages", [])
        current_step = state.get("current_step", 0)
        completed_agents = state.get("completed_agents", [])
        leads_data = state.get("leads_data")
        product_info = state.get("product_info")
        
        # Get the original user question
        user_request = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_request = msg.content
                break
        
        request_lower = user_request.lower()
        
        # Determine what the user needs
        needs_sql = any(kw in request_lower for kw in [
            'top', 'show', 'list', 'find', 'get', 'count', 'how many', 'customer'
        ])
        needs_viz = any(kw in request_lower for kw in [
            'chart', 'pie', 'bar', 'graph', 'plot', 'distribution', 'breakdown',
            'visualiz', 'demographic', 'characteristic', 'analysis', 'insight'
        ])
        needs_email = 'email' in request_lower
        needs_product = 'learning labs' in request_lower
        needs_strategy = any(kw in request_lower for kw in [
            'strategy', 'recommend', 'approach', 'how to', 'marketing plan', 're-engage'
        ])
        
        # Step 1: SQL Agent first to get data
        if needs_sql and "SQL_AGENT" not in completed_agents:
            return {
                "next_agent": "SQL_AGENT",
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["SQL_AGENT"],
                "needs_visualization": needs_viz,  # Carry forward for conditional routing
                "messages": []
            }
        
        # Step 2: DataViz Agent for visualization/analysis (after data)
        if needs_viz and "DATAVIZ_AGENT" not in completed_agents:
            if leads_data or not needs_sql:  # Have data or don't need it
                return {
                    "next_agent": "DATAVIZ_AGENT",
                    "current_step": current_step + 1,
                    "completed_agents": completed_agents + ["DATAVIZ_AGENT"],
                    "messages": []
                }
        
        # Step 3: Product Expert if needed for email
        if needs_product and needs_email and "PRODUCT_EXPERT" not in completed_agents:
            return {
                "next_agent": "PRODUCT_EXPERT",
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["PRODUCT_EXPERT"],
                "messages": []
            }
        
        # Step 4: Email Writer
        if needs_email and "EMAIL_WRITER" not in completed_agents:
            return {
                "next_agent": "EMAIL_WRITER", 
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["EMAIL_WRITER"],
                "messages": []
            }
        
        # Segmentation strategy (standalone)
        if needs_strategy and "SEGMENTATION_AGENT" not in completed_agents:
            return {
                "next_agent": "SEGMENTATION_AGENT",
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["SEGMENTATION_AGENT"],
                "messages": []
            }
        
        # Product questions (standalone)
        if needs_product and not needs_email and "PRODUCT_EXPERT" not in completed_agents:
            return {
                "next_agent": "PRODUCT_EXPERT",
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["PRODUCT_EXPERT"],
                "messages": []
            }
        
        # Default to SQL for data queries
        if "SQL_AGENT" not in completed_agents:
            return {
                "next_agent": "SQL_AGENT",
                "current_step": current_step + 1,
                "completed_agents": completed_agents + ["SQL_AGENT"],
                "needs_visualization": needs_viz,
                "messages": []
            }
        
        # All done
        return {
            "next_agent": "COMPLETE",
            "current_step": current_step + 1,
            "is_complete": True,
            "messages": []
        }
    
    return supervisor_node
