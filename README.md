# Zerobus Station 🚌

A configuration-driven FastAPI service for ingesting data into Databricks tables via Zerobus streams.

## Features

- **Config-driven endpoints**: Automatically creates REST endpoints based on JSON configuration
- **Persistent streams**: Maintains long-lived Zerobus streams for optimal performance
- **Multi-table support**: Handle multiple tables with different schemas simultaneously
- **Dynamic validation**: Automatic request validation using Pydantic models
- **Organized structure**: Clean separation of proto files and stubs per table
- **Flexible durability**: Choose between fast async ingestion or guaranteed durability per request

## Project Structure

```
zerobus-station/
├── app.py                              # Main FastAPI application
├── stream_manager.py                   # Stream lifecycle management
├── config.json                         # Table configuration (created from example)
├── config.example.json                 # Example configuration template
├── .env                                # Environment variables (not committed)
├── .env.example                        # Example environment variables template
├── databricks_zerobus-*.whl            # Zerobus SDK wheel
├── Dockerfile                          # Docker container definition
├── tables/
│   ├── station_one/
│   │   ├── schema.proto                # Protobuf schema
│   │   └── schema_pb2.py               # Generated Python stubs
│   └── station_two/
│       ├── schema.proto
│       └── schema_pb2.py
└── README.md                           # This file
```

## Quick Start

This project includes two example tables (`station_one` and `station_two`) with pre-configured protobuf schemas. Follow these steps to get started quickly:

### 1. Create Example Tables in Databricks

Run these SQL commands in your Databricks workspace (replace `YOUR_CATALOG` and `YOUR_SCHEMA` with your values):

```sql
-- Create station_one table
CREATE TABLE YOUR_CATALOG.YOUR_SCHEMA.station_one (
  device_name STRING,
  temp INT,
  humidity BIGINT
)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableRowTracking' = 'false'
);

-- Create station_two table
CREATE TABLE YOUR_CATALOG.YOUR_SCHEMA.station_two (
  device_name STRING,
  temp INT,
  humidity BIGINT,
  description STRING
)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableRowTracking' = 'false'
);
```

### 2. Grant Permissions to Your Service Principal

```sql
-- Replace <service-principal-id> with your service principal's application ID
GRANT USE CATALOG ON CATALOG YOUR_CATALOG TO `<service-principal-id>`;
GRANT USE SCHEMA ON SCHEMA YOUR_CATALOG.YOUR_SCHEMA TO `<service-principal-id>`;
GRANT SELECT, MODIFY ON TABLE YOUR_CATALOG.YOUR_SCHEMA.station_one TO `<service-principal-id>`;
GRANT SELECT, MODIFY ON TABLE YOUR_CATALOG.YOUR_SCHEMA.station_two TO `<service-principal-id>`;
```

### 3. Configure the Service

```bash
# Copy example configuration files
cp .env.example .env
cp config.example.json config.json

# Edit .env with your service principal credentials
# Edit config.json with your workspace details and replace YOUR_CATALOG/YOUR_SCHEMA
```

### 4. Set Up Virtual Environment and Install Dependencies

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux (.venv\Scripts\activate on Windows)

# Install dependencies
uv sync
```

### 5. Run the Service

```bash
# Run the service (make sure virtual environment is activated)
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test the Endpoints

```bash
# Test station_one
curl -X POST http://localhost:8000/ingest/station_one \
  -H "Content-Type: application/json" \
  -d '{"device_name": "sensor-001", "temp": 25, "humidity": 60}'

# Test station_two
curl -X POST http://localhost:8000/ingest/station_two \
  -H "Content-Type: application/json" \
  -d '{"device_name": "sensor-002", "temp": 22, "humidity": 55, "description": "Main entrance"}'
```

## Setup

### Prerequisites

- Python 3.11+
- Databricks workspace with Zerobus access
- Databricks workspace ID
- Service principal with the following permissions:
  - On catalog: `USE_CATALOG`
  - On schema: `USE_SCHEMA`
  - On table: `MODIFY`, `SELECT`

### Installation

1. **Set up virtual environment:**

Using `uv` (recommended):
```bash
# Create virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

Or using standard Python `venv`:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

Once activated, your terminal prompt should show `(.venv)` at the beginning.

2. **Install dependencies:**

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install fastapi uvicorn python-dotenv
pip install databricks_zerobus-0.0.17-py3-none-any.whl
```

3. **Create a `.env` file from the example:**
```bash
cp .env.example .env
```

4. **Edit `.env` with your credentials:**
```bash
DATABRICKS_CLIENT_ID=your-service-principal-id
DATABRICKS_CLIENT_SECRET=your-service-principal-secret
```

**Note**: The `.env` file is automatically loaded on startup and should never be committed to version control.

## Configuration

The service is driven by [config.json](config.json), which defines:

- Databricks connection details (server endpoint, workspace ID, workspace URL)
- Table definitions with schemas
- Protobuf message mappings

**Quick Start:**
```bash
cp config.example.json config.json
```

Then edit `config.json` with your Databricks details and table definitions.

### Configuration Format

```json
{
  "databricks": {
    "server_endpoint": "workspace-id.zerobus.region.cloud.databricks.com",
    "workspace_id": "workspace-id",
    "workspace_url": "https://workspace-url.cloud.databricks.com"
  },
  "tables": {
    "station_one": {
      "table_name": "catalog.schema.table_name",
      "proto_package": "station_one",
      "message_name": "StationOne",
      "fields": [
        {"name": "device_name", "type": "string", "proto_type": "optional string", "field_num": 1},
        {"name": "temp", "type": "int32", "proto_type": "optional int32", "field_num": 2},
        {"name": "humidity", "type": "int64", "proto_type": "optional int64", "field_num": 3}
      ]
    }
  }
}
```

## Running the Service

### Locally

Start the server:

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The service will:
1. Load environment variables from `.env`
2. Load configuration from `config.json`
3. Create Pydantic validation models for each table
4. Initialize the stream manager with OAuth token factory
5. Create dynamic endpoints for each table

### With Docker

Build and run:

```bash
docker build -t zerobus-station .
docker run -p 8000:8000 --env-file .env zerobus-station
```

## API Endpoints

### Global Endpoints

#### `GET /`
Service information and available endpoints

```bash
curl http://localhost:8000/
```

#### `GET /health`
Global health check showing active streams

```bash
curl http://localhost:8000/health
```

### Table-Specific Endpoints

For each table in the config, the following endpoints are created:

#### `POST /ingest/{table_key}`
Ingest a record into the specified table

**Fast async ingestion (default):**
```bash
curl -X POST http://localhost:8000/ingest/station_one \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "sensor-001",
    "temp": 25,
    "humidity": 60
  }'
```

**With durability guarantee:**
```bash
curl -X POST "http://localhost:8000/ingest/station_one?wait_for_ack=true" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "sensor-001",
    "temp": 25,
    "humidity": 60
  }'
```

**Query Parameters:**
- `wait_for_ack` (bool, default: false): If true, waits for server acknowledgment before returning. Use false for maximum throughput, true for guaranteed durability.

#### `GET /health/{table_key}`
Health check for a specific table

```bash
curl http://localhost:8000/health/station_one
```

#### `POST /flush/{table_key}`
Flush pending records for a table to ensure durability

```bash
curl -X POST http://localhost:8000/flush/station_one
```

## Adding a New Table

Follow these steps to add a new table to the service:

### 1. Create the Databricks Table

Create your table in Databricks SQL:

```sql
CREATE TABLE catalog.schema.my_new_table (
  field1 STRING,
  field2 INT,
  field3 BIGINT
)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableRowTracking' = 'false'
);
GRANT USE CATALOG ON CATALOG YOUR_CATALOG TO `<service-principal-id>`;
GRANT USE SCHEMA ON SCHEMA YOUR_CATALOG.YOUR_SCHEMA TO `<service-principal-id>`;
GRANT SELECT, MODIFY ON TABLE YOUR_CATALOG.YOUR_SCHEMA.station_one TO `<service-principal-id>`;
GRANT SELECT, MODIFY ON TABLE YOUR_CATALOG.YOUR_SCHEMA.station_two TO `<service-principal-id>`;
```

### 2. Create the Proto Directory

```bash
mkdir -p tables/my_new_table
```

### 3. Create the Protobuf Schema

Create `tables/my_new_table/schema.proto`:

```protobuf
syntax = "proto2";

package my_new_table;

message MyNewTable {
    optional string field1 = 1;
    optional int32 field2 = 2;
    optional int64 field3 = 3;
}
```

**Important Notes:**
- Field types must match your Databricks table schema
- Field numbers must be sequential starting from 1
- Use `int32` for INT, `int64` for BIGINT, `string` for STRING
- Package name should match your table key

### 4. Compile the Proto File

```bash
protoc --python_out=. tables/my_new_table/schema.proto
```

This generates `tables/my_new_table/schema_pb2.py`.

### 5. Update config.json

Add your table configuration:

```json
{
  "databricks": {
    "server_endpoint": "workspace-id.zerobus.region.cloud.databricks.com",
    "workspace_id": "workspace-id",
    "workspace_url": "https://workspace-url.cloud.databricks.com"
  },
  "tables": {
    "my_new_table": {
      "table_name": "catalog.schema.my_new_table",
      "proto_package": "my_new_table",
      "message_name": "MyNewTable",
      "fields": [
        {"name": "field1", "type": "string", "proto_type": "optional string", "field_num": 1},
        {"name": "field2", "type": "int32", "proto_type": "optional int32", "field_num": 2},
        {"name": "field3", "type": "int64", "proto_type": "optional int64", "field_num": 3}
      ]
    }
  }
}
```

**Configuration Fields:**
- `table_name`: Fully qualified table name in Databricks (catalog.schema.table)
- `proto_package`: Must match the package name in your .proto file
- `message_name`: Must match the message name in your .proto file
- `fields`: List of fields for Pydantic validation (must match proto definition)

### 6. Restart the Service

```bash
# Stop the current service (Ctrl+C)
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Or for Docker:
```bash
docker build -t zerobus-station .
docker run -p 8000:8000 --env-file .env zerobus-station
```

### 7. Test the New Endpoint

```bash
curl -X POST http://localhost:8000/ingest/my_new_table \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "test",
    "field2": 123,
    "field3": 456
  }'
```

The endpoint will be automatically available at `/ingest/my_new_table`.

## Stream Management

The `StreamManager` class handles:

- **Lazy initialization**: Streams are created on first request
- **Connection pooling**: One persistent stream per table
- **OAuth token management**: Automatic token generation using token factory
- **Health monitoring**: Automatic stream state checking
- **Graceful recovery**: Handles stream failures and recreates as needed
- **Clean shutdown**: Flushes and closes all streams on service shutdown

## Testing

### Health Check
```bash
# Global health
curl http://localhost:8000/health

# Table-specific health
curl http://localhost:8000/health/station_one
curl http://localhost:8000/health/station_two
```

### Ingest Sample Data
```bash
# Fast async ingestion
curl -X POST http://localhost:8000/ingest/station_one \
  -H "Content-Type: application/json" \
  -d '{"device_name": "sensor-001", "temp": 25, "humidity": 60}'

# With durability guarantee
curl -X POST "http://localhost:8000/ingest/station_one?wait_for_ack=true" \
  -H "Content-Type: application/json" \
  -d '{"device_name": "sensor-001", "temp": 25, "humidity": 60}'
```

### View API Documentation
FastAPI automatically generates interactive API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

### Stream Lifecycle

1. **First Request**: When the first record is sent to `/ingest/{table_key}`, the stream manager creates a new Zerobus stream with OAuth token factory
2. **Subsequent Requests**: The same stream is reused for better performance
3. **Health Checks**: Stream state is validated before each use
4. **Recovery**: Failed streams are automatically recreated with fresh tokens
5. **Shutdown**: All streams are gracefully flushed and closed

### Request Flow

```
Client Request
    ↓
FastAPI Endpoint (/ingest/{table_key})
    ↓
JSON Validation (Pydantic)
    ↓
Get/Create Stream (StreamManager)
    ↓
OAuth Token (via token_factory)
    ↓
Convert JSON → Protobuf
    ↓
Ingest via Zerobus Stream
    ↓
[Optional] Wait for Ack
    ↓
Response to Client
```

### Authentication Flow

The service uses OAuth 2.0 with client credentials:
1. Stream manager creates a `token_factory` function
2. Token factory calls `get_zerobus_token()` from the Zerobus SDK
3. Token is automatically refreshed on stream creation/recovery
4. Tokens are scoped to specific table permissions

## Performance Considerations

- **Persistent Streams**: Streams are kept alive between requests for minimal latency
- **Async Operations**: FastAPI's async capabilities ensure non-blocking operations
- **Buffering**: Zerobus SDK handles buffering and flow control automatically (50,000 in-flight records by default)
- **Batch Flushing**: Use the `/flush/{table_key}` endpoint to ensure durability without waiting per-record
- **Fast vs. Durable**: Use `wait_for_ack=false` for high throughput, `wait_for_ack=true` for guaranteed durability

## Error Handling

The service handles various error scenarios:

- **Invalid Table**: Returns 404 if table not found in config
- **Validation Errors**: Returns 400 with detailed validation messages
- **Stream Failures**: Returns 500 and logs detailed error information
- **Automatic Recovery**: StreamManager recreates failed streams automatically
- **OAuth Errors**: Logged with full details for debugging

## License

&copy; 2025 Databricks, Inc. All rights reserved. The source in this notebook is provided subject to the Databricks License [https://databricks.com/db-license-source].  All included or referenced third party libraries are subject to the licenses set forth below.
