"""
Marketing Analytics Team - Streamlit Application
=================================================

Chat interface for interacting with the multi-agent marketing analytics system.
"""

import streamlit as st
from pathlib import Path
import os
import plotly.express as px
import plotly.graph_objects as go

# Cache the workflow to avoid re-initialization on every interaction
@st.cache_resource
def get_workflow(api_key: str):
    """Initialize and cache the marketing analytics team workflow."""
    from marketing_analytics_team import make_marketing_analytics_team
    return make_marketing_analytics_team(openrouter_api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="Marketing Analytics Team",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for a modern look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .agent-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .supervisor-msg { background-color: #fef3c7; border-left: 4px solid #f59e0b; }
    .bi-msg { background-color: #dbeafe; border-left: 4px solid #3b82f6; }
    .seg-msg { background-color: #dcfce7; border-left: 4px solid #22c55e; }
    .product-msg { background-color: #fce7f3; border-left: 4px solid #ec4899; }
    .email-msg { background-color: #f3e8ff; border-left: 4px solid #a855f7; }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📊 Marketing Analytics Team</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Multi-Agent AI System for Lead Analysis & Marketing Automation</p>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        help="Enter your OpenRouter API key (get one at openrouter.ai)",
        value=os.environ.get("OPENROUTER_API_KEY", "")
    )
    
    if api_key:
        os.environ["OPENROUTER_API_KEY"] = api_key
        st.success("✓ API Key configured")
    
    # Clear cache button
    if st.button("🔄 Clear Cache & Reload"):
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    
    # Example queries
    st.header("💡 Example Queries")
    example_queries = [
        "What are the characteristics of top 20 Champions? Show demographics",
        "Show me segment distribution with a pie chart",
        "Top 10 converted leads and their Lead Source breakdown",
        "Analyze At Risk segment - how to re-engage them?",
        "Write an email for top 5 Highly Engaged customers about Learning Labs Pro"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"ex_{query[:20]}"):
            st.session_state.run_query = query
    
    st.divider()
    
    # Database info
    st.header("📁 Data Source")
    db_path = Path(__file__).parent / "data" / "leadscored.db"
    if db_path.exists():
        st.success(f"✓ Database: leadscored.db")
        
        # Show segment counts
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT Segment, COUNT(*) FROM leadscored GROUP BY Segment ORDER BY COUNT(*) DESC")
            segments = cursor.fetchall()
            conn.close()
            
            st.caption("Segment Distribution:")
            for seg, count in segments:
                st.caption(f"• {seg}: {count:,}")
        except:
            pass
    else:
        st.warning("⚠️ Database not found. Run setup scripts first.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Track if we need to process a query
query_to_run = None

# Check for query from example button click
if "run_query" in st.session_state:
    query_to_run = st.session_state.run_query
    del st.session_state.run_query

# Display chat history
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            # Apply styling based on agent type
            if "[Supervisor]" in content:
                st.markdown(f'<div class="agent-message supervisor-msg">{content}</div>', unsafe_allow_html=True)
            elif "[BI Agent]" in content:
                st.markdown(content)  # Contains markdown tables
            elif "[Segmentation Analyst]" in content:
                st.markdown(f'<div class="agent-message seg-msg">{content}</div>', unsafe_allow_html=True)
            elif "[Product Expert]" in content:
                st.markdown(f'<div class="agent-message product-msg">{content}</div>', unsafe_allow_html=True)
            elif "[Email Writer]" in content:
                st.markdown(content)
            else:
                st.write(content)

# Chat input - also handles example button clicks
prompt = st.chat_input("Ask about leads, segments, or request marketing content...")

# Use example query if button was clicked
if query_to_run:
    prompt = query_to_run

if prompt:
    # Check API key
    if not api_key:
        st.error("⚠️ Please enter your OpenRouter API key in the sidebar")
        st.stop()
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Use cached workflow
    workflow = get_workflow(api_key)
    
    # Check for pending clarification
    user_clarification = None
    if hasattr(st.session_state, 'pending_clarification') and st.session_state.pending_clarification:
        user_clarification = st.session_state.pending_clarification
        prompt = st.session_state.get('original_prompt', prompt)
        st.session_state.pending_clarification = None
        st.session_state.original_prompt = None
    
    # Run the query
    with st.chat_message("assistant"):
        with st.spinner("🔄 Agents working on your request..."):
            try:
                from marketing_analytics_team.teams import run_team_query
                import json
                import re
                
                result = run_team_query(workflow, prompt, user_clarification)
                
                # Extract messages from result
                messages = result.get("messages", [])
                
                response_parts = []
                seen_content = set()  # Track seen content to prevent duplicates
                
                for msg in messages:
                    content = getattr(msg, 'content', str(msg))
                    
                    # Skip supervisor routing messages and empty content
                    if not content or content.startswith("[Supervisor]"):
                        continue
                    
                    # Skip duplicates based on first 100 chars
                    content_key = content[:100]
                    if content_key in seen_content:
                        continue
                    seen_content.add(content_key)
                    
                    # Check for embedded chart data
                    chart_match = re.search(r'<!--CHART:(.+?)-->', content, re.DOTALL)
                    chart_data = None
                    display_content = content
                    
                    if chart_match:
                        try:
                            chart_data = json.loads(chart_match.group(1))
                            display_content = content.replace(chart_match.group(0), "")
                        except:
                            pass
                    
                    response_parts.append(display_content)
                    
                    # Display content with appropriate styling
                    if "[SQL Agent]" in content:
                        st.markdown(display_content)
                    
                    elif "[Data Viz Agent]" in content:
                        st.markdown(display_content)
                        
                        # Render chart if present
                        if chart_data:
                            chart_type = chart_data.get("type", "bar")
                            labels = chart_data.get("labels", [])
                            values = chart_data.get("values", [])
                            title = chart_data.get("title", "Chart")
                            
                            if chart_type == "pie":
                                fig = go.Figure(data=[go.Pie(
                                    labels=labels, 
                                    values=values,
                                    hole=0.3,
                                    textinfo='label+percent'
                                )])
                                fig.update_layout(title=title, height=400)
                            else:
                                fig = go.Figure(data=[go.Bar(x=labels, y=values)])
                                fig.update_layout(title=title, height=400, xaxis_title="", yaxis_title="Count")
                            
                            st.plotly_chart(fig)
                    
                    elif "[Segmentation Analyst]" in content:
                        st.markdown(f'<div class="agent-message seg-msg">{display_content}</div>', unsafe_allow_html=True)
                    elif "[Product Expert]" in content:
                        st.markdown(f'<div class="agent-message product-msg">{display_content}</div>', unsafe_allow_html=True)
                    elif "[Email Writer]" in content:
                        st.markdown(display_content)
                    else:
                        st.markdown(display_content)
                
                # Check if clarification is needed
                needs_clarification = result.get("needs_clarification", False)
                clarification_options = result.get("clarification_options", [])
                
                if needs_clarification and clarification_options:
                    st.markdown("---")
                    st.markdown("**🤔 Please choose an option:**")
                    
                    cols = st.columns(len(clarification_options))
                    for i, option in enumerate(clarification_options):
                        if cols[i].button(option, key=f"clarify_{i}_{option[:10]}"):
                            # Store the clarification and re-run
                            st.session_state.pending_clarification = option
                            st.session_state.original_prompt = prompt
                            st.rerun()
                
                # Store response in history (deduplicated)
                full_response = "\n\n---\n\n".join(response_parts) if response_parts else "No response."
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.caption("🤖 Powered by LLM + LangGraph | Multi-Agent Marketing Intelligence")


