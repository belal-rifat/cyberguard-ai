import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.agents import create_agent
from langchain_core.tools import tool

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tools.search_tool import search_web  # noqa: E402

load_dotenv()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "faiss_index")

SYSTEM_PROMPT = """You are CyberGuard AI, a security advisory assistant for a
Security Operations Center (SOC) analyst.

You help analysts understand suspicious emails, logs, or alerts by:
1. Checking the internal knowledge base (retrieve_security_knowledge tool) for
   known attack techniques (MITRE ATT&CK style information).
2. Searching the web (search_current_threats tool) when the user mentions
   something recent, a specific CVE, or something not in the knowledge base.
3. Combining both sources into a clear, structured advisory.

Your final answer MUST start with exactly one line in this format
(no extra text before it):
SEVERITY: <CRITICAL|HIGH|MEDIUM|LOW>

Then a blank line, then the advisory structured with these sections:
- What this looks like (classification)
- Why it is dangerous
- Recommended next steps

Be concise and practical, like a senior security analyst writing a quick brief.
"""


def _load_retriever():
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vectorstore = FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})


retriever = _load_retriever()


@tool
def retrieve_security_knowledge(query: str) -> str:
    """Retrieves relevant cybersecurity knowledge (attack techniques,
    indicators, and mitigations) from the internal knowledge base."""
    docs = retriever.invoke(query)
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


@tool
def search_current_threats(query: str) -> str:
    """Searches the web for current/recent cybersecurity threat information,
    such as new CVEs, ongoing campaigns, or recent attack trends."""
    return search_web(query)


def build_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    tools = [retrieve_security_knowledge, search_current_threats]
    agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
    return agent


if __name__ == "__main__":
    agent = build_agent()
    user_query = (
        "I received an email saying my account will be blocked unless I "
        "verify it by clicking a link. Is this dangerous?"
    )
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    final_message = result["messages"][-1].content
    print(final_message)
