"""
SQL Agent with Plan-and-Execute + Human-in-the-Loop
====================================================

Workflow:
1. PLAN: Create a natural language plan for the query
2. DETECT: Check if response is valid SQL (not web content)
3. CLARIFY: If confused, ask user for clarification
4. VALIDATE: Check the SQL against schema 
5. EXECUTE: Run the validated SQL
"""

import sqlite3
import pandas as pd
import json
import re
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


# Database schema for validation
SCHEMA = {
    "table": "leadscored",
    "columns": [
        "customer_id", "Segment", "engagement_score", "TotalVisits",
        "Total_Time_Spent_on_Website", "Page_Views_Per_Visit", "Converted",
        "Lead_Source", "Lead_Origin", "Country", "City", 
        "Specialization", "Occupation", "Last_Activity"
    ],
    "segment_values": ["Champions", "Highly Engaged", "Potential Loyalists", "At Risk", "Low Value"]
}


PLAN_PROMPT = """You are a SQL query planner for a CUSTOMER LEADS database.

CRITICAL CONTEXT:
- "Champions", "Highly Engaged", "At Risk" etc. are CUSTOMER SEGMENT names, NOT sports/games
- This is a marketing database with lead/customer information
- NEVER search the web - use only the database schema provided

Database table: leadscored
Columns: {columns}
Segment values: {segments}

RULES:
- Plan for SIMPLE queries only (single SELECT, basic WHERE, GROUP BY, ORDER BY)
- NO CTEs, NO subqueries, NO complex joins
- If request cannot be answered with this schema, say: CANNOT_ANSWER: [reason]

User request: {question}

Respond with a brief SQL plan (2-3 sentences max):
"""


SQL_GENERATE_PROMPT = """Generate a SIMPLE SQL query based on this plan.

Plan: {plan}

Table: leadscored
Columns: {columns}

RULES:
- Single SELECT statement only
- NO CTEs (WITH clauses) 
- NO subqueries
- NO comments in SQL
- Return ONLY the SQL query

SQL:"""


def detect_invalid_response(response: str) -> tuple[bool, str]:
    """Detect if LLM response is invalid (web content, not SQL)."""
    response_lower = response.lower()
    
    # Check for web search indicators
    web_indicators = [
        "based on the web", "according to", "search results",
        "i found", "from the web", "online sources",
        "wikipedia", "google", "based on my search"
    ]
    for indicator in web_indicators:
        if indicator in response_lower:
            return True, "web_search"
    
    # Check for gaming/sports confusion
    gaming_indicators = [
        "league of legends", "lol champions", "esports",
        "game", "player", "team", "tournament", "sports"
    ]
    for indicator in gaming_indicators:
        if indicator in response_lower:
            return True, "gaming_confusion"
    
    # Check if it doesn't look like SQL at all
    if not any(kw in response.upper() for kw in ['SELECT', 'FROM', 'CANNOT_ANSWER']):
        if len(response) > 100:  # Long non-SQL response
            return True, "not_sql"
    
    return False, ""


def validate_sql(sql: str, schema: dict) -> tuple[bool, str]:
    """Validate SQL against schema. Returns (is_valid, error_message)."""
    sql_upper = sql.upper()
    
    # Check for forbidden patterns
    if 'WITH ' in sql_upper and ' AS ' in sql_upper:
        return False, "CTEs (WITH clauses) are not allowed. Use simple SELECT."
    
    if sql_upper.count('SELECT') > 1:
        return False, "Subqueries are not allowed. Use simple SELECT."
    
    if 'JOIN' in sql_upper:
        return False, "JOINs are not allowed. Only the leadscored table is available."
    
    # Check table name
    if 'leadscored' not in sql.lower():
        return False, f"Invalid table. Only 'leadscored' table exists."
    
    return True, ""


def create_sql_agent(llm, db_path: Path):
    """Create the SQL agent with Plan-and-Execute + Human-in-the-Loop."""
    
    def sql_agent_node(state: AgentState) -> dict:
        """Plan, validate, and execute SQL queries with human clarification."""
        
        messages = state.get("messages", [])
        user_clarification = state.get("user_clarification")
        
        # Get user question
        user_question = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break
        
        # If user provided clarification, incorporate it
        if user_clarification:
            user_question = f"{user_question} (User clarified: {user_clarification})"
        
        q_lower = user_question.lower()
        
        # Detect if visualization is needed
        needs_viz = any(w in q_lower for w in [
            'chart', 'pie', 'bar', 'graph', 'plot', 'visualiz', 'distribution'
        ])
        
        # === STEP 1: PLAN ===
        plan_response = llm.invoke([
            SystemMessage(content=PLAN_PROMPT.format(
                columns=", ".join(SCHEMA["columns"]),
                segments=", ".join(SCHEMA["segment_values"]),
                question=user_question
            ))
        ])
        
        plan = plan_response.content.strip()
        
        # === STEP 2: DETECT INVALID RESPONSE ===
        is_invalid, invalid_type = detect_invalid_response(plan)
        
        if is_invalid:
            # Request human clarification
            if invalid_type == "gaming_confusion":
                return {
                    "messages": [AIMessage(content="[SQL Agent]\n🤔 **Clarification Needed**\n\nI noticed you mentioned 'Champions'. In our database, this refers to a **customer segment**, not gaming/sports.\n\nDid you mean:\n- **Option A:** Champions customer segment (high-value customers)\n- **Option B:** Something else\n\nPlease select an option or rephrase your question.")],
                    "needs_clarification": True,
                    "clarification_question": "Which 'Champions' did you mean?",
                    "clarification_options": ["Champions customer segment", "Something else - let me rephrase"],
                    "is_complete": False
                }
            elif invalid_type == "web_search":
                return {
                    "messages": [AIMessage(content="[SQL Agent]\n🤔 **Clarification Needed**\n\nI was about to search the web, but I should only query our database.\n\nCould you rephrase your question to ask about:\n- Customer segments (Champions, At Risk, etc.)\n- Lead sources, countries, occupations\n- Engagement scores, conversions\n\nWhat specific data would you like from our leads database?")],
                    "needs_clarification": True,
                    "clarification_question": "What database information do you need?",
                    "clarification_options": ["Show segment distribution", "List top customers", "Let me rephrase"],
                    "is_complete": False
                }
            else:
                return {
                    "messages": [AIMessage(content="[SQL Agent]\n🤔 **Clarification Needed**\n\nI'm not sure how to answer this with our database.\n\nAvailable data:\n- Customer segments: Champions, Highly Engaged, Potential Loyalists, At Risk, Low Value\n- Columns: Country, City, Occupation, Lead_Source, engagement_score, Converted\n\nCould you rephrase your question?")],
                    "needs_clarification": True,
                    "clarification_question": "Please rephrase your question",
                    "clarification_options": ["Show all segments", "Show top customers", "Cancel"],
                    "is_complete": False
                }
        
        # Check if plan says cannot answer
        if plan.upper().startswith("CANNOT_ANSWER"):
            return {
                "messages": [AIMessage(content=f"[SQL Agent]\n⚠️ {plan}\n\nAvailable columns: {', '.join(SCHEMA['columns'])}")],
                "sql_plan": plan,
                "leads_data": None,
                "needs_visualization": needs_viz,
                "needs_clarification": False,
                "is_complete": True
            }
        
        # === STEP 3: GENERATE SQL ===
        sql_response = llm.invoke([
            SystemMessage(content=SQL_GENERATE_PROMPT.format(
                plan=plan,
                columns=", ".join(SCHEMA["columns"])
            ))
        ])
        
        sql_text = sql_response.content.strip()
        
        # Check SQL generation for invalid response
        is_invalid_sql, _ = detect_invalid_response(sql_text)
        if is_invalid_sql:
            return {
                "messages": [AIMessage(content="[SQL Agent]\n🤔 **Clarification Needed**\n\nI couldn't generate a valid SQL query for your request.\n\nPlease try asking about:\n- Segment counts or distributions\n- Top customers by engagement\n- Lead source breakdown\n- Country/city statistics")],
                "needs_clarification": True,
                "clarification_question": "What would you like to query?",
                "clarification_options": ["Show segment counts", "Show top 20 Champions", "Show lead sources"],
                "is_complete": False
            }
        
        # Extract SQL from response
        sql_query = None
        select_match = re.search(r'(SELECT\s+.+?;)', sql_text, re.IGNORECASE | re.DOTALL)
        if select_match:
            sql_query = select_match.group(1).strip()
        elif sql_text.upper().startswith('SELECT'):
            sql_query = sql_text.split(';')[0].strip() + ';'
        else:
            sql_query = sql_text
        
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # === STEP 4: VALIDATE ===
        is_valid, validation_error = validate_sql(sql_query, SCHEMA)
        
        if not is_valid:
            return {
                "messages": [AIMessage(content=f"[SQL Agent]\n❌ **SQL Validation Failed:**\n{validation_error}\n\n**Attempted SQL:**\n```sql\n{sql_query}\n```\n\nWould you like to try a simpler query?")],
                "sql_plan": plan,
                "sql_query": sql_query,
                "sql_validation_error": validation_error,
                "needs_clarification": True,
                "clarification_question": "Try a simpler query?",
                "clarification_options": ["Show all segments", "Show top 10 customers", "Cancel"],
                "leads_data": None,
                "needs_visualization": needs_viz,
                "is_complete": False
            }
        
        # === STEP 5: EXECUTE ===
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql(sql_query, conn)
            conn.close()
            
            if len(df) == 0:
                result_text = f"**📋 Plan:** {plan}\n\n**📝 SQL:**\n```sql\n{sql_query}\n```\n\n**Result:** No data found."
                leads_json = None
            else:
                result_text = f"**📋 Plan:** {plan}\n\n**📝 SQL:**\n```sql\n{sql_query}\n```\n\n"
                result_text += f"**✅ Data Retrieved:** {len(df)} rows\n\n"
                result_text += df.head(15).to_markdown(index=False)
                leads_json = df.to_json(orient='records')
                
        except Exception as e:
            error_msg = str(e)
            return {
                "messages": [AIMessage(content=f"[SQL Agent]\n**📋 Plan:** {plan}\n\n**📝 SQL:**\n```sql\n{sql_query}\n```\n\n**❌ Execution Error:** {error_msg}\n\nWould you like to try a different query?")],
                "sql_plan": plan,
                "sql_query": sql_query,
                "needs_clarification": True,
                "clarification_question": "Query failed. Try another?",
                "clarification_options": ["Show segment counts", "Show top customers", "Cancel"],
                "leads_data": None,
                "needs_visualization": needs_viz,
                "is_complete": False
            }
        
        return {
            "messages": [AIMessage(content=f"[SQL Agent]\n{result_text}")],
            "sql_plan": plan,
            "sql_query": sql_query,
            "leads_data": leads_json,
            "needs_visualization": needs_viz,
            "needs_clarification": False,
            "is_complete": False  # Allow further processing
        }
    
    return sql_agent_node
