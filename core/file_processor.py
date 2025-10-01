import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class FileProcessor:
    """Utility class for processing JSON and CSV files"""

    @staticmethod
    def process_json(file_path: str) -> Dict[str, Any]:
        """Process JSON file and return structured data"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_size = os.path.getsize(file_path)

            return {
                "type": "json",
                "data": data,
                "summary": FileProcessor._generate_json_summary(data),
                "size": file_size,
            }
        except Exception as e:
            raise ValueError(f"Failed to process JSON file: {str(e)}")

    @staticmethod
    def process_csv(file_path: str) -> Dict[str, Any]:
        """Process CSV file and return structured data"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                raise ValueError("CSV file is empty")

            lines = content.split("\n")
            headers = FileProcessor._parse_csv_line(lines[0])

            rows = []
            for line in lines[1:]:
                if line.strip():
                    values = FileProcessor._parse_csv_line(line)
                    row = dict(zip(headers, values))
                    rows.append(row)

            file_size = os.path.getsize(file_path)

            return {
                "type": "csv",
                "data": {"headers": headers, "rows": rows, "totalRows": len(rows)},
                "summary": FileProcessor._generate_csv_summary(headers, rows),
                "size": file_size,
            }
        except Exception as e:
            raise ValueError(f"Failed to process CSV file: {str(e)}")

    @staticmethod
    def _parse_csv_line(line: str) -> List[str]:
        """Parse a CSV line handling quoted values"""
        result = []
        current = ""
        in_quotes = False
        i = 0

        while i < len(line):
            char = line[i]

            if char == '"' and (i == 0 or line[i - 1] == ","):
                in_quotes = True
            elif (
                char == '"' and in_quotes and (i == len(line) - 1 or line[i + 1] == ",")
            ):
                in_quotes = False
            elif char == "," and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char

            i += 1

        result.append(current.strip())
        return result

    @staticmethod
    def _generate_json_summary(data: Any) -> Dict[str, Any]:
        """Generate summary for JSON data"""
        if isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "firstItemKeys": (
                    list(data[0].keys()) if data and isinstance(data[0], dict) else []
                ),
                "dataTypes": FileProcessor._analyze_data_types(data),
            }
        elif isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys()),
                "dataTypes": FileProcessor._analyze_data_types([data]),
            }
        else:
            return {"type": type(data).__name__, "value": data}

    @staticmethod
    def _generate_csv_summary(headers: List[str], rows: List[Dict]) -> Dict[str, Any]:
        """Generate summary for CSV data"""
        return {
            "columnCount": len(headers),
            "rowCount": len(rows),
            "columns": headers,
            "sampleData": rows[:3],
            "columnTypes": FileProcessor._analyze_csv_column_types(headers, rows),
        }

    @staticmethod
    def _analyze_data_types(data: List[Any]) -> Dict[str, str]:
        """Analyze data types of object fields"""
        types = {}

        if not data:
            return types

        sample = data[0]
        if isinstance(sample, dict):
            for key in sample.keys():
                values = [
                    item[key] for item in data if key in item and item[key] is not None
                ]
                types[key] = FileProcessor._determine_column_type(values)

        return types

    @staticmethod
    def _analyze_csv_column_types(
        headers: List[str], rows: List[Dict]
    ) -> Dict[str, str]:
        """Analyze data types of CSV columns"""
        types = {}

        for header in headers:
            values = [row.get(header, "") for row in rows if row.get(header, "") != ""]
            types[header] = FileProcessor._determine_column_type(values)

        return types

    @staticmethod
    def _determine_column_type(values: List[Any]) -> str:
        """Determine the data type of a column"""
        if not values:
            return "empty"

        sample = values[: min(100, len(values))]

        # Check if all values are numbers
        try:
            all_numbers = all(
                isinstance(v, (int, float))
                or (
                    isinstance(v, str)
                    and v.replace(".", "", 1).replace("-", "", 1).isdigit()
                )
                for v in sample
            )
            if all_numbers:
                return "number"
        except:
            pass

        # Check if all values are booleans
        try:
            all_booleans = all(
                str(v).lower() in ["true", "false", "1", "0", "yes", "no"]
                for v in sample
            )
            if all_booleans:
                return "boolean"
        except:
            pass

        # Check if all values are dates
        try:
            all_dates = all(
                isinstance(v, str) and FileProcessor._is_date(v) for v in sample
            )
            if all_dates:
                return "date"
        except:
            pass

        return "string"

    @staticmethod
    def _is_date(value: str) -> bool:
        """Check if a string value is a date"""
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]
        for fmt in date_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except:
                continue
        return False

    @staticmethod
    def generate_context_prompt(file_data: Dict[str, Any]) -> str:
        """Generate context prompt for AI from file data"""
        if not file_data:
            return ""

        prompt = f"\n\nFile Data Context:\n"
        prompt += f"File Type: {file_data['type'].upper()}\n"
        prompt += f"File Size: {file_data['size'] / 1024:.2f} KB\n"

        if file_data["type"] == "csv":
            data = file_data["data"]
            headers = data["headers"]
            rows = data["rows"]
            total_rows = data["totalRows"]

            prompt += f"Columns ({len(headers)}): {', '.join(headers)}\n"
            prompt += f"Total Rows: {total_rows}\n"

            column_types = file_data["summary"]["columnTypes"]
            prompt += f"Column Types: {', '.join([f'{col}: {ctype}' for col, ctype in column_types.items()])}\n"

            if rows:
                prompt += f"\nSample Data (first 3 rows):\n"
                for idx, row in enumerate(rows[:3], 1):
                    prompt += f"Row {idx}: {json.dumps(row)}\n"

        elif file_data["type"] == "json":
            summary = file_data["summary"]
            if summary["type"] == "array":
                prompt += f"Array Length: {summary['length']}\n"
                if summary["firstItemKeys"]:
                    prompt += f"Object Keys: {', '.join(summary['firstItemKeys'])}\n"
            elif summary["type"] == "object":
                prompt += f"Object Keys: {', '.join(summary['keys'])}\n"

            data = file_data["data"]
            sample_data = data[:3] if isinstance(data, list) else data
            prompt += f"\nData Sample:\n{json.dumps(sample_data, indent=2)}\n"

        prompt += "\nYou can answer questions about this data, perform analysis, filter records, calculate statistics, or help with data insights."

        return prompt

    @staticmethod
    def query_data(file_data: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
        """Query file data based on search query"""
        if not file_data or not query:
            return None

        query_lower = query.lower()

        try:
            if file_data["type"] == "csv":
                return FileProcessor._query_csv_data(file_data["data"], query_lower)
            elif file_data["type"] == "json":
                return FileProcessor._query_json_data(file_data["data"], query_lower)
        except Exception as e:
            print(f"Error querying data: {e}")
            return None

        return None

    @staticmethod
    def _query_csv_data(csv_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Query CSV data"""
        headers = csv_data["headers"]
        rows = csv_data["rows"]

        # Simple keyword search across all columns
        matching_rows = [
            row
            for row in rows
            if any(query in str(value).lower() for value in row.values())
        ]

        return {
            "matchingRows": matching_rows[:10],  # Limit to 10 results
            "totalMatches": len(matching_rows),
            "searchedColumns": headers,
        }

    @staticmethod
    def _query_json_data(json_data: Any, query: str) -> Dict[str, Any]:
        """Query JSON data"""
        data_array = json_data if isinstance(json_data, list) else [json_data]

        matching_items = [
            item for item in data_array if query in json.dumps(item).lower()
        ]

        return {
            "matchingItems": matching_items[:10],  # Limit to 10 results
            "totalMatches": len(matching_items),
        }
