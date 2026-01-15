import requests
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--log-level", default="WARNING")
args = parser.parse_args()

logging.basicConfig(
    level=args.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

class NewsCategory(str, Enum):
    general = "general"
    science = "science"
    sports = "sports"
    business = "business"
    health = "health"
    entertainment = "entertainment"
    tech = "tech"
    politics = "politics"
    food = "food"
    travel = "travel"

#working_domains = ["nytimes.com", "bbc.com", "apnews.com"]
#not_working_domains = ["theguardian.com","reuters.com"]
class TheNewsAPIClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.domains = ["nytimes.com", "bbc.com", "apnews.com"] 
        self.languages = ["en"]

    def search_news(self, query, categories: Optional[List[NewsCategory]]=None, limit: int=1):
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []

        trimmed_query = query.strip()
        if len(trimmed_query) > 300:
            logger.warning(
                "Search query too long (%d chars), truncating to 100",
                len(trimmed_query),
            )
            trimmed_query = trimmed_query[:100]

        
        if limit <= 0:
            logger.warning("Invalid limit %d provided, using default 1", limit)
            limit = 1
        elif limit > 3:
            logger.warning("Limit %d exceeds maximum, capping at 3", limit)
            limit = 3

        api_url = 'https://api.thenewsapi.com/v1/news/all'
        params = {
            "api_token": self.access_token,
            "search": trimmed_query,
            "limit": limit,
            "domains": self.domains,
            "language": self.languages
        }
        if categories:
            params["categories"]= categories

        try:
            logger.debug("Making search request to %s with params %s", api_url, params)
            response = requests.get(api_url,
                                params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_info = data["error"]
                logger.error(
                    "TheNewsAPI API error: %s - %s",
                    error_info.get("code", "unknown"),
                    error_info.get("info", "No details"),
                )
                return []

            if "warnings" in data:
                for warning_type, warning_body in data["warnings"].items():
                    logger.warning("TheNewsAPI API warning (%s): %s", warning_type, warning_body)

            search_results = data.get("data", [])
            logger.info(
                "Search for '%s' returned %d results",
                trimmed_query,
                len(search_results),
            )

            results: List[Dict[str, Any]] = []
            for item in search_results:
                title = item.get("title")
                if not title:
                    logger.warning("Search result missing title: %s", item)
                    continue

                results.append(
                    {
                        "title": title,
                        "description": item.get("description", ""),
                        "snippet": item.get("snippet", ""),
                        "uuid" : item.get("uuid", 0),
                        "published_at": item.get("published_at", ""),
                        "url": item.get("url", ""),
                        "source" : item.get("source", 0),
                    }
                )

            return results

        except requests.exceptions.Timeout as exc:
            logger.error("Search request timed out for query '%s': %s", trimmed_query, exc)
            return []
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error when searching for '%s': %s", trimmed_query, exc)
            return []
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error when searching for '%s': %s", trimmed_query, exc)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Request error when searching for '%s': %s", trimmed_query, exc)
            return []
        except ValueError as exc:
            logger.error("JSON decode error when searching for '%s': %s", trimmed_query, exc)
            return []
        except Exception as exc:  # pragma: no cover - unexpected safeguard
            logger.error("Unexpected error searching TheNewsAPI for '%s': %s", trimmed_query, exc)
            return []
        

    def search_news_by_uuid(self, uuid):
        api_url = "https://api.thenewsapi.com/v1/news/uuid/"+str(uuid)
        params = {
            "api_token": self.access_token
        }

        try:
            logger.debug("Making search request to %s with params %s", api_url, params)
            response = requests.get(api_url,
                                params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_info = data["error"]
                logger.error(
                    "TheNewsAPI API error: %s - %s",
                    error_info.get("code", "unknown"),
                    error_info.get("info", "No details"),
                )
                return []

            if "warnings" in data:
                for warning_type, warning_body in data["warnings"].items():
                    logger.warning("TheNewsAPI API warning (%s): %s", warning_type, warning_body)

            keys = ["uuid", "title", "snippet", "description", "url", "source"]
            result = {key: data[key] for key in keys}
            return result

        except requests.exceptions.Timeout as exc:
            logger.error("Search request timed out for uuid '%s': %s", uuid, exc)
            return []
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error when searching for '%s': %s", uuid, exc)
            return []
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error when searching for '%s': %s", uuid, exc)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Request error when searching for '%s': %s", uuid, exc)
            return []
        except ValueError as exc:
            logger.error("JSON decode error when searching for '%s': %s", uuid, exc)
            return []
        except Exception as exc:  # pragma: no cover - unexpected safeguard
            logger.error("Unexpected error searching TheNewsAPI for '%s': %s", uuid, exc)
            return []

    def search_similar_news_by_uuid(self, uuid, limit: int=1, categories: Optional[List[NewsCategory]]=None):
        if limit <= 0:
            logger.warning("Invalid limit %d provided, using default 1", limit)
            limit = 1
        elif limit > 3:
            logger.warning("Limit %d exceeds maximum, capping at 3", limit)
            limit = 3

        api_url = "https://api.thenewsapi.com/v1/news/similar/"+str(uuid)
        params = {
            "api_token": self.access_token,
            "limit": limit,
            "categories": categories,
            "domains": self.domains,
            "language": self.languages
        }

        try:
            logger.debug("Making search request to %s with params %s", api_url, params)
            response = requests.get(api_url,
                                params=params)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_info = data["error"]
                logger.error(
                    "TheNewsAPI API error: %s - %s",
                    error_info.get("code", "unknown"),
                    error_info.get("info", "No details"),
                )
                return []

            if "warnings" in data:
                for warning_type, warning_body in data["warnings"].items():
                    logger.warning("TheNewsAPI API warning (%s): %s", warning_type, warning_body)

            search_results = data.get("data", [])

            results: List[Dict[str, Any]] = []
            for item in search_results:
                title = item.get("title")
                if not title:
                    logger.warning("Search result missing title: %s", item)
                    continue

                results.append(
                    {
                        "title": title,
                        "description": item.get("description", ""),
                        "snippet": item.get("snippet", ""),
                        "uuid" : item.get("uuid", 0),
                        "source" : item.get("source", 0),
                        "published_at": item.get("published_at", ""),
                        "url": item.get("url", ""),
                    }
                )

            return results

        except requests.exceptions.Timeout as exc:
            logger.error("Search request timed out for uuid '%s': %s", uuid, exc)
            return []
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error when searching for '%s': %s", uuid, exc)
            return []
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error when searching for '%s': %s", uuid, exc)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Request error when searching for '%s': %s", uuid, exc)
            return []
        except ValueError as exc:
            logger.error("JSON decode error when searching for '%s': %s", uuid, exc)
            return []
        except Exception as exc:  # pragma: no cover - unexpected safeguard
            logger.error("Unexpected error searching TheNewsAPI for '%s': %s", uuid, exc)
            return []







