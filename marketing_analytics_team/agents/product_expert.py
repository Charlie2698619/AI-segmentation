"""
Product Expert Agent
====================

Provides detailed information about products, specifically "Learning Labs Pro".
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..state import AgentState


# Hard-coded product information as specified in requirements
PRODUCT_CATALOG = {
    "Learning Labs Pro": {
        "name": "Learning Labs Pro",
        "tagline": "Accelerate Your Career with Hands-On Learning",
        "description": """Learning Labs Pro is our flagship professional development platform 
designed for ambitious professionals looking to advance their careers.

Key Features:
• 500+ hands-on labs and projects across tech, business, and leadership
• AI-powered portfolio builder that showcases your skills to employers
• Personalized learning paths based on your career goals
• Industry-recognized certifications included
• 1-on-1 mentorship sessions with industry experts
• Job placement assistance and interview preparation

Career Advancement Benefits:
• Build a professional portfolio demonstrating real-world skills
• Earn certifications valued by Fortune 500 companies
• Get discovered by recruiters through our talent marketplace
• Average 40% salary increase reported by completers

Pricing:
• Monthly: $149/month
• Annual: $999/year (save 44%)
• Enterprise: Custom pricing for teams

Success Stories:
• 87% of users report career advancement within 6 months
• 92% satisfaction rate from 50,000+ professionals
• Featured in Forbes as "Best Career Development Platform 2024"

Ideal For:
• Working professionals seeking promotion or career change
• Recent graduates building their portfolios
• Teams looking to upskill employees
• Anyone wanting practical, hands-on learning""",
        "price_monthly": 149,
        "price_annual": 999,
        "target_audience": "Working professionals, recent graduates, career changers",
        "key_benefits": [
            "Build a professional portfolio",
            "Earn industry certifications", 
            "Get mentorship from experts",
            "Job placement assistance"
        ]
    }
}


PRODUCT_EXPERT_PROMPT = """You are a Product Expert for Learning Labs Pro.

PRODUCT INFO:
{product_info}

Provide a brief, compelling summary of Learning Labs Pro that can be used in a marketing email.
Focus on: key benefits, pricing, and value proposition.
Keep it concise (2-3 paragraphs).
"""


def create_product_expert(llm):
    """Create the product expert agent node function."""
    
    def product_expert_node(state: AgentState) -> dict:
        """Provide product information for marketing use."""
        
        messages = state.get("messages", [])
        
        # Get the request
        request = ""
        for msg in reversed(messages):
            if isinstance(msg, (HumanMessage, AIMessage)):
                request = msg.content
                break
        
        # Check which product is being asked about
        product_info = PRODUCT_CATALOG.get("Learning Labs Pro", {})
        product_str = f"""
Product: {product_info.get('name', 'Learning Labs Pro')}
Tagline: {product_info.get('tagline', '')}

{product_info.get('description', '')}
"""
        
        # Generate context-aware product information
        response = llm.invoke([
            SystemMessage(content=PRODUCT_EXPERT_PROMPT.format(product_info=product_str)),
            HumanMessage(content=f"Provide product information for: {request}")
        ])
        
        return {
            "messages": [AIMessage(content=f"[Product Expert]\n{response.content}")],
            "product_info": product_str
        }
    
    return product_expert_node
