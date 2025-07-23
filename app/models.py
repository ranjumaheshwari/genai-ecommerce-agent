"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import re

class QueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=1000,
        description="Natural language query about e-commerce data"
    )
    include_visualization: bool = Field(
        default=False,
        description="Whether to generate a visualization for the query"
    )
    
    @validator('query')
    def validate_query(cls, v):
        # Remove extra whitespace
        v = v.strip()
        
        # Check for potentially dangerous SQL keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
            'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION', '--', ';'
        ]
        
        query_upper = v.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(
                    f"Query contains potentially dangerous keyword: {keyword}. "
                    "Only SELECT queries are allowed."
                )
        
        # Basic validation for meaningful content
        if len(v.split()) < 2:
            raise ValueError("Query must contain at least 2 words")
        
        return v

class QueryResponse(BaseModel):
    """Response model for query results"""
    response: str = Field(..., description="Natural language response to the query")
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Raw data returned from the database"
    )
    visualization: Optional[str] = Field(
        default=None, 
        description="Base64 encoded visualization image"
    )
    sql_query: Optional[str] = Field(
        default=None, 
        description="Generated SQL query"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="Query execution time in seconds"
    )
    record_count: Optional[int] = Field(
        default=None,
        description="Number of records returned"
    )

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: Optional[str] = Field(default=None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    database: bool = Field(..., description="Database connection status")
    llm: bool = Field(..., description="LLM service status")
    timestamp: str = Field(..., description="Health check timestamp")

class SchemaResponse(BaseModel):
    """Database schema response model"""
    schema: Dict[str, List[Dict[str, Any]]] = Field(
        ..., 
        description="Database schema information"
    )
    table_count: int = Field(..., description="Number of tables")
    
class SampleDataResponse(BaseModel):
    """Sample data response model"""
    sample_data: Dict[str, List[Dict[str, Any]]] = Field(
        ..., 
        description="Sample data from database tables"
    )
    tables: List[str] = Field(..., description="List of table names")

class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value")

def validate_sql_query(sql: str) -> bool:
    """
    Validate that a SQL query is safe to execute
    
    Args:
        sql: SQL query string
        
    Returns:
        bool: True if query is safe, False otherwise
        
    Raises:
        ValueError: If query contains dangerous operations
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty")
    
    sql_upper = sql.upper().strip()
    
    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed")
    
    # Check for dangerous keywords
    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bEXEC\b',
        r'\bEXECUTE\b', r'--', r';.*SELECT', r'UNION.*SELECT'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            raise ValueError(f"SQL query contains dangerous pattern: {pattern}")
    
    # Check for multiple statements (basic check)
    if sql.count(';') > 1 or (sql.count(';') == 1 and not sql.strip().endswith(';')):
        raise ValueError("Multiple SQL statements are not allowed")
    
    return True
