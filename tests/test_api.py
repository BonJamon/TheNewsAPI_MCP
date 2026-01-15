from thenewsapi_mcp.thenewsapi_client import TheNewsAPIClient
from dotenv import load_dotenv
import os
import requests

load_dotenv()

access_token = os.getenv("THENEWSAPI_API_KEY")


client = TheNewsAPIClient(access_token)
results = client.search_news(query="Trump Greenland", limit=1)
print(results)
