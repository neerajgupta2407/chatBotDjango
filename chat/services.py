import json
import math
from typing import Any, Dict, List, Optional

from llms.file_processor import FileProcessor


class ChatService:
    """Service layer for chat message processing and context building"""

    MAX_TOTAL_TOKENS = 6000
    MAX_USER_MESSAGE_TOKENS = 3000
    MAX_JSON_DATA_TOKENS = 2000
    MAX_HISTORY_TOKENS = 1500

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """Rough estimation: 1 token ≈ 4 characters"""
        return math.ceil(len(text) / 4)

    @staticmethod
    def truncate_text(text: str, max_tokens: int, preserve_ending: bool = False) -> str:
        """Truncate text while preserving meaning"""
        estimated_tokens = ChatService.estimate_token_count(text)
        if estimated_tokens <= max_tokens:
            return text

        max_chars = max_tokens * 4
        if preserve_ending:
            return "..." + text[-(max_chars - 3) :]
        else:
            return text[: max_chars - 3] + "..."

    @staticmethod
    def convert_array_to_csv(
        data_array: List[Dict], array_name: str = "data"
    ) -> Optional[str]:
        """Convert array of objects to CSV format"""
        if not data_array or not isinstance(data_array, list) or len(data_array) == 0:
            return None

        # Check if first element is an object
        if not isinstance(data_array[0], dict):
            return None

        # Get all columns from the first object
        all_columns = list(data_array[0].keys())

        # Create CSV header
        csv = ",".join(all_columns) + "\n"

        # Add data rows
        for item in data_array:
            row = []
            for col in all_columns:
                value = item.get(col)
                # Handle string values that might contain commas
                if isinstance(value, str) and "," in value:
                    row.append(f'"{value}"')
                else:
                    row.append(str(value) if value is not None else "0")
            csv += ",".join(row) + "\n"

        return csv

    @staticmethod
    def process_json_data_to_csv(data: Dict) -> tuple:
        """Recursively find and convert arrays in jsonData to CSV format"""
        csv_data = {}
        processed_data = json.loads(json.dumps(data))  # Deep clone

        def traverse(obj, path=""):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                if isinstance(value, list):
                    csv = ChatService.convert_array_to_csv(value, key)
                    if csv:
                        csv_data[current_path] = {
                            "csv": csv,
                            "originalLength": len(value),
                            "name": key,
                        }
                        obj[key] = f"[See CSV data for {key} below]"
                elif isinstance(value, dict):
                    traverse(value, current_path)

        traverse(processed_data)
        return processed_data, csv_data

    @staticmethod
    def build_context_prompt(
        user_message: str,
        session_config: Dict[str, Any],
        conversation_history: List[Dict],
        file_data: Optional[Dict] = None,
    ) -> str:
        """Build context prompt with comprehensive token management"""
        page_context = session_config.get("pageContext", {})
        custom_instructions = session_config.get("customInstructions", "")
        json_data = session_config.get("jsonData", {})
        page_data = session_config.get("pageData", {})

        # Truncate user message if too long
        truncated_user_message = ChatService.truncate_text(
            user_message, ChatService.MAX_USER_MESSAGE_TOKENS, preserve_ending=True
        )

        # Build base context
        base_context = f"""You are a helpful assistant embedded in a website to answer questions about the current page and help users.

Page Information:
- URL: {page_context.get('url') or page_data.get('url') or 'Not provided'}
- Title: {page_context.get('title') or page_data.get('title') or 'Not provided'}
- Content Summary: {page_context.get('content') or page_context.get('description') or page_data.get('pageContent') or 'Not provided'}
- Hostname: {page_data.get('hostname') or 'Not provided'}
- Page Language: {page_data.get('language') or 'Not provided'}

{f'Special Instructions: {custom_instructions}' if custom_instructions else ''}"""

        # Handle JSON data with dynamic CSV conversion
        json_data_section = ""
        if json_data:
            processed_data, csv_data = ChatService.process_json_data_to_csv(json_data)

            if csv_data:
                csv_sections = ""
                for path, data in csv_data.items():
                    csv_sections += f"\n## {data['name']} ({data['originalLength']} records):\n{data['csv']}\n"

                optimized_json_string = json.dumps(processed_data, indent=2)
                truncated_json_string = ChatService.truncate_text(
                    optimized_json_string, ChatService.MAX_JSON_DATA_TOKENS
                )

                json_data_section = f"""Available Data{' (truncated)' if '...' in truncated_json_string else ''}:

=== CSV DATA ===
{csv_sections}

=== ADDITIONAL CONTEXT ===
{truncated_json_string}

You have access to structured data in CSV format above, plus additional context. You can analyze this data, compare records, calculate totals, identify trends, and provide insights based on the metrics."""
            else:
                json_string = json.dumps(json_data, indent=2)
                truncated_json_string = ChatService.truncate_text(
                    json_string, ChatService.MAX_JSON_DATA_TOKENS
                )

                json_data_section = f"""Available JSON Data{' (truncated)' if '...' in truncated_json_string else ''}:
{truncated_json_string}

You have access to structured data. You can analyze this data and answer questions about it."""

        # Handle file data
        file_data_section = ""
        if file_data:
            file_data_section = FileProcessor.generate_context_prompt(file_data)

        # Build conversation history with smart truncation
        history_section = ""
        if conversation_history:
            history_text = ""
            current_tokens = 0

            # Add messages from most recent backwards until we hit token limit
            for msg in reversed(conversation_history):
                msg_text = f"{msg['role']}: {msg['content']}\n"
                msg_tokens = ChatService.estimate_token_count(msg_text)

                if current_tokens + msg_tokens > ChatService.MAX_HISTORY_TOKENS:
                    break

                history_text = msg_text + history_text
                current_tokens += msg_tokens

            if history_text:
                history_section = f"Previous conversation:\n{history_text}"

        # Final assembly
        context_prompt = base_context

        if json_data_section:
            context_prompt += f"\n\n{json_data_section}"

        if file_data_section:
            context_prompt += f"\n\n{file_data_section}"

        if history_section:
            context_prompt += f"\n\n{history_section}"

        context_prompt += f"\nCurrent user question: {truncated_user_message}"

        # Add warning if user message was truncated
        if truncated_user_message != user_message:
            context_prompt += f"\n\n[Note: User message was truncated due to length. Original length: {len(user_message)} characters]"

        context_prompt += f"""\n\nPlease provide a helpful, accurate response based on the page context{', the JSON data provided' if json_data else ''}, conversation history{', and the uploaded file data' if file_data else ''}.

{f'When discussing the JSON data, be specific about metrics, campaigns, and performance indicators. You can compare campaigns, calculate totals, identify trends, and provide insights based on the data.' if json_data else ''} Keep responses concise but informative."""

        return context_prompt
