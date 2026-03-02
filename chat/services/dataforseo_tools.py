"""
DataForSEO tool definitions for AI function calling.

Tools are grouped by module (SERP, KEYWORDS_DATA, BACKLINKS, ONPAGE, DATAFORSEO_LABS).
Each tool maps to a specific DataForSEO v3 API endpoint.
"""

from typing import Dict, List, Optional

# Module → tool definitions mapping
TOOL_DEFINITIONS = {
    "SERP": [
        {
            "name": "serp_google_organic_live",
            "description": (
                "Search Google and get live organic search results (SERP) for a keyword. "
                "Returns top-ranking pages, their titles, URLs, descriptions, and positions. "
                "Use this when the user asks about search rankings, top results, or SERP analysis."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The search keyword or phrase to look up",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location for search results (e.g., 'United States', 'United Kingdom'). Defaults to 'United States'.",
                    },
                    "language_name": {
                        "type": "string",
                        "description": "Language for search results (e.g., 'English'). Defaults to 'English'.",
                    },
                    "device": {
                        "type": "string",
                        "enum": ["desktop", "mobile"],
                        "description": "Device type for search results. Defaults to 'desktop'.",
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Number of results to return (10, 20, 50, 100). Defaults to 10.",
                    },
                },
                "required": ["keyword"],
            },
        },
    ],
    "KEYWORDS_DATA": [
        {
            "name": "kw_google_ads_search_volume",
            "description": (
                "Get Google Ads search volume data for one or more keywords. "
                "Returns monthly search volume, competition level, CPC, and historical data. "
                "Use this when the user asks about keyword search volume, popularity, or traffic potential."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keywords to get search volume for (max 700)",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location for search data (e.g., 'United States'). Defaults to 'United States'.",
                    },
                    "language_name": {
                        "type": "string",
                        "description": "Language for search data (e.g., 'English'). Defaults to 'English'.",
                    },
                },
                "required": ["keywords"],
            },
        },
        {
            "name": "kw_google_ads_keywords_for_site",
            "description": (
                "Get keyword suggestions for a specific website/domain from Google Ads. "
                "Returns relevant keywords, their search volumes, and competition data. "
                "Use this when the user asks about keywords for a website or domain."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target domain or URL (e.g., 'example.com')",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location for keyword data (e.g., 'United States'). Defaults to 'United States'.",
                    },
                    "language_name": {
                        "type": "string",
                        "description": "Language for keyword data (e.g., 'English'). Defaults to 'English'.",
                    },
                },
                "required": ["target"],
            },
        },
    ],
    "BACKLINKS": [
        {
            "name": "backlinks_summary",
            "description": (
                "Get a backlink profile summary for a domain or URL. "
                "Returns total backlinks count, referring domains, domain rank, and other link metrics. "
                "Use this when the user asks about a site's backlink profile, authority, or link metrics."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target domain or URL to analyze (e.g., 'example.com')",
                    },
                },
                "required": ["target"],
            },
        },
        {
            "name": "backlinks_referring_domains",
            "description": (
                "Get a list of domains that link to a target domain or URL. "
                "Returns referring domains with their rank, backlink count, and first/last seen dates. "
                "Use this when the user asks about who links to a website or referring domains."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target domain or URL to analyze (e.g., 'example.com')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of referring domains to return. Defaults to 10.",
                    },
                },
                "required": ["target"],
            },
        },
    ],
    "ONPAGE": [
        {
            "name": "onpage_instant_pages",
            "description": (
                "Perform an instant on-page SEO analysis of a specific URL. "
                "Returns page title, meta description, headings, word count, page speed metrics, "
                "and SEO issues found. Use this when the user asks about on-page SEO for a specific page."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to analyze (e.g., 'https://example.com/page')",
                    },
                },
                "required": ["url"],
            },
        },
    ],
    "DATAFORSEO_LABS": [
        {
            "name": "labs_google_keyword_ideas",
            "description": (
                "Get keyword ideas and suggestions based on seed keywords using DataForSEO Labs. "
                "Returns related keywords with search volume, CPC, competition, and keyword difficulty. "
                "Use this when the user asks for keyword ideas, suggestions, or related keywords."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Seed keywords to generate ideas from",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location for keyword data (e.g., 'United States'). Defaults to 'United States'.",
                    },
                    "language_name": {
                        "type": "string",
                        "description": "Language for keyword data (e.g., 'English'). Defaults to 'English'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of keyword ideas to return. Defaults to 10.",
                    },
                },
                "required": ["keywords"],
            },
        },
        {
            "name": "labs_google_domain_rank_overview",
            "description": (
                "Get a domain ranking overview from DataForSEO Labs. "
                "Returns organic and paid traffic estimates, total keywords, domain rank, and top keywords. "
                "Use this when the user asks about a domain's overall SEO performance or ranking."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target domain to analyze (e.g., 'example.com')",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Location for ranking data (e.g., 'United States'). Defaults to 'United States'.",
                    },
                    "language_name": {
                        "type": "string",
                        "description": "Language for ranking data (e.g., 'English'). Defaults to 'English'.",
                    },
                },
                "required": ["target"],
            },
        },
    ],
}

# Map tool names to their module for quick lookup
TOOL_TO_MODULE: Dict[str, str] = {}
for module, tools in TOOL_DEFINITIONS.items():
    for tool in tools:
        TOOL_TO_MODULE[tool["name"]] = module

# Map tool names to their API endpoint paths
TOOL_ENDPOINTS: Dict[str, str] = {
    "serp_google_organic_live": "serp/google/organic/live/advanced",
    "kw_google_ads_search_volume": "keywords_data/google_ads/search_volume/live",
    "kw_google_ads_keywords_for_site": "keywords_data/google_ads/keywords_for_site/live",
    "backlinks_summary": "backlinks/summary/live",
    "backlinks_referring_domains": "backlinks/referring_domains/live",
    "onpage_instant_pages": "on_page/instant_pages",
    "labs_google_keyword_ideas": "dataforseo_labs/google/keyword_ideas/live",
    "labs_google_domain_rank_overview": "dataforseo_labs/google/domain_rank_overview/live",
}


def get_tools(enabled_modules: Optional[List[str]] = None) -> List[Dict]:
    """Get tool definitions for the specified modules.

    Args:
        enabled_modules: List of module names to enable (e.g., ["SERP", "KEYWORDS_DATA"]).
                        If None, returns all tools.

    Returns:
        List of tool definition dicts ready for AI provider consumption.
    """
    if enabled_modules is None:
        enabled_modules = list(TOOL_DEFINITIONS.keys())

    tools = []
    for module in enabled_modules:
        module_upper = module.strip().upper()
        if module_upper in TOOL_DEFINITIONS:
            tools.extend(TOOL_DEFINITIONS[module_upper])
    return tools
