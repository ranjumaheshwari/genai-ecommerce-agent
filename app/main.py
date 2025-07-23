from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.exceptions import RequestValidationError
import asyncio
import time
import logging
import csv
import io
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn

# Use absolute imports for module execution
from app.config import get_settings, validate_environment
from app.models import (
    QueryRequest, QueryResponse, ErrorResponse, HealthResponse,
    SchemaResponse, SampleDataResponse, validate_sql_query
)
from app.llm_handler import LLMHandler
from app.db_handler import DatabaseHandler
from app.visualizer import DataVisualizer
from app.cache import query_cache

# Validate environment on startup
if not validate_environment():
    raise RuntimeError("Environment validation failed. Please check your configuration.")

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GenAI E-commerce Agent",
    description="An intelligent e-commerce analytics agent powered by Gemini 2.5",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware with more secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            error_type="validation_error",
            details=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception for {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            error_type="server_error",
            details="An unexpected error occurred" if not settings.debug else str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# Initialize handlers with error handling
try:
    llm_handler = LLMHandler()
    logger.info("✅ LLM Handler initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize LLM Handler: {e}")
    raise

try:
    db_handler = DatabaseHandler()
    logger.info("✅ Database Handler initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Database Handler: {e}")
    raise

try:
    visualizer = DataVisualizer()
    logger.info("✅ Data Visualizer initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Data Visualizer: {e}")
    raise

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "GenAI E-commerce Agent API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint"""
    db_status = db_handler.is_connected()

    # Test LLM connection
    llm_status = True
    try:
        # Simple test to verify LLM is accessible
        await llm_handler.model.generate_content_async("test")
    except:
        llm_status = False

    return HealthResponse(
        status="healthy" if db_status and llm_status else "degraded",
        database=db_status,
        llm=llm_status,
        timestamp=datetime.now().isoformat()
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process natural language queries about e-commerce data with enhanced security and error handling
    """
    start_time = time.time()

    try:
        logger.info(f"Processing query: {request.query[:100]}...")

        # Generate SQL query using LLM
        sql_query = await llm_handler.generate_sql(request.query)
        logger.info(f"Generated SQL: {sql_query}")

        # Validate SQL query for security
        validate_sql_query(sql_query)

        # Execute SQL query
        data = db_handler.execute_query(sql_query)
        logger.info(f"Query returned {len(data) if data else 0} records")

        # Generate natural language response
        response = await llm_handler.generate_response(request.query, data, sql_query)

        # Generate visualization if requested
        visualization = None
        if request.include_visualization and data:
            try:
                visualization = visualizer.create_visualization(data, request.query)
                logger.info("Visualization generated successfully")
            except Exception as viz_error:
                logger.warning(f"Visualization generation failed: {viz_error}")
                # Continue without visualization rather than failing the entire request

        execution_time = time.time() - start_time

        return QueryResponse(
            response=response,
            data=data,
            visualization=visualization,
            sql_query=sql_query,
            execution_time=round(execution_time, 3),
            record_count=len(data) if data else 0
        )

    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other errors
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Query processing failed. Please try again or contact support."
        )

@app.post("/query-stream")
async def process_query_stream(request: QueryRequest):
    """
    Process natural language queries with streaming response for better UX
    """
    try:
        logger.info(f"Processing streaming query: {request.query[:100]}...")

        # Generate SQL query using LLM
        sql_query = await llm_handler.generate_sql(request.query)

        # Validate SQL query for security
        validate_sql_query(sql_query)

        # Execute SQL query
        data = db_handler.execute_query(sql_query)

        # Generate natural language response
        response = await llm_handler.generate_response(request.query, data, sql_query)

        async def event_generator():
            try:
                # Send metadata first
                yield f"data: {{\"type\": \"metadata\", \"sql\": \"{sql_query}\", \"record_count\": {len(data) if data else 0}}}\n\n"

                # Stream the response character by character
                for char in response:
                    yield f"data: {{\"type\": \"text\", \"content\": \"{char}\"}}\n\n"
                    await asyncio.sleep(0.03)  # Simulate typing effect

                # Send completion signal
                yield f"data: {{\"type\": \"complete\"}}\n\n"

            except Exception as e:
                logger.error(f"Error in event generator: {e}")
                yield f"data: {{\"type\": \"error\", \"message\": \"Stream interrupted\"}}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except ValueError as e:
        logger.warning(f"Validation error in streaming query: {e}")
        async def error_event():
            yield f"data: {{\"type\": \"error\", \"message\": \"{str(e)}\"}}\n\n"
        return StreamingResponse(error_event(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Streaming query processing failed: {e}", exc_info=True)
        async def error_event():
            yield f"data: {{\"type\": \"error\", \"message\": \"Query processing failed. Please try again.\"}}\n\n"
        return StreamingResponse(error_event(), media_type="text/event-stream")

@app.get("/schema", response_model=SchemaResponse)
async def get_database_schema():
    """Get database schema information with enhanced error handling"""
    try:
        logger.info("Fetching database schema")
        schema = db_handler.get_schema()

        if not schema:
            raise HTTPException(status_code=404, detail="No database schema found")

        return SchemaResponse(
            schema=schema,
            table_count=len(schema)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve database schema")

@app.get("/sample-data", response_model=SampleDataResponse)
async def get_sample_data(table_name: Optional[str] = None, limit: int = 5):
    """Get sample data from the database with enhanced error handling"""
    try:
        logger.info(f"Fetching sample data for table: {table_name or 'all tables'}")

        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

        sample_data = db_handler.get_sample_data(table_name, limit)

        if not sample_data:
            raise HTTPException(status_code=404, detail="No sample data found")

        return SampleDataResponse(
            sample_data=sample_data,
            tables=list(sample_data.keys())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sample data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve sample data")

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics and performance metrics"""
    try:
        stats = query_cache.stats()
        return {
            "cache_stats": stats,
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached entries"""
    try:
        query_cache.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.post("/cache/cleanup")
async def cleanup_cache():
    """Remove expired cache entries"""
    try:
        removed_count = query_cache.cleanup_expired()
        return {
            "message": f"Cache cleanup completed",
            "removed_entries": removed_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")

@app.post("/export/csv")
async def export_data_csv(request: QueryRequest):
    """Export query results as CSV file"""
    try:
        logger.info(f"Exporting CSV for query: {request.query[:50]}...")

        # Generate SQL query using LLM
        sql_query = await llm_handler.generate_sql(request.query)

        # Validate SQL query for security
        validate_sql_query(sql_query)

        # Execute SQL query
        data = db_handler.execute_query(sql_query)

        if not data:
            raise HTTPException(status_code=404, detail="No data found for the query")

        # Create CSV content
        output = io.StringIO()
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        csv_content = output.getvalue()
        output.close()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ecommerce_data_{timestamp}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ValueError as e:
        logger.warning(f"Validation error in CSV export: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export data as CSV")

@app.post("/export/json")
async def export_data_json(request: QueryRequest):
    """Export query results as JSON file"""
    try:
        logger.info(f"Exporting JSON for query: {request.query[:50]}...")

        # Generate SQL query using LLM
        sql_query = await llm_handler.generate_sql(request.query)

        # Validate SQL query for security
        validate_sql_query(sql_query)

        # Execute SQL query
        data = db_handler.execute_query(sql_query)

        if not data:
            raise HTTPException(status_code=404, detail="No data found for the query")

        # Create JSON export with metadata
        export_data = {
            "metadata": {
                "query": request.query,
                "sql_query": sql_query,
                "export_timestamp": datetime.now().isoformat(),
                "record_count": len(data)
            },
            "data": data
        }

        json_content = json.dumps(export_data, indent=2, default=str)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ecommerce_data_{timestamp}.json"

        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ValueError as e:
        logger.warning(f"Validation error in JSON export: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export data as JSON")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )