"""
Marketing Analytics Team - LangGraph Workflow
==============================================

Orchestrates the multi-agent workflow using LangGraph with Plan-and-Execute pattern.
"""

from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import AgentState
from .agents import (
    create_supervisor,
    create_sql_agent,
    create_dataviz_agent,
    create_segmentation_agent,
    create_product_expert,
    create_email_writer
)


def make_marketing_analytics_team(
    openrouter_api_key: str,
    db_path: Path = None,
    data_path: Path = None,
    model: str = "anthropic/claude-3.5-haiku"
):
    """Create and compile the marketing analytics team LangGraph workflow."""
    
    # Set default paths
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "leadscored.db"
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data"
    
    # Initialize LLM via OpenRouter
    llm = ChatOpenAI(
        model=model,
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.5,  # Lower temperature for more consistent SQL
        max_tokens=4096
    )
    
    # Create agent node functions
    supervisor_node = create_supervisor(llm)
    sql_agent_node = create_sql_agent(llm, db_path)
    dataviz_agent_node = create_dataviz_agent(llm)
    segmentation_agent_node = create_segmentation_agent(llm, data_path)
    product_expert_node = create_product_expert(llm)
    email_writer_node = create_email_writer(llm)
    
    # Build the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("dataviz_agent", dataviz_agent_node)
    workflow.add_node("segmentation_agent", segmentation_agent_node)
    workflow.add_node("product_expert", product_expert_node)
    workflow.add_node("email_writer", email_writer_node)
    
    # Routing function from supervisor
    def route_from_supervisor(state: AgentState) -> str:
        next_agent = state.get("next_agent", "COMPLETE")
        current_step = state.get("current_step", 0)
        
        # Safety: prevent infinite loops
        if current_step > 8:
            return "__end__"
        
        routing = {
            "SQL_AGENT": "sql_agent",
            "DATAVIZ_AGENT": "dataviz_agent",
            "SEGMENTATION_AGENT": "segmentation_agent", 
            "PRODUCT_EXPERT": "product_expert",
            "EMAIL_WRITER": "email_writer",
            "COMPLETE": "__end__"
        }
        return routing.get(next_agent, "__end__")
    
    # Routing after SQL agent - check if visualization needed
    def route_after_sql(state: AgentState) -> str:
        needs_viz = state.get("needs_visualization", False)
        leads_data = state.get("leads_data")
        is_complete = state.get("is_complete", False)
        completed_agents = state.get("completed_agents", [])
        
        # If SQL failed or marked complete, go to supervisor
        if is_complete or not leads_data:
            return "supervisor"
        
        # If visualization needed and not yet done, go to dataviz
        if needs_viz and "DATAVIZ_AGENT" not in completed_agents:
            return "dataviz_agent"
        
        # Otherwise back to supervisor
        return "supervisor"
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Supervisor routes to agents
    workflow.add_conditional_edges("supervisor", route_from_supervisor)
    
    # SQL agent has conditional routing for visualization
    workflow.add_conditional_edges("sql_agent", route_after_sql)
    
    # Other agents go back to supervisor
    workflow.add_edge("dataviz_agent", "supervisor")  
    workflow.add_edge("segmentation_agent", "supervisor")
    workflow.add_edge("product_expert", "supervisor")
    workflow.add_edge("email_writer", END)  # Email is final
    
    return workflow.compile()


def run_team_query(app, user_message: str, user_clarification: str = None) -> dict:
    """Run a query through the marketing analytics team."""
    from langchain_core.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "next_agent": None,
        "leads_data": None,
        "product_info": None,
        "segment_analysis": None,
        "email_draft": None,
        "sql_plan": None,
        "sql_query": None,
        "sql_validation_error": None,
        "needs_visualization": False,
        "needs_clarification": False,
        "clarification_question": None,
        "clarification_options": None,
        "user_clarification": user_clarification,
        "is_complete": False,
        "current_step": 0,
        "completed_agents": []
    }
    
    return app.invoke(initial_state)
