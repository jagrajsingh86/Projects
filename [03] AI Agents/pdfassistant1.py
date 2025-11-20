## PDF Assistant
import typer
from typing import Optional, List
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.storage.agent.postgres import PgAgentStorage
from phi.document.reader.pdf import PDFReader
from phi.document import Document

import os
import re
import uuid
from dotenv import load_dotenv

# Workaround for missing identity import
import phi.utils
if not hasattr(phi.utils, 'identity'):
    setattr(phi.utils, 'identity', lambda x: x)

# Load environment variables
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "").strip()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "").strip()

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Custom PDF Reader to handle encoding issues and ensure ID generation
class CustomPDFReader(PDFReader):
    def read(self, file_path: str) -> List[Document]:
        documents = super().read(file_path)
        
        # Clean text and ensure IDs
        for doc in documents:
            # Generate UUID if missing
            if not doc.id:
                doc.id = str(uuid.uuid4())
                
            # Clean text from encoding artifacts
            if doc.content:
                # Remove non-printable characters except basic punctuation
                doc.content = re.sub(r'[^\x20-\x7E\u00A0-\u00FF\u2018\u2019\u201C\u201D]', ' ', doc.content)
                # Normalize whitespace
                doc.content = re.sub(r'\s+', ' ', doc.content).strip()
                
        return documents

# Initialize knowledge base with custom reader
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://www.chiangmaiecolodges.com/wp-content/uploads/2020/11/Booklet.pdf"],
    vector_db=PgVector(
        #schema="public",
        db_url=db_url,
        table_name="pdf_documents",
        search_type=SearchType.hybrid
    )
    #reader=PDFUrlReader()  # Use our custom reader
)

# Initialize storage
storage = PgAgentStorage(table_name="pdf_assistant", db_url=db_url)

# Create database schema if needed (important fix!)
try:
    knowledge_base.vector_db.create()
except Exception as e:
    print(f"Schema creation warning: {str(e)}")
    # Often safe to ignore if already exists

# Load knowledge base with recreation to fix schema
knowledge_base.load(recreate=True)  # Recreate to fix schema issues

app = typer.Typer()

@app.command()
def chat(
    new: bool = typer.Option(False, "--new", "-n", help="Start a new conversation"),
    user: str = typer.Option("default_user", "--user", "-u", help="User ID for conversation tracking")
):
    """
    Interactive PDF chatbot that answers questions about the document.
    """
    run_id: Optional[str] = None

    # Resume existing conversation if available
    if not new:
        existing_run_ids: List[str] = storage.get_all_run_ids(user)
        if existing_run_ids:
            run_id = existing_run_ids[0]

    # Initialize the agent
    agent = Agent(
        run_id=run_id,
        user_id=user,
        knowledge_base=knowledge_base,
        storage=storage,
        instructions=[
            "You are an expert PDF assistant. Answer questions based strictly on the provided PDF document.",
            "Be concise and accurate. If you don't know the answer, say so.",
        ],
        markdown=True,
        show_tool_calls=True,
        search_knowledge=True,
        read_chat_history=True,
    )

    # Conversation management
    if run_id:
        typer.echo(f"↻ Resuming conversation [ID: {run_id}]\n")
    else:
        run_id = agent.run_id
        typer.echo(f"★ New conversation [ID: {run_id}]\n")

    typer.echo("💬 PDF Assistant ready. Ask about the document or type '/exit' to quit.\n")
    
    # Conversation loop
    while True:
        question = typer.prompt("\nYour question")
        
        # Exit condition
        if question.lower() in ["/exit", "/quit", "/bye"]:
            typer.echo("\n✅ Conversation saved. Goodbye!")
            break
            
        # Process the question
        typer.echo("\n🤖 Assistant:")
        response = ""
        for chunk in agent.chat(question, stream=True):
            response += chunk
            typer.echo(chunk, nl=False)
        typer.echo("")

if __name__ == "__main__":
    app()