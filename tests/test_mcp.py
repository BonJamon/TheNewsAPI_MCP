from thenewsapi_mcp.server import create_server, NewsCategory
from dotenv import load_dotenv
import os
import pytest
import pytest_asyncio
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from langchain_core.tools import StructuredTool 
from pydantic import BaseModel
from typing import Literal
from langchain.agents import create_agent

load_dotenv()

access_token = os.getenv("THENEWSAPI_API_KEY")

mcp = create_server(access_token)

@pytest_asyncio.fixture
async def main_mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


"""
'''
Test number of tools
'''
@pytest.mark.asyncio
async def test_list_tools(main_mcp_client: Client[FastMCPTransport]):
    list_tools = await main_mcp_client.list_tools()

    assert len(list_tools) == 2

'''
Test search tool
'''
@pytest.mark.parametrize("query, limit, expected_query, expected_status, expected_count", 
                         [("OpenAI", 1, "OpenAI", "success", 1),
                          ("Greenland", 5, "Greenland", "success", 3)])
@pytest.mark.asyncio
async def test_search(query: str, limit: int, expected_query: str, 
                      expected_status: str, expected_count: int, 
                      main_mcp_client: Client[FastMCPTransport]):
    result = await main_mcp_client.call_tool(name="search", arguments={"query":query, "limit":limit})
    
    assert result.data["query"] == expected_query
    assert result.data["count"] == expected_count
    assert result.data["status"] == expected_status



'''
Test get article tool
'''
@pytest.mark.parametrize("uuid, expected_title, expected_status", 
                         [('3dd16916-8d7d-4848-bf5f-6c95d3d68b88', 'Trump Wants Greenland; Greenland Says NO!',"success")])
@pytest.mark.asyncio
async def test_get_article(uuid: str, expected_title: str, 
                      expected_status: str,  main_mcp_client: Client[FastMCPTransport]):
    result = await main_mcp_client.call_tool(name="get_article", arguments={"uuid":uuid})
    
    assert result.data["uuid"] == uuid
    assert result.data["result"]["title"] == expected_title
    assert result.data["status"] == expected_status
"""


'''
Test utility in agent
'''

async def load_langchain_tools(client, original_tools):
    '''
    Adapt FastMCP tools to LangChain tools
    '''
    tools = []
    for tool in original_tools:
        tool_name = tool.name
        async def _tool_runner(_tool_name = tool_name, **kwargs):
            return await client.call_tool(_tool_name, kwargs)

        tools.append(
            StructuredTool(
                name=tool.name,
                description=tool.description or "",
                args_schema=tool.inputSchema,
                coroutine=_tool_runner,
            )
        )
    return tools


@pytest.mark.parametrize("query, expected_answer", 
                         [('Trump proposed to buy Greenland', 'True'),
                          ('Trump died', 'False'),
                          ('Demonstrants have died in recent protests in Iran', 'True'),
                          ('Trump is secretly in love with Hilary Clinton', 'Unknown')])

#Problem: Inconsistent, probably because I am limiting the amount of news checked to 3 to save api usage
@pytest.mark.asyncio
async def test_mcp_in_agent(query:str, expected_answer:str, main_mcp_client: Client[FastMCPTransport]):
    async with main_mcp_client:
        tools = await main_mcp_client.list_tools()
        tools = await load_langchain_tools(main_mcp_client, tools)

        class Answer(BaseModel):
            answer: Literal["True", "False", "Unknown"]
            summary: str
            links: str

        system_prompt='''You are a fact-checking agent that verifies claims only using evidence from news articles via the thenewsapi MCP tools.
        Process:
        1.) Classify the claim (verifiable fact, interpretive/causal, predictive, or subjective/private/speculative).
        2.) Search for news articles that explicitly support or contradict the claim.
        
        Decision rules:
        - True: Reliable news articles clearly confirm the claim.
        - False: Reliable news articles clearly contradict the claim.
        - Unknown:
            - No relevant articles are found
            - Articles do not directly address the claim
            - Evidence is inconclusive
            - The claim is subjective, private, speculative, or not verifiable via news

        Important:
        - Absence of evidence ≠ evidence of falsity.
        - Do not infer motives, emotions, secrets, or intent beyond what articles explicitly state.
        
        Output:
        1.) Answer: [True, False, Unknown]
        2.) 1–3 sentence explanation
        3.) Article links used (or state none found)'''

        agent = create_agent(
            model="openai:gpt-4.1-mini",
            tools=tools,
            system_prompt=system_prompt,  # default tool-calling prompt
            response_format=Answer
        )

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]}
        )

        print(result["structured_response"])

        assert result["structured_response"].answer == expected_answer

        
        

