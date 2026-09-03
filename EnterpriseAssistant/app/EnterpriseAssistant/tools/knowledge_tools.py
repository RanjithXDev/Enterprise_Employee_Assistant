from strands import tool
from services.knowledge_service import search_knowledge_base

@tool 
def search_company_knowledge(query: str ) -> str:
    """
    Search the Enterprise Employee Knowledge Base for
    company policies, procedures, guidelines, and other
    internal documentation.

    Use this tool when the user asks about:
    - HR policies
    - Leave policies
    - Company holidays
    - Employee policies
    - Benefits
    - IT policies
    - VPN troubleshooting
    - Laptop policies
    - Password policies
    - IT support guidelines
    """

    results = search_knowledge_base(query)

    if not results:
        return "No relevant company information was found in the Knowledge Base."

    formatted_results = []

    for result in results:
        text = result.get("content", {}).get("text", "")
        location = result.get("location", {})
        formatted_results.append(
            f"Source: {location}\n"
            f"Content:\n {text}"
        )

    return "\n\n----\n\n".join(formatted_results)