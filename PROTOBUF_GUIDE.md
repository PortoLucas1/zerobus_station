# Protobuf Schema Guide

## 📋 Overview

This project uses Protocol Buffers (protobuf) to define data schemas for ingestion into Databricks via Zerobus. Each table has its own `.proto` file that must be compiled into Python modules.

## 📁 Directory Structure

```
tables/
├── __init__.py
├── station_one/
│   ├── __init__.py
│   ├── schema.proto          # Source proto definition
│   └── schema_pb2.py         # Compiled Python module (generated)
└── station_two/
    ├── __init__.py
    ├── schema.proto          # Source proto definition
    └── schema_pb2.py         # Compiled Python module (generated)
```

## ✅ Already Compiled

Your protobuf schemas have been compiled and are ready to use:
- ✅ `tables/station_one/schema_pb2.py`
- ✅ `tables/station_two/schema_pb2.py`

## 🔄 When to Recompile

You need to recompile protobuf files when:
1. You modify any `.proto` file
2. You add a new table with a new schema
3. You clone the repository on a new machine (if `*_pb2.py` files are gitignored)

## 🛠️ How to Compile

### Option 1: Use the Provided Script (Recommended)

```bash
./compile_protos.sh
```

This script automatically compiles all `.proto` files in the `tables/` directory.

### Option 2: Manual Compilation

Compile individual proto files:

```bash
# Activate virtual environment
source .venv/bin/activate

# Compile specific proto files
python -m grpc_tools.protoc --python_out=. --proto_path=. tables/station_one/schema.proto
python -m grpc_tools.protoc --python_out=. --proto_path=. tables/station_two/schema.proto
```

## ➕ Adding a New Table

When adding a new table:

1. **Create the directory structure:**
   ```bash
   mkdir -p tables/station_three
   ```

2. **Create the proto file** (`tables/station_three/schema.proto`):
   ```protobuf
   syntax = "proto2";
   
   package station_three;
   
   message StationThree {
       optional string device_name = 1;
       optional int32 value = 2;
   }
   ```

3. **Create `__init__.py`:**
   ```bash
   touch tables/station_three/__init__.py
   ```

4. **Compile the proto:**
   ```bash
   ./compile_protos.sh
   ```
   
   Or manually:
   ```bash
   python -m grpc_tools.protoc --python_out=. --proto_path=. tables/station_three/schema.proto
   ```

5. **Update `config.json`** to include the new table

## 🔍 Verifying Compilation

Test that your compiled protos can be imported:

```bash
python -c "from tables.station_one.schema_pb2 import StationOne; print('✓ Works!')"
python -c "from tables.station_two.schema_pb2 import StationTwo; print('✓ Works!')"
```

## 📝 Proto File Format

Your `.proto` files should follow this format:

```protobuf
syntax = "proto2";

package your_package_name;

// Message definition
message YourMessage {
    optional string field1 = 1;
    optional int32 field2 = 2;
    optional int64 field3 = 3;
    // ... more fields
}
```

**Important Notes:**
- Use `syntax = "proto2"` for Zerobus compatibility
- Field numbers must be unique and sequential
- Use appropriate data types (string, int32, int64, etc.)

## 🚫 Common Errors

### Error: `No module named 'tables.station_one.schema_pb2'`

**Cause:** Proto files haven't been compiled.

**Solution:** Run `./compile_protos.sh`

### Error: `ModuleNotFoundError: No module named 'tables'`

**Cause:** Missing `__init__.py` files.

**Solution:** Ensure all directories have `__init__.py`:
```bash
touch tables/__init__.py
touch tables/station_one/__init__.py
touch tables/station_two/__init__.py
```

### Error: `google.protobuf not found`

**Cause:** Missing protobuf or grpcio-tools.

**Solution:**
```bash
pip install grpcio-tools protobuf
```

## 📦 Dependencies

The following packages are required for protobuf compilation:
- `grpcio-tools>=1.76.0` (includes protoc compiler)
- `protobuf>=6.33.2` (installed with zerobus SDK)

These are included in `requirements.txt` and `pyproject.toml`.

