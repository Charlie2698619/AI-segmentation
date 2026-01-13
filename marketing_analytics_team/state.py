"""
Marketing Analytics Team - Multi-Agent State
=============================================

Defines the shared state for the LangGraph workflow.
"""

from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state for the marketing analytics team workflow."""
    
    # Conversation messages - uses LangGraph's message reducer
    messages: Annotated[list, add_messages]
    
    # Current routing decision
    next_agent: Optional[str]
    
    # Data passed between agents
    leads_data: Optional[str]  # JSON string of leads from SQL agent
    product_info: Optional[str]  # Product details from Product Expert
    segment_analysis: Optional[str]  # Analysis from Segmentation agent
    
    # Generated content
    email_draft: Optional[str]  # Email from Email Writer
    
    # SQL Plan-and-Execute state
    sql_plan: Optional[str]  # Natural language plan for SQL
    sql_query: Optional[str]  # Generated SQL query
    sql_validation_error: Optional[str]  # Validation error if any
    
    # Visualization flag
    needs_visualization: bool  # True if user requested charts/graphs
    
    # Human-in-the-Loop state
    needs_clarification: bool  # True if agent needs user input
    clarification_question: Optional[str]  # Question to ask user
    clarification_options: Optional[List[str]]  # Options for user to choose
    user_clarification: Optional[str]  # User's response to clarification
    
    # Workflow control
    is_complete: bool
    current_step: int
    completed_agents: List[str]  # Track which agents have finished
