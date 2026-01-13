"""
Data Visualization Agent
========================

Creates charts, visualizations, and BI analytics from data.
"""

import json
import pandas as pd
from io import StringIO
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


DATAVIZ_PROMPT = """You are a Data Visualization and BI Analytics expert.

Analyze the following data and provide:
1. Key insights and patterns
2. Recommendations based on the findings

Data columns: {columns}
Data summary:
{data_summary}

User question: {question}

Provide 3-5 bullet points of actionable insights.
"""


def create_dataviz_agent(llm):
    """Create the data visualization agent node function."""
    
    def dataviz_agent_node(state: AgentState) -> dict:
        """Create visualizations and analytics from data."""
        
        messages = state.get("messages", [])
        leads_data = state.get("leads_data")
        
        # Get the user question
        user_question = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break
        
        q_lower = user_question.lower()
        
        # Check if we have data to visualize
        if not leads_data:
            return {
                "messages": [AIMessage(content="[Data Viz Agent]\n⚠️ No data available. Please query data first.")],
                "is_complete": True
            }
        
        # Parse the data - handle JSON records format
        try:
            data_list = json.loads(leads_data)
            df = pd.DataFrame(data_list)
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"[Data Viz Agent]\n⚠️ Could not parse data: {str(e)}")],
                "is_complete": True
            }
        
        if df.empty:
            return {
                "messages": [AIMessage(content="[Data Viz Agent]\n⚠️ Data is empty.")],
                "is_complete": True
            }
        
        # Build response
        result_parts = []
        chart_data = None
        
        # Determine what column to use for chart
        # Priority: Segment > Lead_Source > Country > first string column
        chart_col = None
        
        # Check if SQL already aggregated the data (has 'count' column)
        if 'count' in df.columns:
            # Data is already aggregated - use as-is
            label_col = [c for c in df.columns if c != 'count'][0] if len(df.columns) > 1 else df.columns[0]
            labels = df[label_col].astype(str).tolist()
            values = df['count'].tolist()
            chart_col = label_col
        else:
            # Need to aggregate data ourselves
            # Find best column to aggregate
            str_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if 'Segment' in df.columns:
                chart_col = 'Segment'
            elif 'Lead_Source' in df.columns:
                chart_col = 'Lead_Source'
            elif 'Country' in df.columns:
                chart_col = 'Country'
            elif 'Occupation' in df.columns:
                chart_col = 'Occupation'
            elif str_cols:
                chart_col = str_cols[0]
            
            if chart_col:
                value_counts = df[chart_col].value_counts()
                labels = value_counts.index.astype(str).tolist()
                values = value_counts.values.tolist()
        
        # Determine chart type from user question
        wants_pie = 'pie' in q_lower
        wants_bar = 'bar' in q_lower
        wants_chart = any(w in q_lower for w in ['chart', 'graph', 'plot', 'distribution', 'breakdown', 'visualiz'])
        
        # Create chart if requested and we have data
        if (wants_chart or wants_pie or wants_bar) and chart_col and labels and values:
            chart_type = "pie" if wants_pie else "bar"
            chart_data = {
                "type": chart_type,
                "labels": labels,
                "values": [int(v) for v in values],  # Ensure integers
                "title": f"Distribution by {chart_col}"
            }
            
            result_parts.append(f"**📊 {chart_col} Distribution:**")
            total = sum(values)
            for label, count in zip(labels, values):
                pct = (count / total * 100) if total > 0 else 0
                result_parts.append(f"- {label}: {count} ({pct:.1f}%)")
        
        # Generate analytics summary
        result_parts.append(f"\n**📈 Data Summary:**")
        result_parts.append(f"- Total records: {len(df)}")
        
        if 'engagement_score' in df.columns:
            try:
                avg_eng = df['engagement_score'].astype(float).mean()
                result_parts.append(f"- Avg engagement: {avg_eng:.3f}")
            except:
                pass
        
        if 'Converted' in df.columns:
            try:
                conv_rate = df['Converted'].astype(float).mean() * 100
                result_parts.append(f"- Conversion rate: {conv_rate:.1f}%")
            except:
                pass
        
        if 'Segment' in df.columns:
            segments = df['Segment'].unique()
            result_parts.append(f"- Segments: {len(segments)} ({', '.join(segments[:5])})")
        
        # LLM analysis for deeper insights
        try:
            data_summary = f"Records: {len(df)}\nColumns: {list(df.columns)}\nSample:\n{df.head(3).to_string()}"
            
            analysis_response = llm.invoke([
                SystemMessage(content=DATAVIZ_PROMPT.format(
                    columns=list(df.columns),
                    data_summary=data_summary,
                    question=user_question
                )),
                HumanMessage(content="Provide your analysis.")
            ])
            
            result_parts.append(f"\n**🔍 Insights:**\n{analysis_response.content}")
        except Exception as e:
            result_parts.append(f"\n**🔍 Insights:** Analysis unavailable.")
        
        # Build final message
        msg_content = "[Data Viz Agent]\n" + "\n".join(result_parts)
        
        if chart_data:
            msg_content += f"\n\n<!--CHART:{json.dumps(chart_data)}-->"
        
        return {
            "messages": [AIMessage(content=msg_content)],
            "is_complete": True
        }
    
    return dataviz_agent_node
