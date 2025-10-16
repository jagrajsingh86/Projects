##PDF Assistant
import typer
from typing import Optional, List
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.storage.agent.postgres import PgAgentStorage

import os
from dotenv import load_dotenv

#Load environment variables
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "").strip()  # Remove trailing newline
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY","").strip()  # Remove trailing newline

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://www.ucm.es/data/cont/docs/119-2014-04-09-Wuthering%20Heights.pdf"],
    vector_db=PgVector(table_name="recipes", db_url=db_url, search_type=SearchType.hybrid),
)

knowledge_base.load()
storage= PgAgentStorage(table_name="pdf_assistant", db_url=db_url)

def pdf_assistant(new:bool=False, user: str = user):
    run_id: Optional[str] = None,

    if not new:
        existing_run_id: List[str] = storage.get_all_run_ids(user)
        if len(existing_run_id) > 0:
            run_id = existing_run_id[0]
    """
    A simple PDF assistant that searches for information in PDF documents.
    """
    agent = Agent(
        run_id = run_id,
        user_id = user,
#        name="PDF Assistant",
#        role="Search and provide information from PDF documents.",
        knowledge_base=knowledge_base,
        storage=storage,
        instructions=["Search for the topic in the provided PDFs and return relevant information."],
        markdown=True,
        show_tool_calls=True,
        search_knowledge=True,
        read_chat_history=True,
    )
    if run_id is None:
        run_id = agent.run_id
        print(f"Started a new run with ID: {run_id}\n")
    else:
        print(f"Resuming run with ID: {run_id}\n")
    agent.cli_app(markdown=True)

if __name__ == "__main__":
    typer.run(pdf_assistant)