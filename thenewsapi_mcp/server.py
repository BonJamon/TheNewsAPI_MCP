import logging
from typing import Dict, Optional, Any, List
from enum import Enum
from pydantic import Field

from fastmcp import FastMCP
from thenewsapi_mcp.thenewsapi_client import TheNewsAPIClient, NewsCategory

logger = logging.getLogger(__name__)

def create_server(access_token: Optional[str]=None)->FastMCP:
    """
    Create TheNewsAPI MCP Server
    
    :return: FastMCP Server containing the tool calls
    :rtype: FastMCP[Any]
    """
    server = FastMCP(name="thenewsapi")
    thenewsapi_client = TheNewsAPIClient(access_token)

    @server.tool()
    def search(query: str, limit: int=1, categories: Optional[List[NewsCategory]]=None)-> Dict[str, Any]:
        """
        Search News Articles by Keywords. 
        - Use Categories only if the user explicetly mentions a topic like technology, sports, politics, etc. 
        
        Returns a dictionary with the search query, results, status, and
        additional metadata. If the query is empty or invalid, the status
        will be 'error' and an explanatory message is included.
        """
        logger.info("Tool: Searching TheNewsAPI for '%s' (categories: '%s', limit: '%d')", query, str(categories), limit)
        # Validate query
        if not query or not query.strip():
            logger.warning("Search tool called with empty query")
            return {
                "query": query,
                "results": [],
                "status": "error",
                "message": "Empty search query provided",
            }
        
        # Sanitize and validate limit
        validated_limit = limit
        if limit <= 0:
            validated_limit = 1
            logger.warning("Invalid limit %d; using default %d", limit, validated_limit)
        elif limit > 3:
            validated_limit = 3
            logger.warning("Limit %d capped to %d", limit, validated_limit)

        results = thenewsapi_client.search_news(query, categories=categories, limit=validated_limit)
        status = "success" if results else "no_results"
        response: Dict[str, Any] = {
            "query": query,
            "results": results,
            "status": status,
            "count": len(results),
        }

        if not results:
            response["message"] = (
                "No search results found. This could indicate connectivity issues, "
                "API errors, or simply no matching articles."
            )

        return response
    

    @server.tool()
    def get_article(uuid: str)-> Dict[str, Any]:
        """
        Get a News Article by uuid. 
        
        Returns a dictionary with the search uuid, result, status, and
        additional metadata. If the query is empty or invalid, the status
        will be 'error' and an explanatory message is included.
        """
        logger.info("Tool: Get article for '%s' ", uuid)
        # Validate query
        if not uuid or not uuid.strip():
            logger.warning("Search tool called with empty uuid")
            return {
                "uuid": uuid,
                "results": [],
                "status": "error",
                "message": "Empty search query provided",
            }
        

        result = thenewsapi_client.search_news_by_uuid(uuid)
        status = "success" if result else "no_results"
        response: Dict[str, Any] = {
            "uuid": uuid,
            "result": result,
            "status": status
        }

        if not result:
            response["message"] = (
                "No search results found. This could indicate connectivity issues, "
                "API errors, or simply no matching articles."
            )

        return response

    return server