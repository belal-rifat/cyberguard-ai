import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def search_web(query: str, max_results: int = 3) -> str:
    """
    Searches the web for the given query and returns a combined
    summary of the top results, formatted for use as LLM context.
    """
    response = client.search(query=query, max_results=max_results)

    formatted_results = []
    for result in response.get("results", []):
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")
        formatted_results.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")

    return "\n---\n".join(formatted_results)


if __name__ == "__main__":
    result = search_web("latest phishing attack trends 2026")
    print(result)
