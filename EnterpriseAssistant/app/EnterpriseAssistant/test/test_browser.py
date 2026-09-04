from strands import Agent
from strands_tools.browser import AgentCoreBrowser
from model.load import load_model

browser_tool = AgentCoreBrowser(
    region="ap-south-1",
    identifier="EnterpriseAssistantBrowser-09gCURlBMD",
)

agent = Agent(
    model=load_model(),
    tools=[browser_tool.browser],
)

response = agent(
    "Use the browser to open https://grootan.com "
    "and tell me the page title and main heading."
)

print(response)