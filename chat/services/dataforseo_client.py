"""
DataForSEO REST API client.

Makes HTTP calls to https://api.dataforseo.com/v3/ using HTTP Basic Auth.
Each method maps to a specific API endpoint and returns concise, filtered results.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings

from .dataforseo_tools import TOOL_ENDPOINTS

logger = logging.getLogger(__name__)

BASE_URL = "https://api.dataforseo.com/v3/"


class DataForSEOClient:
    """REST client for DataForSEO v3 API."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.username = username or settings.DATAFORSEO_USERNAME
        self.password = password or settings.DATAFORSEO_PASSWORD
        self._http_client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    def _get_client(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=BASE_URL,
                auth=(self.username, self.password),
                timeout=30.0,
            )
        return self._http_client

    def _post(self, endpoint: str, payload: List[Dict]) -> Dict:
        """Make a POST request to DataForSEO API."""
        client = self._get_client()
        logger.info(f"DataForSEO API call: POST {endpoint}")

        response = client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status_code") != 20000:
            error_msg = data.get("status_message", "Unknown API error")
            logger.error(f"DataForSEO API error: {error_msg}")
            raise ValueError(f"DataForSEO API error: {error_msg}")

        tasks = data.get("tasks", [])
        if not tasks:
            return {"error": "No tasks returned"}

        task = tasks[0]
        if task.get("status_code") != 20000:
            error_msg = task.get("status_message", "Task error")
            logger.error(f"DataForSEO task error: {error_msg}")
            raise ValueError(f"DataForSEO task error: {error_msg}")

        return task

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute a DataForSEO tool by name.

        Maps tool names to API endpoints and extracts concise results.

        Args:
            tool_name: Name of the tool to execute (e.g., 'serp_google_organic_live')
            arguments: Tool arguments from the AI model

        Returns:
            Filtered result dict suitable for sending back to the AI.
        """
        endpoint = TOOL_ENDPOINTS.get(tool_name)
        if not endpoint:
            return {"error": f"Unknown tool: {tool_name}"}

        logger.info(f"Executing DataForSEO tool: {tool_name} with args: {arguments}")

        # Build the task payload based on tool name
        payload = self._build_payload(tool_name, arguments)

        try:
            task = self._post(endpoint, payload)
            result = self._extract_result(tool_name, task)
            logger.info(f"DataForSEO tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"DataForSEO tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def _build_payload(self, tool_name: str, args: Dict) -> List[Dict]:
        """Build API payload from tool arguments."""
        if tool_name == "serp_google_organic_live":
            return [
                {
                    "keyword": args["keyword"],
                    "location_name": args.get("location_name", "United States"),
                    "language_name": args.get("language_name", "English"),
                    "device": args.get("device", "desktop"),
                    "depth": args.get("depth", 10),
                }
            ]

        elif tool_name == "kw_google_ads_search_volume":
            return [
                {
                    "keywords": args["keywords"],
                    "location_name": args.get("location_name", "United States"),
                    "language_name": args.get("language_name", "English"),
                }
            ]

        elif tool_name == "kw_google_ads_keywords_for_site":
            return [
                {
                    "target": args["target"],
                    "location_name": args.get("location_name", "United States"),
                    "language_name": args.get("language_name", "English"),
                }
            ]

        elif tool_name == "backlinks_summary":
            return [{"target": args["target"]}]

        elif tool_name == "backlinks_referring_domains":
            payload = {"target": args["target"]}
            if args.get("limit"):
                payload["limit"] = args["limit"]
            else:
                payload["limit"] = 10
            return [payload]

        elif tool_name == "onpage_instant_pages":
            return [{"url": args["url"]}]

        elif tool_name == "labs_google_keyword_ideas":
            payload = {
                "keywords": args["keywords"],
                "location_name": args.get("location_name", "United States"),
                "language_name": args.get("language_name", "English"),
            }
            if args.get("limit"):
                payload["limit"] = args["limit"]
            else:
                payload["limit"] = 10
            return [payload]

        elif tool_name == "labs_google_domain_rank_overview":
            return [
                {
                    "target": args["target"],
                    "location_name": args.get("location_name", "United States"),
                    "language_name": args.get("language_name", "English"),
                }
            ]

        return [args]

    def _extract_result(self, tool_name: str, task: Dict) -> Dict:
        """Extract concise results from raw API response."""
        results = task.get("result") or []
        if not results:
            return {"message": "No results found"}

        if tool_name == "serp_google_organic_live":
            return self._extract_serp(results[0])
        elif tool_name == "kw_google_ads_search_volume":
            return self._extract_search_volume(results)
        elif tool_name == "kw_google_ads_keywords_for_site":
            return self._extract_keywords_for_site(results)
        elif tool_name == "backlinks_summary":
            return self._extract_backlinks_summary(results[0])
        elif tool_name == "backlinks_referring_domains":
            return self._extract_referring_domains(results)
        elif tool_name == "onpage_instant_pages":
            return self._extract_onpage(results[0])
        elif tool_name == "labs_google_keyword_ideas":
            return self._extract_keyword_ideas(results)
        elif tool_name == "labs_google_domain_rank_overview":
            return self._extract_domain_rank(results)

        return {"raw_result_count": len(results)}

    def _extract_serp(self, result: Dict) -> Dict:
        """Extract organic SERP results."""
        items = result.get("items") or []
        organic_results = []
        for item in items:
            if item.get("type") == "organic":
                organic_results.append(
                    {
                        "position": item.get("rank_group"),
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "domain": item.get("domain"),
                        "description": item.get("description"),
                    }
                )

        return {
            "keyword": result.get("keyword"),
            "total_results": result.get("se_results_count"),
            "organic_results": organic_results[:20],
        }

    def _extract_search_volume(self, results: List[Dict]) -> Dict:
        """Extract keyword search volume data."""
        keywords = []
        for result in results:
            keywords.append(
                {
                    "keyword": result.get("keyword"),
                    "search_volume": result.get("search_volume"),
                    "competition": result.get("competition"),
                    "competition_level": result.get("competition_level"),
                    "cpc": result.get("cpc"),
                    "monthly_searches": result.get("monthly_searches", [])[:6],
                }
            )
        return {"keywords": keywords}

    def _extract_keywords_for_site(self, results: List[Dict]) -> Dict:
        """Extract keywords for site data."""
        keywords = []
        for result in results[:20]:
            keywords.append(
                {
                    "keyword": result.get("keyword"),
                    "search_volume": result.get("search_volume"),
                    "competition": result.get("competition"),
                    "competition_level": result.get("competition_level"),
                    "cpc": result.get("cpc"),
                }
            )
        return {"keywords": keywords}

    def _extract_backlinks_summary(self, result: Dict) -> Dict:
        """Extract backlinks summary."""
        return {
            "target": result.get("target"),
            "total_backlinks": result.get("external_links_count"),
            "referring_domains": result.get("referring_domains"),
            "referring_main_domains": result.get("referring_main_domains"),
            "rank": result.get("rank"),
            "broken_backlinks": result.get("broken_backlinks"),
            "referring_ips": result.get("referring_ips"),
            "referring_subnets": result.get("referring_subnets"),
        }

    def _extract_referring_domains(self, results: List[Dict]) -> Dict:
        """Extract referring domains data."""
        domains = []
        for result in results[:20]:
            domains.append(
                {
                    "domain": result.get("domain"),
                    "rank": result.get("rank"),
                    "backlinks": result.get("backlinks"),
                    "first_seen": result.get("first_seen"),
                    "last_seen": result.get("last_seen"),
                }
            )
        return {"referring_domains": domains}

    def _extract_onpage(self, result: Dict) -> Dict:
        """Extract on-page SEO data."""
        items = result.get("items") or []
        if not items:
            return {"message": "No page data found"}

        page = items[0]
        meta = page.get("meta", {})
        page_timing = page.get("page_timing", {})
        onpage_score = page.get("onpage_score")
        checks = page.get("checks", {})

        return {
            "url": page.get("url"),
            "status_code": page.get("status_code"),
            "title": meta.get("title"),
            "description": meta.get("description"),
            "h1": meta.get("htags", {}).get("h1", []),
            "word_count": page.get("content", {}).get("plain_text_word_count"),
            "onpage_score": onpage_score,
            "page_timing": {
                "time_to_interactive": page_timing.get("time_to_interactive"),
                "dom_complete": page_timing.get("dom_complete"),
                "connection_time": page_timing.get("connection_time"),
            },
            "checks": {k: v for k, v in (checks or {}).items() if v is True},
        }

    def _extract_keyword_ideas(self, results: List[Dict]) -> Dict:
        """Extract keyword ideas from Labs."""
        ideas = []
        for result in results[:20]:
            kw_data = result.get("keyword_data") or result
            keyword_info = kw_data.get("keyword_info", {})
            ideas.append(
                {
                    "keyword": kw_data.get("keyword"),
                    "search_volume": keyword_info.get("search_volume"),
                    "competition": keyword_info.get("competition"),
                    "cpc": keyword_info.get("cpc"),
                    "keyword_difficulty": result.get("keyword_properties", {}).get(
                        "keyword_difficulty"
                    ),
                }
            )
        return {"keyword_ideas": ideas}

    def _extract_domain_rank(self, results: List[Dict]) -> Dict:
        """Extract domain rank overview."""
        metrics_list = []
        for result in results:
            metrics = result.get("metrics", {}).get("organic", {})
            metrics_list.append(
                {
                    "target": result.get("target"),
                    "organic_traffic": metrics.get("etv"),
                    "organic_keywords": metrics.get("count"),
                    "organic_cost": metrics.get("estimated_paid_traffic_cost"),
                    "is_new": metrics.get("is_new"),
                    "is_up": metrics.get("is_up"),
                    "is_down": metrics.get("is_down"),
                    "is_lost": metrics.get("is_lost"),
                }
            )

        if len(metrics_list) == 1:
            return metrics_list[0]
        return {"domains": metrics_list}


# Singleton instance (lazy init)
_client_instance = None


def get_dataforseo_client() -> Optional[DataForSEOClient]:
    """Get the DataForSEO client singleton. Returns None if not configured."""
    global _client_instance
    if _client_instance is None:
        client = DataForSEOClient()
        if client.is_configured:
            _client_instance = client
        else:
            return None
    return _client_instance
