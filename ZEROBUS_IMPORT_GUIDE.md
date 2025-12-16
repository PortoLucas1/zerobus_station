# Databricks Zerobus SDK Import Guide

## ✅ Correct Import Paths

The `databricks-zerobus-ingest-sdk` package is installed as the `zerobus` module.

### Async SDK (for async/await usage)
```python
from zerobus.sdk.aio import ZerobusSdk
```

### Sync SDK (for synchronous usage)
```python
from zerobus.sdk import ZerobusSdk
# or
from zerobus.sdk.sync import ZerobusSdk
```

### Shared Components
```python
from zerobus.sdk.shared import (
    StreamConfigurationOptions,
    TableProperties,
    StreamState,
    RecordAcknowledgment,
    RecordType
)
```

**Note:** The SDK handles authentication directly via `client_id` and `client_secret` passed to `create_stream()`. The `get_zerobus_token` function is no longer needed.

### Exception Handling
```python
from zerobus.sdk import (
    ZerobusException,
    NonRetriableException
)
```

## ❌ Incorrect Import Paths (Do Not Use)

```python
# WRONG - This will cause ModuleNotFoundError
from zerobus_sdk.aio import ZerobusSdk
from zerobus_sdk.shared import StreamConfigurationOptions

# WRONG - This will also fail
from databricks_zerobus_ingest_sdk import ZerobusSdk
```

## 📦 Package vs Module Name

- **Package name** (for pip): `databricks-zerobus-ingest-sdk`
- **Module name** (for imports): `zerobus`

This is a common pattern in Python packages where the package name differs from the import name.

## 🔧 Fixed Files

- ✅ `stream_manager.py` - Updated to use correct imports

## 🔧 SDK Initialization

The `ZerobusSdk` requires two parameters:

### Async SDK
```python
from zerobus.sdk.aio import ZerobusSdk

sdk = ZerobusSdk(
    host="your-workspace-id.zerobus.region.cloud.databricks.com",
    unity_catalog_url="https://your-workspace-url.azuredatabricks.net"
)
```

### Sync SDK
```python
from zerobus.sdk import ZerobusSdk

sdk = ZerobusSdk(
    host="your-workspace-id.zerobus.region.cloud.databricks.com",
    unity_catalog_url="https://your-workspace-url.azuredatabricks.net"
)
```

**Note:** The `unity_catalog_url` is typically the same as your Databricks workspace URL.

### Creating a Stream

The `create_stream` method requires authentication credentials:

```python
from zerobus.sdk.aio import ZerobusSdk
from zerobus.sdk.shared import TableProperties, StreamConfigurationOptions

sdk = ZerobusSdk(host="...", unity_catalog_url="...")

# Configure stream options
options = StreamConfigurationOptions(
    max_inflight_records=50_000,
    recovery=True,
    ack_callback=your_callback_function
)

# Create table properties with protobuf descriptor
table_properties = TableProperties(table_name, protobuf_descriptor)

# Create stream with authentication
stream = await sdk.create_stream(
    client_id,           # OAuth client ID
    client_secret,       # OAuth client secret
    table_properties,    # Table configuration
    options             # Stream configuration
)
```

**Important:** The SDK now handles authentication internally. You no longer need to use `token_factory` or `get_zerobus_token` in the options.

## 🚀 Verification

To verify your imports are correct, run:
```bash
source .venv/bin/activate
python -c "from zerobus.sdk.aio import ZerobusSdk; print('Success!')"
```

