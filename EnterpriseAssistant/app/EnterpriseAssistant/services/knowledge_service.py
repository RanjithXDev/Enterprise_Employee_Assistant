import boto3


KNOWLEDGE_BASE_ID = "7UDOWAFZE3"

_bedrock_agent_runtime = None


def _get_bedrock_agent_runtime():
    global _bedrock_agent_runtime

    if _bedrock_agent_runtime is None:
        _bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime",
            region_name="ap-south-1",
        )

    return _bedrock_agent_runtime


def search_knowledge_base(
    query: str,
    number_of_results: int = 5,
):
    """
    Retrieve relevant information from the Enterprise Employee
    Knowledge Base.
    """

    bedrock_agent_runtime = _get_bedrock_agent_runtime()

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": number_of_results,
            }
        },
        retrievalQuery={
            "text": query,
        },
    )

    return response.get("retrievalResults", [])