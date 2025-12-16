#!/bin/bash
# Script to compile all protobuf schemas

set -e

echo "🔧 Compiling Protobuf Schemas..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Compile all proto files
for proto_file in tables/*/schema.proto; do
    echo "  → Compiling $proto_file"
    python -m grpc_tools.protoc --python_out=. --proto_path=. "$proto_file"
done

echo "✓ All protobuf schemas compiled successfully!"
echo ""
echo "Generated files:"
find tables -name "*_pb2.py" -type f

