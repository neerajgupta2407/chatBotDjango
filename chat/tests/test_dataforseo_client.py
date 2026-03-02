"""Test cases for DataForSEO API client"""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from chat.services.dataforseo_client import DataForSEOClient, get_dataforseo_client


class DataForSEOClientInitTestCase(TestCase):
    """Test cases for DataForSEOClient initialization and configuration"""

    @override_settings(
        DATAFORSEO_USERNAME="test@example.com", DATAFORSEO_PASSWORD="pass123"
    )
    def test_init_from_settings(self):
        """Should initialize credentials from Django settings"""
        client = DataForSEOClient()

        self.assertEqual("test@example.com", client.username)
        self.assertEqual("pass123", client.password)
        self.assertTrue(client.is_configured)

    def test_init_with_explicit_credentials(self):
        """Should use explicitly provided credentials"""
        client = DataForSEOClient(username="user@test.com", password="secret")

        self.assertEqual("user@test.com", client.username)
        self.assertEqual("secret", client.password)
        self.assertTrue(client.is_configured)

    @override_settings(DATAFORSEO_USERNAME=None, DATAFORSEO_PASSWORD=None)
    def test_not_configured_without_credentials(self):
        """Should report not configured when credentials are missing"""
        client = DataForSEOClient()

        self.assertFalse(client.is_configured)

    @override_settings(DATAFORSEO_USERNAME="user@test.com", DATAFORSEO_PASSWORD=None)
    def test_not_configured_without_password(self):
        """Should report not configured when password is missing"""
        client = DataForSEOClient()

        self.assertFalse(client.is_configured)


class DataForSEOClientBuildPayloadTestCase(TestCase):
    """Test cases for payload building"""

    def setUp(self):
        self.client = DataForSEOClient(username="test", password="test")

    def test_build_serp_payload_with_defaults(self):
        """Should build SERP payload with default location and language"""
        payload = self.client._build_payload(
            "serp_google_organic_live", {"keyword": "python tutorial"}
        )

        self.assertEqual(1, len(payload))
        self.assertEqual("python tutorial", payload[0]["keyword"])
        self.assertEqual("United States", payload[0]["location_name"])
        self.assertEqual("English", payload[0]["language_name"])
        self.assertEqual("desktop", payload[0]["device"])
        self.assertEqual(10, payload[0]["depth"])

    def test_build_serp_payload_with_custom_options(self):
        """Should build SERP payload with custom options"""
        payload = self.client._build_payload(
            "serp_google_organic_live",
            {
                "keyword": "test",
                "location_name": "United Kingdom",
                "device": "mobile",
                "depth": 50,
            },
        )

        self.assertEqual("United Kingdom", payload[0]["location_name"])
        self.assertEqual("mobile", payload[0]["device"])
        self.assertEqual(50, payload[0]["depth"])

    def test_build_search_volume_payload(self):
        """Should build search volume payload correctly"""
        payload = self.client._build_payload(
            "kw_google_ads_search_volume",
            {"keywords": ["python", "javascript"]},
        )

        self.assertEqual(["python", "javascript"], payload[0]["keywords"])
        self.assertEqual("United States", payload[0]["location_name"])

    def test_build_keywords_for_site_payload(self):
        """Should build keywords for site payload correctly"""
        payload = self.client._build_payload(
            "kw_google_ads_keywords_for_site", {"target": "example.com"}
        )

        self.assertEqual("example.com", payload[0]["target"])

    def test_build_backlinks_summary_payload(self):
        """Should build backlinks summary payload correctly"""
        payload = self.client._build_payload(
            "backlinks_summary", {"target": "example.com"}
        )

        self.assertEqual({"target": "example.com"}, payload[0])

    def test_build_referring_domains_payload_with_default_limit(self):
        """Should build referring domains payload with default limit"""
        payload = self.client._build_payload(
            "backlinks_referring_domains", {"target": "example.com"}
        )

        self.assertEqual("example.com", payload[0]["target"])
        self.assertEqual(10, payload[0]["limit"])

    def test_build_referring_domains_payload_with_custom_limit(self):
        """Should build referring domains payload with custom limit"""
        payload = self.client._build_payload(
            "backlinks_referring_domains", {"target": "example.com", "limit": 25}
        )

        self.assertEqual(25, payload[0]["limit"])

    def test_build_onpage_payload(self):
        """Should build on-page payload correctly"""
        payload = self.client._build_payload(
            "onpage_instant_pages", {"url": "https://example.com/page"}
        )

        self.assertEqual({"url": "https://example.com/page"}, payload[0])

    def test_build_keyword_ideas_payload(self):
        """Should build keyword ideas payload correctly"""
        payload = self.client._build_payload(
            "labs_google_keyword_ideas",
            {"keywords": ["seo", "marketing"], "limit": 20},
        )

        self.assertEqual(["seo", "marketing"], payload[0]["keywords"])
        self.assertEqual(20, payload[0]["limit"])

    def test_build_domain_rank_payload(self):
        """Should build domain rank payload correctly"""
        payload = self.client._build_payload(
            "labs_google_domain_rank_overview", {"target": "example.com"}
        )

        self.assertEqual("example.com", payload[0]["target"])
        self.assertEqual("United States", payload[0]["location_name"])

    def test_build_unknown_tool_payload(self):
        """Should pass args through for unknown tool names"""
        args = {"custom_field": "value"}
        payload = self.client._build_payload("unknown_tool", args)

        self.assertEqual([args], payload)


class DataForSEOClientExtractResultTestCase(TestCase):
    """Test cases for result extraction methods"""

    def setUp(self):
        self.client = DataForSEOClient(username="test", password="test")

    def test_extract_result_no_results(self):
        """Should handle empty results"""
        result = self.client._extract_result("serp_google_organic_live", {"result": []})

        self.assertEqual({"message": "No results found"}, result)

    def test_extract_result_none_results(self):
        """Should handle None results"""
        result = self.client._extract_result(
            "serp_google_organic_live", {"result": None}
        )

        self.assertEqual({"message": "No results found"}, result)

    def test_extract_serp_results(self):
        """Should extract organic SERP results correctly"""
        task = {
            "result": [
                {
                    "keyword": "python tutorial",
                    "se_results_count": 1000000,
                    "items": [
                        {
                            "type": "organic",
                            "rank_group": 1,
                            "title": "Python.org",
                            "url": "https://python.org",
                            "domain": "python.org",
                            "description": "Official Python site",
                        },
                        {
                            "type": "people_also_ask",
                            "rank_group": 2,
                        },
                        {
                            "type": "organic",
                            "rank_group": 3,
                            "title": "W3Schools Python",
                            "url": "https://w3schools.com/python",
                            "domain": "w3schools.com",
                            "description": "Python Tutorial",
                        },
                    ],
                }
            ]
        }

        result = self.client._extract_result("serp_google_organic_live", task)

        self.assertEqual("python tutorial", result["keyword"])
        self.assertEqual(1000000, result["total_results"])
        self.assertEqual(2, len(result["organic_results"]))
        self.assertEqual("Python.org", result["organic_results"][0]["title"])
        self.assertEqual(1, result["organic_results"][0]["position"])

    def test_extract_serp_filters_non_organic(self):
        """Should only include organic results, not ads or other types"""
        task = {
            "result": [
                {
                    "keyword": "test",
                    "se_results_count": 100,
                    "items": [
                        {"type": "paid", "rank_group": 1, "title": "Ad"},
                        {"type": "organic", "rank_group": 2, "title": "Organic Result"},
                        {
                            "type": "featured_snippet",
                            "rank_group": 3,
                            "title": "Featured",
                        },
                    ],
                }
            ]
        }

        result = self.client._extract_result("serp_google_organic_live", task)

        self.assertEqual(1, len(result["organic_results"]))
        self.assertEqual("Organic Result", result["organic_results"][0]["title"])

    def test_extract_search_volume(self):
        """Should extract search volume data correctly"""
        task = {
            "result": [
                {
                    "keyword": "python",
                    "search_volume": 450000,
                    "competition": 0.15,
                    "competition_level": "LOW",
                    "cpc": 2.50,
                    "monthly_searches": [
                        {"month": 1, "search_volume": 400000},
                        {"month": 2, "search_volume": 420000},
                    ],
                }
            ]
        }

        result = self.client._extract_result("kw_google_ads_search_volume", task)

        self.assertEqual(1, len(result["keywords"]))
        self.assertEqual("python", result["keywords"][0]["keyword"])
        self.assertEqual(450000, result["keywords"][0]["search_volume"])
        self.assertEqual("LOW", result["keywords"][0]["competition_level"])

    def test_extract_backlinks_summary(self):
        """Should extract backlinks summary correctly"""
        task = {
            "result": [
                {
                    "target": "example.com",
                    "external_links_count": 50000,
                    "referring_domains": 1500,
                    "referring_main_domains": 1200,
                    "rank": 450,
                    "broken_backlinks": 100,
                    "referring_ips": 800,
                    "referring_subnets": 600,
                }
            ]
        }

        result = self.client._extract_result("backlinks_summary", task)

        self.assertEqual("example.com", result["target"])
        self.assertEqual(50000, result["total_backlinks"])
        self.assertEqual(1500, result["referring_domains"])
        self.assertEqual(450, result["rank"])

    def test_extract_referring_domains(self):
        """Should extract referring domains correctly"""
        task = {
            "result": [
                {
                    "domain": "blog.example.com",
                    "rank": 300,
                    "backlinks": 50,
                    "first_seen": "2024-01-01",
                    "last_seen": "2024-06-01",
                },
                {
                    "domain": "news.example.com",
                    "rank": 500,
                    "backlinks": 30,
                    "first_seen": "2024-03-01",
                    "last_seen": "2024-06-01",
                },
            ]
        }

        result = self.client._extract_result("backlinks_referring_domains", task)

        self.assertEqual(2, len(result["referring_domains"]))
        self.assertEqual("blog.example.com", result["referring_domains"][0]["domain"])

    def test_extract_onpage_results(self):
        """Should extract on-page SEO data correctly"""
        task = {
            "result": [
                {
                    "items": [
                        {
                            "url": "https://example.com",
                            "status_code": 200,
                            "meta": {
                                "title": "Example Page",
                                "description": "An example page",
                                "htags": {"h1": ["Main Heading"]},
                            },
                            "content": {"plain_text_word_count": 1500},
                            "onpage_score": 85.5,
                            "page_timing": {
                                "time_to_interactive": 1.2,
                                "dom_complete": 2.5,
                                "connection_time": 0.1,
                            },
                            "checks": {
                                "has_title": True,
                                "has_description": True,
                                "is_https": True,
                                "has_render_blocking_resources": False,
                            },
                        }
                    ]
                }
            ]
        }

        result = self.client._extract_result("onpage_instant_pages", task)

        self.assertEqual("https://example.com", result["url"])
        self.assertEqual(200, result["status_code"])
        self.assertEqual("Example Page", result["title"])
        self.assertEqual(1500, result["word_count"])
        self.assertEqual(85.5, result["onpage_score"])
        self.assertIn("has_title", result["checks"])
        self.assertNotIn("has_render_blocking_resources", result["checks"])

    def test_extract_onpage_no_items(self):
        """Should handle on-page results with no items"""
        task = {"result": [{"items": []}]}

        result = self.client._extract_result("onpage_instant_pages", task)

        self.assertEqual({"message": "No page data found"}, result)

    def test_extract_keyword_ideas(self):
        """Should extract keyword ideas correctly"""
        task = {
            "result": [
                {
                    "keyword_data": {
                        "keyword": "python tutorial",
                        "keyword_info": {
                            "search_volume": 300000,
                            "competition": 0.2,
                            "cpc": 3.0,
                        },
                    },
                    "keyword_properties": {"keyword_difficulty": 45},
                }
            ]
        }

        result = self.client._extract_result("labs_google_keyword_ideas", task)

        self.assertEqual(1, len(result["keyword_ideas"]))
        self.assertEqual("python tutorial", result["keyword_ideas"][0]["keyword"])
        self.assertEqual(300000, result["keyword_ideas"][0]["search_volume"])
        self.assertEqual(45, result["keyword_ideas"][0]["keyword_difficulty"])

    def test_extract_domain_rank_single(self):
        """Should extract single domain rank as flat dict"""
        task = {
            "result": [
                {
                    "target": "example.com",
                    "metrics": {
                        "organic": {
                            "etv": 150000,
                            "count": 25000,
                            "estimated_paid_traffic_cost": 50000,
                            "is_new": 100,
                            "is_up": 500,
                            "is_down": 200,
                            "is_lost": 50,
                        }
                    },
                }
            ]
        }

        result = self.client._extract_result("labs_google_domain_rank_overview", task)

        self.assertEqual("example.com", result["target"])
        self.assertEqual(150000, result["organic_traffic"])
        self.assertEqual(25000, result["organic_keywords"])

    def test_extract_unknown_tool_type(self):
        """Should return raw count for unknown tool types"""
        task = {"result": [{"data": "something"}, {"data": "else"}]}

        result = self.client._extract_result("unknown_tool", task)

        self.assertEqual({"raw_result_count": 2}, result)


class DataForSEOClientExecuteToolTestCase(TestCase):
    """Test cases for execute_tool method"""

    def setUp(self):
        self.client = DataForSEOClient(username="test", password="test")

    def test_execute_unknown_tool(self):
        """Should return error for unknown tool name"""
        result = self.client.execute_tool("nonexistent_tool", {})

        self.assertIn("error", result)
        self.assertIn("Unknown tool", result["error"])

    @patch.object(DataForSEOClient, "_post")
    def test_execute_tool_success(self, mock_post):
        """Should execute tool and return extracted results"""
        mock_post.return_value = {
            "result": [
                {
                    "keyword": "test",
                    "se_results_count": 100,
                    "items": [
                        {
                            "type": "organic",
                            "rank_group": 1,
                            "title": "Test Result",
                            "url": "https://test.com",
                            "domain": "test.com",
                            "description": "A test",
                        }
                    ],
                }
            ]
        }

        result = self.client.execute_tool(
            "serp_google_organic_live", {"keyword": "test"}
        )

        self.assertEqual("test", result["keyword"])
        self.assertEqual(1, len(result["organic_results"]))
        mock_post.assert_called_once_with(
            "serp/google/organic/live/advanced",
            [
                {
                    "keyword": "test",
                    "location_name": "United States",
                    "language_name": "English",
                    "device": "desktop",
                    "depth": 10,
                }
            ],
        )

    @patch.object(DataForSEOClient, "_post")
    def test_execute_tool_api_error(self, mock_post):
        """Should return error when API call fails"""
        mock_post.side_effect = ValueError("DataForSEO API error: Bad request")

        result = self.client.execute_tool(
            "serp_google_organic_live", {"keyword": "test"}
        )

        self.assertIn("error", result)
        self.assertIn("Bad request", result["error"])

    @patch.object(DataForSEOClient, "_post")
    def test_execute_tool_network_error(self, mock_post):
        """Should return error on network failure"""
        mock_post.side_effect = Exception("Connection timeout")

        result = self.client.execute_tool(
            "backlinks_summary", {"target": "example.com"}
        )

        self.assertIn("error", result)
        self.assertIn("Connection timeout", result["error"])


class DataForSEOClientPostTestCase(TestCase):
    """Test cases for the _post method"""

    def setUp(self):
        self.client = DataForSEOClient(username="test", password="test")

    @patch("chat.services.dataforseo_client.httpx.Client")
    def test_post_success(self, mock_httpx_client_class):
        """Should return task on successful API response"""
        mock_http = Mock()
        mock_httpx_client_class.return_value = mock_http

        mock_response = Mock()
        mock_response.json.return_value = {
            "status_code": 20000,
            "tasks": [
                {
                    "status_code": 20000,
                    "result": [{"data": "test"}],
                }
            ],
        }
        mock_http.post.return_value = mock_response

        task = self.client._post("test/endpoint", [{"key": "value"}])

        self.assertEqual(20000, task["status_code"])
        self.assertEqual([{"data": "test"}], task["result"])

    @patch("chat.services.dataforseo_client.httpx.Client")
    def test_post_api_level_error(self, mock_httpx_client_class):
        """Should raise ValueError on API-level error"""
        mock_http = Mock()
        mock_httpx_client_class.return_value = mock_http

        mock_response = Mock()
        mock_response.json.return_value = {
            "status_code": 40000,
            "status_message": "Authentication failed",
        }
        mock_http.post.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            self.client._post("test/endpoint", [{}])

        self.assertIn("Authentication failed", str(ctx.exception))

    @patch("chat.services.dataforseo_client.httpx.Client")
    def test_post_task_level_error(self, mock_httpx_client_class):
        """Should raise ValueError on task-level error"""
        mock_http = Mock()
        mock_httpx_client_class.return_value = mock_http

        mock_response = Mock()
        mock_response.json.return_value = {
            "status_code": 20000,
            "tasks": [
                {
                    "status_code": 40501,
                    "status_message": "Invalid keyword",
                }
            ],
        }
        mock_http.post.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            self.client._post("test/endpoint", [{}])

        self.assertIn("Invalid keyword", str(ctx.exception))

    @patch("chat.services.dataforseo_client.httpx.Client")
    def test_post_no_tasks(self, mock_httpx_client_class):
        """Should return error dict when no tasks returned"""
        mock_http = Mock()
        mock_httpx_client_class.return_value = mock_http

        mock_response = Mock()
        mock_response.json.return_value = {
            "status_code": 20000,
            "tasks": [],
        }
        mock_http.post.return_value = mock_response

        task = self.client._post("test/endpoint", [{}])

        self.assertEqual({"error": "No tasks returned"}, task)


class GetDataForSEOClientTestCase(TestCase):
    """Test cases for get_dataforseo_client singleton"""

    @override_settings(DATAFORSEO_USERNAME=None, DATAFORSEO_PASSWORD=None)
    def test_returns_none_when_not_configured(self):
        """Should return None when credentials are not set"""
        # Reset singleton
        import chat.services.dataforseo_client as module

        module._client_instance = None

        result = get_dataforseo_client()

        self.assertIsNone(result)

    @override_settings(DATAFORSEO_USERNAME="user@test.com", DATAFORSEO_PASSWORD="pass")
    def test_returns_client_when_configured(self):
        """Should return DataForSEOClient when credentials are set"""
        # Reset singleton
        import chat.services.dataforseo_client as module

        module._client_instance = None

        result = get_dataforseo_client()

        self.assertIsNotNone(result)
        self.assertIsInstance(result, DataForSEOClient)

    @override_settings(DATAFORSEO_USERNAME="user@test.com", DATAFORSEO_PASSWORD="pass")
    def test_returns_same_instance(self):
        """Should return the same singleton instance"""
        # Reset singleton
        import chat.services.dataforseo_client as module

        module._client_instance = None

        first = get_dataforseo_client()
        second = get_dataforseo_client()

        self.assertIs(first, second)

    def tearDown(self):
        """Reset singleton after each test"""
        import chat.services.dataforseo_client as module

        module._client_instance = None
