# 🎯 AI Marketing Analytics Team

A multi-agent AI system for marketing analytics, customer segmentation analysis, and automated email generation. Built with LangGraph, Streamlit, and OpenRouter.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Chat%20UI-red.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Agents](#agents)
- [Installation](#installation)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Example Queries](#example-queries)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)
- [Future Improvements](#future-improvements)

---

## 🎯 Overview

This project implements a **multi-agent AI system** designed for marketing teams to:

- **Query customer data** using natural language
- **Generate visualizations** (pie charts, bar charts) automatically
- **Analyze customer segments** (Champions, At Risk, etc.)
- **Write personalized marketing emails** based on customer data
- **Get product information** for campaigns

The system uses a **Plan-and-Execute** pattern with **Human-in-the-Loop** for reliability.

---

## ✨ Features

### Multi-Agent Architecture
- **6 specialized agents** working together via LangGraph
- **Supervisor routing** based on query intent
- **Multi-step workflows** (e.g., query data → create chart → write email)

### Intelligent SQL Generation
- **Plan-and-Execute pattern**: Plans query → Generates SQL → Validates → Executes
- **Schema validation** to prevent invalid queries
- **Human-in-the-Loop** clarification when confused

### Interactive Visualizations
- **Plotly charts** embedded in chat responses
- **Automatic chart type selection** based on data
- Supports pie charts and bar charts

### Robust Error Handling
- **Duplicate prevention** via agent tracking
- **Web search detection** to keep LLM focused
- **Graceful error messages** with recovery options

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Chat UI                           │
│              (Chat history, clarification buttons)              │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────┐
│                         SUPERVISOR                               │
│                  (Intent detection & routing)                    │
└────┬─────────┬──────────┬──────────┬──────────┬─────────────────┘
     │         │          │          │          │
     ▼         ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   SQL   │ │ DataViz │ │Segment  │ │ Product │ │  Email  │
│  Agent  │ │  Agent  │ │ Analyst │ │ Expert  │ │ Writer  │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │          │          │          │
     └───────────┴──────────┴──────────┴──────────┘
                            │
                    ┌───────▼───────┐
                    │   SQLite DB   │
                    │  (leadscored) │
                    └───────────────┘
```

### Workflow Flow

```
User Query → Supervisor → Agent(s) → Response with Charts/Data
                ↑              │
                └──────────────┘
              (multi-step if needed)
```

---

## 🤖 Agents

### 1. Supervisor Agent
**Role:** Routes user requests to appropriate agents

- Keyword-based fast routing
- Tracks completed agents to prevent loops
- Manages multi-step workflows

### 2. SQL Agent
**Role:** Generates and executes SQL queries

**Features:**
- Plan-and-Execute pattern:
  1. **PLAN**: Creates natural language query plan
  2. **DETECT**: Checks for invalid responses (web content)
  3. **VALIDATE**: Verifies SQL against schema
  4. **EXECUTE**: Runs query and returns data

- Human-in-the-Loop for ambiguous queries

### 3. DataViz Agent
**Role:** Creates visualizations and analytics

- Generates Plotly pie/bar charts
- Calculates summary statistics
- Provides data insights via LLM

### 4. Segmentation Agent
**Role:** Marketing strategy recommendations

- Segment-specific strategies
- Re-engagement tactics for At Risk customers
- Upsell recommendations for Champions

### 5. Product Expert
**Role:** Product information for Learning Labs Pro

- Detailed product descriptions
- Pricing information
- Segment-tailored messaging

### 6. Email Writer
**Role:** Generates marketing emails

- Segment-aware tone and messaging
- Subject lines and CTAs
- Uses lead data and product info

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd AI-segmentation
```

2. **Install dependencies**
```bash
uv sync
```

3. **Create the database**
```bash
uv run python scripts/create_segments.py
```

4. **Set up API key**
Get an API key from [OpenRouter](https://openrouter.ai) and enter it in the app sidebar.

5. **Run the application**
```bash
uv run streamlit run app.py
```

---

## 💡 Usage

### Starting the App
```bash
uv run streamlit run app.py
```

### Chat Interface
1. Enter your OpenRouter API key in the sidebar
2. Type your question in the chat input
3. View results with data tables and charts

### Clarification Workflow
If the agent is confused:
1. Agent shows clarification options as buttons
2. Click an option to clarify your intent
3. Agent retries with the clarification

---

## 📊 Database Schema

### Table: `leadscored`

| Column | Type | Description |
|--------|------|-------------|
| customer_id | TEXT | Unique customer identifier |
| Segment | TEXT | Customer segment (Champions, At Risk, etc.) |
| engagement_score | FLOAT | 0-1 engagement metric |
| TotalVisits | INT | Website visits |
| Total_Time_Spent_on_Website | FLOAT | Time on site (seconds) |
| Page_Views_Per_Visit | FLOAT | Pages per session |
| Converted | INT | 1=converted, 0=not |
| Lead_Source | TEXT | Traffic source |
| Lead_Origin | TEXT | Lead origin channel |
| Country | TEXT | Customer country |
| City | TEXT | Customer city |
| Specialization | TEXT | Professional specialization |
| Occupation | TEXT | Current occupation |
| Last_Activity | TEXT | Last recorded activity |

### Segments
- **Champions** - High engagement, high value
- **Highly Engaged** - Active but not converted
- **Potential Loyalists** - Emerging prospects
- **At Risk** - Declining engagement
- **Low Value** - Minimal engagement

---

## 📝 Example Queries

### Data Queries
```
Show top 20 Champions
What is the segment distribution?
How many customers from India?
Show lead source breakdown
```

### Visualization Queries
```
Show segment distribution with a pie chart
Create a bar chart of lead sources
Visualize country distribution
```

### Multi-Step Queries
```
Find top 5 Highly Engaged customers and write them an email about Learning Labs Pro
Show At Risk segment and suggest re-engagement strategy
```

### Strategy Queries
```
How should I re-engage At Risk customers?
What's the best approach for Champions?
```

---

## ⚙️ Configuration

### OpenRouter Settings
In `marketing_analytics_team/teams.py`:

```python
llm = ChatOpenAI(
    model="anthropic/claude-3.5-haiku",  # Change model here
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.5,  # Lower = more consistent
    max_tokens=4096
)
```

### Available Models
- `anthropic/claude-3.5-haiku` (fast, cheap)
- `anthropic/claude-3.5-sonnet` (better quality)
- `openai/gpt-4o-mini` (OpenAI alternative)
- `google/gemini-pro` (Google alternative)

---

## 📁 Project Structure

```
AI-segmentation/
├── app.py                          # Streamlit UI
├── pyproject.toml                  # Dependencies
├── README.md                       # This file
│
├── data/
│   ├── leadscored.db              # SQLite database
│   ├── leadscored_clean.csv       # Source data
│   └── segment_descriptions.json  # Segment metadata
│
├── marketing_analytics_team/
│   ├── __init__.py                # Package exports
│   ├── state.py                   # Shared agent state
│   ├── teams.py                   # LangGraph workflow
│   │
│   └── agents/
│       ├── __init__.py            # Agent exports
│       ├── supervisor.py          # Routing agent
│       ├── sql_agent.py           # SQL with HITL
│       ├── dataviz_agent.py       # Charts & analytics
│       ├── segmentation_agent.py  # Strategy agent
│       ├── product_expert.py      # Product info
│       └── email_writer.py        # Email generation
│
└── scripts/
    └── create_segments.py         # Database setup
```

---

## 🔧 Technical Details

### State Management
Shared state via `AgentState` TypedDict:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: Optional[str]
    leads_data: Optional[str]
    needs_clarification: bool
    clarification_options: Optional[List[str]]
    # ... more fields
```

### Human-in-the-Loop Flow
1. SQL Agent detects invalid response (web content, gaming terms)
2. Returns `needs_clarification=True` with options
3. UI displays buttons for user selection
4. User clicks option → stored in session state
5. Query re-runs with `user_clarification` parameter

### Duplicate Prevention
- `completed_agents` list tracks finished agents
- `seen_content` set deduplicates messages in UI
- `current_step` counter prevents infinite loops

```

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [Streamlit](https://streamlit.io/) - Web UI framework
- [OpenRouter](https://openrouter.ai/) - LLM API gateway
- [Plotly](https://plotly.com/) - Interactive charts





