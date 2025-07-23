import google.generativeai as genai
import logging
from typing import List, Dict, Any, Optional
import json
import datetime
import hashlib
from app.config import get_settings
from app.db_handler import DatabaseHandler
from app.cache import query_cache

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self):
        """Initialize the LLM handler with Gemini 2.5 and enhanced security"""
        settings = get_settings()

        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("LLM handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM handler: {e}")
            raise ValueError(f"Failed to initialize LLM: {e}")

        # Initialize a database handler to get schema
        self.db_handler = DatabaseHandler()
        self.settings = settings

    def _get_schema_str(self):
        schema = self.db_handler.get_schema()
        # Add a mapping for known table column corrections
        column_rename_map = {
            'sales': {
                'sale_date': 'date',
                'revenue': 'ad_sales',
                'quantity': 'units_sold',
                'product_id': 'item_id',
            },
            'total_sales': {
                'sale_date': 'date',
                'revenue': 'total_sales',
                'quantity': 'total_units_ordered',
                'product_id': 'item_id',
            },
            'eligibility': {
                'eligibility_datetime_utc': 'eligibility_datetime_utc',
                'item_id': 'item_id',
                'eligibility': 'eligibility',
                'message': 'message',
            }
        }
        schema_str = "\n".join(
            f"Table: {table}\nColumns: {', '.join(column_rename_map.get(table, {}).get(col['name'], col['name']) for col in cols)}"
            for table, cols in schema.items()
        )
        return schema_str

    def _get_dataset_date_info(self) -> str:
        """Get information about the date range in the dataset"""
        try:
            cursor = self.db_handler.connection.cursor()
            cursor.execute("SELECT MIN(date), MAX(date) FROM sales")
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                min_date, max_date = result
                return f"Dataset contains dates from {min_date} to {max_date}"
            else:
                return "Dataset date range: unknown"
        except Exception as e:
            logger.warning(f"Could not get dataset date info: {e}")
            return "Dataset date range: unknown"

    def _get_latest_date(self) -> str:
        """Get the latest date in the dataset"""
        try:
            cursor = self.db_handler.connection.cursor()
            cursor.execute("SELECT MAX(date) FROM sales")
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            else:
                return "2025-06-01"  # fallback
        except Exception as e:
            logger.warning(f"Could not get latest date: {e}")
            return "2025-06-01"  # fallback

    def _replace_relative_dates(self, sql_query: str) -> str:
        """Replace relative date functions with actual dataset dates"""
        import datetime
        import re

        try:
            # Get the latest date from the dataset
            latest_date = self._get_latest_date()
            latest_dt = datetime.datetime.strptime(latest_date, "%Y-%m-%d")

            # Replace various date patterns
            replacements = []

            # Pattern 1: date('now', '-X days') or DATE('now', '-X days')
            pattern1 = r"(?i)date\('now',\s*'-(\d+)\s+days?'\)"
            matches = re.finditer(pattern1, sql_query)
            for match in matches:
                days_back = int(match.group(1))
                target_date = latest_dt - datetime.timedelta(days=days_back)
                target_date_str = target_date.strftime("%Y-%m-%d")
                replacements.append((match.group(0), f"DATE('{target_date_str}')"))

            # Pattern 2: date('now') or DATE('now')
            pattern2 = r"(?i)date\('now'\)"
            matches = re.finditer(pattern2, sql_query)
            for match in matches:
                replacements.append((match.group(0), f"DATE('{latest_date}')"))

            # Pattern 3: BETWEEN Date('now', '-X days') AND Date('now')
            pattern3 = r"(?i)between\s+date\('now',\s*'-(\d+)\s+days?'\)\s+and\s+date\('now'\)"
            matches = re.finditer(pattern3, sql_query)
            for match in matches:
                days_back = int(match.group(1))
                start_date = latest_dt - datetime.timedelta(days=days_back)
                start_date_str = start_date.strftime("%Y-%m-%d")
                replacements.append((match.group(0), f"BETWEEN DATE('{start_date_str}') AND DATE('{latest_date}')"))

            # Apply all replacements
            for old_text, new_text in replacements:
                sql_query = sql_query.replace(old_text, new_text)
                logger.info(f"Replaced '{old_text}' with '{new_text}'")

            return sql_query

        except Exception as e:
            logger.warning(f"Failed to replace relative dates: {e}")
            return sql_query

    async def generate_sql(self, natural_query: str) -> str:
        """
        Generate SQL query from natural language query with caching
        """
        # Create cache context with schema hash for invalidation
        schema = self.db_handler.get_schema()
        schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
        cache_context = {"schema_hash": schema_hash, "type": "sql_generation"}

        # Check cache first
        cached_sql = query_cache.get(natural_query, cache_context)
        if cached_sql:
            logger.info(f"Using cached SQL for query: {natural_query[:50]}...")
            return cached_sql

        schema_str = self._get_schema_str()
        date_info = self._get_dataset_date_info()

        prompt = f"""
You are working with the following SQLite database schema:
{schema_str}

Dataset Date Information:
{date_info}

Convert the following natural language query to a SELECT SQL statement using the correct table and column names as shown above. For example, use 'date' instead of 'sale_date', 'ad_sales' instead of 'revenue', 'units_sold' instead of 'quantity', and 'item_id' instead of 'product_id' if appropriate. Always use the column names exactly as shown above.

IMPORTANT for date queries:
- The dataset contains dates from {date_info.split('to')[0].strip() if 'to' in date_info else 'unknown'} to {date_info.split('to')[1].strip() if 'to' in date_info else 'unknown'}
- For "last X days" queries, calculate from the LATEST date in the dataset, not current system date
- For "recent" queries, use the most recent dates available in the dataset
- Use DATE() function with YYYY-MM-DD format for all date comparisons

Natural language query:
\"{natural_query}\"

Return only the SQL query, no explanations or additional text. The query must be a SELECT statement.
"""
        try:
            logger.info(f"Generating SQL for query: {natural_query[:50]}...")
            response = self.model.generate_content(prompt)
            sql_query = response.text.strip()
            # Remove code block markers if present
            if sql_query.startswith('```'):
                sql_query = sql_query.strip('`')
                sql_query = sql_query.replace('sql', '', 1).strip()
            sql_query = sql_query.strip()
            logger.debug("LLM generated SQL:", sql_query)
            if not sql_query.lower().startswith('select'):
                raise ValueError("Generated query must be a SELECT statement")

            # Cache the result
            query_cache.set(natural_query, sql_query, cache_context)
            logger.info(f"Cached SQL query for: {natural_query[:50]}...")

            # Enhanced date replacement logic for dataset-relative dates
            sql_query = self._replace_relative_dates(sql_query)
            print("[DEBUG] Final SQL after patching:", sql_query)
            return sql_query
        except Exception as e:
            print(f"[ERROR] Exception in generate_sql: {e}")
            raise Exception(f"Failed to generate SQL: {str(e)}")

    async def generate_response(self, original_query: str, data: List[Dict[str, Any]], sql_query: str) -> str:
        if not data:
            return "No data found for your query."

        # Create cache key from query, data summary, and SQL
        data_summary = self._summarize_data(data)
        cache_key = f"{original_query}|{sql_query}|{data_summary}"
        cache_context = {"type": "response_generation"}

        # Check cache first
        cached_response = query_cache.get(cache_key, cache_context)
        if cached_response:
            logger.info(f"Using cached response for query: {original_query[:50]}...")
            return cached_response

        prompt = f"""
You are an e-commerce analytics assistant. Based on the following information, provide a clear and insightful response:

Original Query: "{original_query}"
SQL Query Used: {sql_query}
Data Summary: {data_summary}

Provide a natural language response that:
1. Directly answers the user's question
2. Includes relevant statistics and insights
3. Is written in a professional but conversational tone
4. Highlights any interesting patterns or trends
5. Suggests potential actions if applicable

Keep the response concise but informative (2-4 sentences).
"""
        try:
            logger.info(f"Generating response for query: {original_query[:50]}...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Cache the result
            query_cache.set(cache_key, response_text, cache_context)
            logger.info(f"Cached response for: {original_query[:50]}...")

            return response_text
        except Exception as e:
            logger.warning(f"Failed to generate response: {e}")
            return f"Based on the data, I found {len(data)} records. Here are the key insights: {self._format_data_insights(data)}"

    def _summarize_data(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return "No data available"
        summary = f"Found {len(data)} records. "
        if len(data) <= 5:
            summary += f"All records: {data}"
        else:
            summary += f"Sample records: {data[:3]}... (and {len(data)-3} more)"
        return summary

    def _format_data_insights(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return "No data available"
        insights = []
        insights.append(f"Total records: {len(data)}")
        if data and len(data) > 0:
            sample_record = data[0]
            numeric_columns = [col for col, val in sample_record.items() 
                             if isinstance(val, (int, float)) and col != 'id']
            if numeric_columns:
                for col in numeric_columns[:3]:
                    values = [record.get(col, 0) for record in data if record.get(col) is not None]
                    if values:
                        avg_val = sum(values) / len(values)
                        insights.append(f"Average {col}: {avg_val:.2f}")
        return "; ".join(insights)

    async def analyze_trends(self, data: List[Dict[str, Any]], time_column: str = None) -> str:
        if not data or len(data) < 2:
            return "Insufficient data for trend analysis."
        prompt = f"""
Analyze the following e-commerce data for trends and patterns:
{data[:10]}  # First 10 records for analysis

Focus on:
1. Temporal trends (if time data is available)
2. Performance patterns
3. Anomalies or outliers
4. Business insights

Provide a concise analysis (2-3 sentences).
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Unable to analyze trends at this time." 