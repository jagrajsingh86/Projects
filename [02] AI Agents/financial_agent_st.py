import streamlit as st
import os
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from openai import APIError

# --- Environment Setup ---
oai_key = os.getenv("OPENAI_API_KEY", "").strip()
if not oai_key:
    raise RuntimeError("Missing OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = oai_key

# Build OpenAIChat client for function-calling
oai_client = OpenAIChat(id="gpt-4o", api_key=oai_key)

# --- Define Agents ---
web_agent = Agent(
    name="Web Agent",
    role="Search the web",
    model=oai_client,
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=False,
    markdown=True,
)
finance_agent = Agent(
    name="Finance Agent",
    model=oai_client,
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            stock_fundamentals=True,
            company_news=True
        )
    ],
    instructions=["Always include sources", "Use tables to structure the data"],
    show_tool_calls=False,
    markdown=True,
)
multi_agent = Agent(
    team=[web_agent, finance_agent],
    instructions=["Always include sources", "Use tables to structure the data"],
    show_tool_calls=False,
    markdown=True,
)

# --- Streamlit UI ---
st.set_page_config(page_title="Financial Analyst", layout="wide")
st.title("Financial Analyst")
st.subheader("Enter the company name")

# Persist input
if 'company' not in st.session_state:
    st.session_state.company = ''
st.session_state.company = st.text_input("Company Name", st.session_state.company)

@st.cache_data
# Fetch and combine chunks by reading .content attribute
def fetch_data(company: str) -> str:
    prompt = (
        f"Lookup the ticker for '{company}' and fetch analyst recommendations, "
        "stock price, fundamentals, and recent news. Present results in tables with sources."
    )
    buffer = []
    for chunk in multi_agent.run(message=prompt, stream=True):
        # use 'content' for actual responses
        content = getattr(chunk, 'content', None) or getattr(chunk, 'text', '')
        if content:
            buffer.append(content)
    return "".join(buffer)

output = st.empty()
if st.button("Run") and st.session_state.company.strip():
    with st.spinner("Fetching data..."):
        try:
            result = fetch_data(st.session_state.company)
            if result:
                output.markdown(result)
            else:
                output.warning("No response received—check your query or try again.")
        except APIError as e:
            output.error(f"APIError: {e}")
        except Exception as e:
            output.error(f"Unexpected error: {e}")
else:
    output.info("Please enter a company name and click Run.")
