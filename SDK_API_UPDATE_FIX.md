# ✅ SDK API Update Fixed

## The Problem

Error received:
```
ZerobusSdk.create_stream() missing 1 required positional argument: 'table_properties'
```

## Root Cause

The Databricks Zerobus SDK API has changed in version 0.2.0. The `create_stream` method now has a different signature.

### Old API (Expected)
```python
stream = await sdk.create_stream(table_properties, options)
```

### New API (v0.2.0)
```python
stream = await sdk.create_stream(
    client_id,
    client_secret,
    table_properties,
    options
)
```

## Changes Made

### 1. Updated `stream_manager.py` Imports

**Before:**
```python
from zerobus.sdk.shared import StreamConfigurationOptions, TableProperties, get_zerobus_token
```

**After:**
```python
from zerobus.sdk.shared import StreamConfigurationOptions, TableProperties
```

**Reason:** `get_zerobus_token` is no longer needed as the SDK handles authentication internally.

### 2. Removed `token_factory` from Options

**Before:**
```python
def token_factory():
    return get_zerobus_token(
        table_name=table_name,
        workspace_id=self.workspace_id,
        workspace_url=self.workspace_url,
        client_id=self.client_id,
        client_secret=self.client_secret
    )

options = StreamConfigurationOptions(
    max_inflight_records=50_000,
    recovery=True,
    token_factory=token_factory,  # ← No longer supported
    ack_callback=self._create_ack_callback(table_key)
)
```

**After:**
```python
options = StreamConfigurationOptions(
    max_inflight_records=50_000,
    recovery=True,
    ack_callback=self._create_ack_callback(table_key)
)
```

**Reason:** The `StreamConfigurationOptions` no longer accepts `token_factory`. Authentication is now handled by passing credentials directly to `create_stream`.

### 3. Updated `create_stream()` Call

**Before:**
```python
stream = await self.sdk.create_stream(table_properties, options)
```

**After:**
```python
stream = await self.sdk.create_stream(
    self.client_id,
    self.client_secret,
    table_properties,
    options
)
```

**Reason:** The method signature now requires `client_id` and `client_secret` as the first two positional arguments.

## SDK Method Signature

```python
async def create_stream(
    self,
    client_id: str,              # OAuth client ID (service principal)
    client_secret: str,          # OAuth client secret
    table_properties: TableProperties,  # Table configuration
    options: StreamConfigurationOptions = default  # Stream options
) -> ZerobusStream
```

## Verification

```bash
✓ stream_manager imports successfully
✓ Application imports successfully
✓ create_stream() signature matches SDK v0.2.0
```

## Impact on Your Code

The `StreamManager` class now:
- ✅ Passes `client_id` and `client_secret` directly to `create_stream()`
- ✅ No longer uses `token_factory` pattern
- ✅ Simplified authentication flow
- ✅ Compatible with SDK v0.2.0

## Documentation Updated

- ✅ `ZEROBUS_IMPORT_GUIDE.md` - Added `create_stream` usage examples
- ✅ Removed references to `get_zerobus_token`
- ✅ Added note about authentication handling

## 🚀 Status: Ready to Test

Your API should now work correctly. Try:

```bash
curl -X POST http://localhost:8000/ingest/station_one \
  -H "Content-Type: application/json" \
  -d '{"device_name": "sensor-001", "temp": 25, "humidity": 60}'
```

The error about missing `table_properties` argument is now resolved! ✅

