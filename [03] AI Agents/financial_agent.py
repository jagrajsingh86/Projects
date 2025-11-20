from phi.agent import Agent
from phi.model.groq import Groq
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from groq import APIError
import os
import httpx

client = Groq(
api_key=os.environ.get("GROQ_API_KEY "),
http_client=httpx.Client(verify=False),  # Disable SSL verification
)


raw_key = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = raw_key.strip()  # <-- removes trailing newline
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


##Web Search Agent
web_agent = Agent(
    name="Web Agent",
    role="Search the web for the information",
    model=Groq(id="llama-3.3-70b-versatile"),
 #   model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True,
)

web_agent.print_response("Tell me about Nike Stock", stream=True)


##Financial Agent
Finance_agent=Agent(
    name="Finance Agent",
#    role="Answer questions about financial markets",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=["Always include sources", "Use Tables to Structure the data","Use YFinance API for real-time data"],
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True, company_news=True)],
    show_tool_calls=True,
    markdown=True,
)

multi_ai_agent = Agent(team=[web_agent, Finance_agent],
instructions=["Always include sources", "Use the table to display the data"],
show_tool_calls=True,
markdown =True,
)

multi_ai_agent.print_response("Summarize analyst recommendation and share latest news for LUBUBU", stream=True)