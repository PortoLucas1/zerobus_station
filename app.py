"""
FastAPI Zerobus Ingestion Service

Configuration-driven service that exposes REST endpoints for ingesting
data into Databricks tables via Zerobus streams.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import create_model

from stream_manager import StreamManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

stream_manager: StreamManager = None
config: Dict = None
table_models: Dict[str, Any] = {}


def load_config() -> Dict:
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def create_pydantic_model(table_key: str, fields: list):
    """
    Create a Pydantic model dynamically from field definitions.

    Args:
        table_key: Unique table identifier
        fields: List of field definitions from config

    Returns:
        Pydantic model class
    """
    field_definitions = {}
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]

        type_map = {
            "string": (str, ...),
            "int32": (int, ...),
            "int64": (int, ...),
            "float": (float, ...),
            "double": (float, ...),
            "bool": (bool, ...),
        }

        if field_type in type_map:
            field_definitions[field_name] = type_map[field_type]
        else:
            field_definitions[field_name] = (str, ...)

    model_name = f"{table_key.title().replace('_', '')}Record"
    return create_model(model_name, **field_definitions)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global stream_manager, config, table_models

    logger.info("Starting Zerobus Station service...")

    config = load_config()
    logger.info(f"Loaded configuration with {len(config['tables'])} tables")

    client_id = os.getenv("DATABRICKS_CLIENT_ID")
    client_secret = os.getenv("DATABRICKS_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET must be set")
        raise ValueError("Missing required environment variables")

    stream_manager = StreamManager(
        server_endpoint=config["databricks"]["server_endpoint"],
        workspace_id=config["databricks"]["workspace_id"],
        workspace_url=config["databricks"]["workspace_url"],
        client_id=client_id,
        client_secret=client_secret,
    )
    logger.info("✓ Stream manager initialized")

    for table_key, table_config in config["tables"].items():
        table_models[table_key] = create_pydantic_model(
            table_key, table_config["fields"]
        )
        logger.info(f"✓ Created validation model for {table_key}")

    logger.info("=" * 60)
    logger.info("Zerobus Station is ready!")
    logger.info("Available endpoints:")
    for table_key in config["tables"].keys():
        logger.info(f"  POST /ingest/{table_key}")
        logger.info(f"  GET  /health/{table_key}")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down Zerobus Station...")
    if stream_manager:
        await stream_manager.close_all()
    logger.info("✓ Shutdown complete")


app = FastAPI(
    title="Zerobus Station",
    description="Configuration-driven Databricks ingestion service using Zerobus",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Zerobus Station",
        "version": "1.0.0",
        "tables": list(config["tables"].keys()) if config else [],
        "endpoints": {
            table_key: {
                "ingest": f"/ingest/{table_key}",
                "health": f"/health/{table_key}",
            }
            for table_key in (config["tables"].keys() if config else [])
        },
    }


@app.get("/health")
async def health():
    """Global health check"""
    return {
        "status": "healthy",
        "active_streams": stream_manager.get_active_tables() if stream_manager else [],
    }


@app.get("/health/{table_key}")
async def table_health(table_key: str):
    """Health check for a specific table"""
    if not config or table_key not in config["tables"]:
        raise HTTPException(status_code=404, detail=f"Table {table_key} not found")

    is_active = table_key in (
        stream_manager.get_active_tables() if stream_manager else []
    )

    return {
        "table": table_key,
        "table_name": config["tables"][table_key]["table_name"],
        "stream_active": is_active,
        "status": "healthy",
    }


@app.post("/ingest/{table_key}")
async def ingest_record(
    table_key: str, body: Dict[str, Any], wait_for_ack: bool = False
):
    """
    Ingest a record into the specified table.

    Args:
        table_key: Table identifier (e.g., "station_one")
        body: JSON payload matching the table schema
        wait_for_ack: If True, waits for durability acknowledgment (default: False)

    Returns:
        Acknowledgment of ingestion
    """
    if not config or table_key not in config["tables"]:
        raise HTTPException(status_code=404, detail=f"Table {table_key} not found")

    try:
        model = table_models[table_key]
        validated_data = model(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

    table_config = config["tables"][table_key]

    try:
        await stream_manager.get_stream(
            table_key=table_key,
            table_name=table_config["table_name"],
            proto_module=f"tables.{table_key}.schema_pb2",
            message_name=table_config["message_name"],
        )

        pb_module = import_module(f"tables.{table_key}.schema_pb2")
        message_class = getattr(pb_module, table_config["message_name"])

        record_dict = validated_data.model_dump()
        record = message_class(**record_dict)

        future = await stream_manager.ingest_record(table_key, record)

        if wait_for_ack:
            await future

        return {
            "status": "success",
            "table": table_key,
            "message": "Record ingested successfully",
            "wait_for_ack": wait_for_ack,
        }

    except Exception as e:
        logger.error(f"Error ingesting record into {table_key}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to ingest record: {str(e)}"
        )


@app.post("/flush/{table_key}")
async def flush_table(table_key: str):
    """
    Flush pending records for a specific table.

    Args:
        table_key: Table identifier

    Returns:
        Flush status
    """
    if not config or table_key not in config["tables"]:
        raise HTTPException(status_code=404, detail=f"Table {table_key} not found")

    if table_key not in stream_manager.streams:
        return {
            "status": "no_active_stream",
            "table": table_key,
            "message": "No active stream to flush",
        }

    try:
        stream = stream_manager.streams[table_key]
        await stream.flush()
        return {
            "status": "success",
            "table": table_key,
            "message": "Stream flushed successfully",
        }
    except Exception as e:
        logger.error(f"Error flushing stream for {table_key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to flush stream: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )
