"""Test cases for DataForSEO tool definitions"""

from django.test import TestCase

from chat.services.dataforseo_tools import (
    TOOL_DEFINITIONS,
    TOOL_ENDPOINTS,
    TOOL_TO_MODULE,
    get_tools,
)


class DataForSEOToolDefinitionsTestCase(TestCase):
    """Test cases for tool definitions structure and consistency"""

    def test_all_modules_defined(self):
        """Should have all expected modules"""
        expected_modules = {
            "SERP",
            "KEYWORDS_DATA",
            "BACKLINKS",
            "ONPAGE",
            "DATAFORSEO_LABS",
        }

        self.assertEqual(expected_modules, set(TOOL_DEFINITIONS.keys()))

    def test_total_tool_count(self):
        """Should have 8 tools total across all modules"""
        total = sum(len(tools) for tools in TOOL_DEFINITIONS.values())

        self.assertEqual(8, total)

    def test_serp_module_tools(self):
        """Should have correct tools in SERP module"""
        tool_names = [t["name"] for t in TOOL_DEFINITIONS["SERP"]]

        self.assertEqual(["serp_google_organic_live"], tool_names)

    def test_keywords_data_module_tools(self):
        """Should have correct tools in KEYWORDS_DATA module"""
        tool_names = [t["name"] for t in TOOL_DEFINITIONS["KEYWORDS_DATA"]]

        self.assertEqual(
            ["kw_google_ads_search_volume", "kw_google_ads_keywords_for_site"],
            tool_names,
        )

    def test_backlinks_module_tools(self):
        """Should have correct tools in BACKLINKS module"""
        tool_names = [t["name"] for t in TOOL_DEFINITIONS["BACKLINKS"]]

        self.assertEqual(
            ["backlinks_summary", "backlinks_referring_domains"], tool_names
        )

    def test_onpage_module_tools(self):
        """Should have correct tools in ONPAGE module"""
        tool_names = [t["name"] for t in TOOL_DEFINITIONS["ONPAGE"]]

        self.assertEqual(["onpage_instant_pages"], tool_names)

    def test_dataforseo_labs_module_tools(self):
        """Should have correct tools in DATAFORSEO_LABS module"""
        tool_names = [t["name"] for t in TOOL_DEFINITIONS["DATAFORSEO_LABS"]]

        self.assertEqual(
            ["labs_google_keyword_ideas", "labs_google_domain_rank_overview"],
            tool_names,
        )

    def test_every_tool_has_required_fields(self):
        """Should have name, description, and input_schema for every tool"""
        for module, tools in TOOL_DEFINITIONS.items():
            for tool in tools:
                self.assertIn("name", tool, f"Missing 'name' in {module}")
                self.assertIn("description", tool, f"Missing 'description' in {module}")
                self.assertIn(
                    "input_schema", tool, f"Missing 'input_schema' in {module}"
                )

    def test_every_input_schema_is_valid_json_schema(self):
        """Should have valid JSON Schema structure for each tool's input_schema"""
        for module, tools in TOOL_DEFINITIONS.items():
            for tool in tools:
                schema = tool["input_schema"]
                self.assertEqual(
                    "object",
                    schema["type"],
                    f"{tool['name']} schema should be object type",
                )
                self.assertIn(
                    "properties",
                    schema,
                    f"{tool['name']} schema missing properties",
                )
                self.assertIn(
                    "required",
                    schema,
                    f"{tool['name']} schema missing required",
                )

    def test_every_tool_has_endpoint_mapping(self):
        """Should have an endpoint mapping for every defined tool"""
        for module, tools in TOOL_DEFINITIONS.items():
            for tool in tools:
                self.assertIn(
                    tool["name"],
                    TOOL_ENDPOINTS,
                    f"Missing endpoint for tool: {tool['name']}",
                )

    def test_tool_to_module_mapping(self):
        """Should correctly map every tool name to its module"""
        self.assertEqual("SERP", TOOL_TO_MODULE["serp_google_organic_live"])
        self.assertEqual("KEYWORDS_DATA", TOOL_TO_MODULE["kw_google_ads_search_volume"])
        self.assertEqual("BACKLINKS", TOOL_TO_MODULE["backlinks_summary"])
        self.assertEqual("ONPAGE", TOOL_TO_MODULE["onpage_instant_pages"])
        self.assertEqual("DATAFORSEO_LABS", TOOL_TO_MODULE["labs_google_keyword_ideas"])

    def test_endpoint_paths_are_valid(self):
        """Should have reasonable endpoint paths for all tools"""
        for name, endpoint in TOOL_ENDPOINTS.items():
            self.assertNotIn(
                "https://", endpoint, f"{name} endpoint should be relative"
            )
            self.assertNotIn(
                "/v3/", endpoint, f"{name} endpoint should not include base path"
            )


class GetToolsTestCase(TestCase):
    """Test cases for get_tools() function"""

    def test_get_tools_all_modules(self):
        """Should return all tools when no modules specified"""
        tools = get_tools()

        self.assertEqual(8, len(tools))

    def test_get_tools_none_returns_all(self):
        """Should return all tools when None passed"""
        tools = get_tools(None)

        self.assertEqual(8, len(tools))

    def test_get_tools_single_module(self):
        """Should return only tools from specified module"""
        tools = get_tools(["SERP"])

        self.assertEqual(1, len(tools))
        self.assertEqual("serp_google_organic_live", tools[0]["name"])

    def test_get_tools_multiple_modules(self):
        """Should return tools from multiple specified modules"""
        tools = get_tools(["SERP", "BACKLINKS"])

        self.assertEqual(3, len(tools))
        names = {t["name"] for t in tools}
        self.assertIn("serp_google_organic_live", names)
        self.assertIn("backlinks_summary", names)
        self.assertIn("backlinks_referring_domains", names)

    def test_get_tools_case_insensitive(self):
        """Should handle case-insensitive module names"""
        tools = get_tools(["serp", "backlinks"])

        self.assertEqual(3, len(tools))

    def test_get_tools_with_whitespace(self):
        """Should handle module names with whitespace"""
        tools = get_tools([" SERP ", " BACKLINKS "])

        self.assertEqual(3, len(tools))

    def test_get_tools_unknown_module_ignored(self):
        """Should ignore unknown module names"""
        tools = get_tools(["SERP", "NONEXISTENT_MODULE"])

        self.assertEqual(1, len(tools))
        self.assertEqual("serp_google_organic_live", tools[0]["name"])

    def test_get_tools_empty_list_returns_nothing(self):
        """Should return empty list for empty modules list"""
        tools = get_tools([])

        self.assertEqual(0, len(tools))

    def test_get_tools_returns_complete_tool_definitions(self):
        """Should return tool dicts with all required fields"""
        tools = get_tools(["SERP"])

        tool = tools[0]
        self.assertIn("name", tool)
        self.assertIn("description", tool)
        self.assertIn("input_schema", tool)
        self.assertEqual("serp_google_organic_live", tool["name"])
        self.assertIn("keyword", tool["input_schema"]["properties"])
