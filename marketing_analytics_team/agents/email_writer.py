"""
Marketing Email Writer Agent
=============================

Writes persuasive sales emails for targeted lead lists.
"""

import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


EMAIL_WRITER_PROMPT = """You are an expert Marketing Email Writer specializing in personalized content emails.

Your emails should:
1. Have an attention-grabbing subject line
2. Personalize based on the audience segment
3. Clearly articulate the value proposition
4. Include a compelling call-to-action
5. Be concise yet persuasive
6. Follow best practices for email deliverability
7. Understand the campaign goal (reactivation, upsell, product launch)
8. Adapt the tone/style appropriately (friendly, professional, urgent)
9. Generate a plain-text version

Segment-specific tone:
- Champions: VIP treatment, exclusive offers, loyalty appreciation
- Highly Engaged: Value reinforcement, success case studies, premium features
- Potential Loyalists: Nurturing, educational content, special onboarding
- At Risk: Re-engagement, win-back offers, "we miss you" messaging
- Low Value: Awareness building, introductory offers, low-friction CTAs

Target Audience Info:
{leads_info}

Product Info:
{product_info}

Write a complete marketing email including:
- Subject Line
- Preview Text
- Email Body (greeting, hook, value prop, CTA)
- Postscript (P.S.) with urgency element
"""


def create_email_writer(llm):
    """Create the email writer agent node function."""
    
    def email_writer_node(state: AgentState) -> dict:
        """Write a marketing email based on leads and product info."""
        
        messages = state.get("messages", [])
        leads_data = state.get("leads_data")
        product_info = state.get("product_info")
        
        # Parse leads info
        if leads_data:
            try:
                leads_list = json.loads(leads_data)
                num_leads = len(leads_list)
                # Extract segment info if available
                if leads_list and 'Segment' in leads_list[0]:
                    segment = leads_list[0]['Segment']
                else:
                    segment = "Targeted prospects"
                leads_info = f"Sending to {num_leads} leads in segment: {segment}"
            except:
                leads_info = "Targeted lead list"
        else:
            leads_info = "General prospect list"
        
        # Get product info
        if not product_info:
            product_info = """Learning Labs Pro - Professional development platform 
for career advancement with hands-on labs, portfolio building, and certifications."""
        
        # Get original user request for context
        user_request = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_request = msg.content
                break
        
        # Generate the email
        response = llm.invoke([
            SystemMessage(content=EMAIL_WRITER_PROMPT.format(
                leads_info=leads_info,
                product_info=product_info
            )),
            HumanMessage(content=f"Write a sales email for this request: {user_request}")
        ])
        
        email_content = response.content
        
        return {
            "messages": [AIMessage(content=f"[Email Writer]\n{email_content}")],
            "email_draft": email_content,
            "is_complete": True
        }
    
    return email_writer_node
