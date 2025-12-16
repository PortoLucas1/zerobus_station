"""
Stream Manager for Zerobus Streams

Manages persistent Zerobus streams for each configured table.
Handles stream lifecycle, health checks, and graceful cleanup.
"""

import asyncio
import logging
from typing import Dict
from importlib import import_module

from zerobus.sdk.aio import ZerobusSdk
from zerobus.sdk.shared import StreamConfigurationOptions, TableProperties

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages persistent Zerobus streams for multiple tables.

    Each table gets one persistent stream that is kept alive for performance.
    Streams are created on-demand and cleaned up when no longer needed.
    """

    def __init__(self, server_endpoint: str, workspace_id: str, workspace_url: str,
                 client_id: str, client_secret: str):
        """
        Initialize the StreamManager.

        Args:
            server_endpoint: Zerobus gRPC endpoint
            workspace_id: Databricks workspace ID
            workspace_url: Databricks workspace URL (also used as Unity Catalog URL)
            client_id: OAuth client ID (service principal)
            client_secret: OAuth client secret
        """
        self.server_endpoint = server_endpoint
        self.workspace_id = workspace_id
        self.workspace_url = workspace_url
        self.client_id = client_id
        self.client_secret = client_secret

        # Initialize SDK with both host and Unity Catalog URL
        self.sdk = ZerobusSdk(host=server_endpoint, unity_catalog_url=workspace_url)
        self.streams: Dict[str, any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_stream(self, table_key: str, table_name: str,
                         proto_module: str, message_name: str):
        """
        Get or create a stream for a table.

        Args:
            table_key: Unique key for the table (e.g., "station_one")
            table_name: Fully qualified table name in Databricks
            proto_module: Python module path for the protobuf (e.g., "tables.station_one.schema_pb2")
            message_name: Name of the protobuf message (e.g., "StationOne")

        Returns:
            The Zerobus stream for this table
        """
        if table_key not in self._locks:
            self._locks[table_key] = asyncio.Lock()

        async with self._locks[table_key]:
            if table_key in self.streams:
                stream = self.streams[table_key]
                state = stream.get_state()
                if str(state) in ["OPENED", "StreamState.OPENED"]:
                    return stream
                else:
                    logger.warning(f"Stream {table_key} is in state {state}, recreating...")
                    await self._close_stream(table_key)

            logger.info(f"Creating new stream for table {table_key} ({table_name})")

            try:
                pb_module = import_module(proto_module)
                message_class = getattr(pb_module, message_name)
                descriptor = message_class.DESCRIPTOR
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to import protobuf for {table_key}: {e}")
                raise

            # Configure stream options
            options = StreamConfigurationOptions(
                max_inflight_records=50_000,
                recovery=True,
                ack_callback=self._create_ack_callback(table_key)
            )

            table_properties = TableProperties(table_name, descriptor)

            try:
                # create_stream now takes client_id and client_secret directly
                stream = await self.sdk.create_stream(
                    self.client_id,
                    self.client_secret,
                    table_properties,
                    options
                )
                self.streams[table_key] = stream
                logger.info(f"✓ Stream created for {table_key}: {stream.stream_id}")
                return stream
            except Exception as e:
                logger.error(f"Failed to create stream for {table_key}: {e}")
                raise

    def _create_ack_callback(self, table_key: str):
        """Create an acknowledgment callback for a specific table."""
        def callback(response):
            offset = response.durability_ack_up_to_offset
            if offset % 1000 == 0:
                logger.info(f"[{table_key}] Acknowledged up to offset: {offset}")
        return callback

    async def ingest_record(self, table_key: str, record):
        """
        Ingest a record into the specified table's stream.

        Args:
            table_key: Table identifier
            record: Protobuf message to ingest

        Returns:
            Future that resolves when record is acknowledged
        """
        if table_key not in self.streams:
            raise ValueError(f"No stream available for table {table_key}")

        stream = self.streams[table_key]
        future = await stream.ingest_record(record)
        return future

    async def _close_stream(self, table_key: str):
        """Close a specific stream."""
        if table_key in self.streams:
            stream = self.streams[table_key]
            try:
                await stream.close()
                logger.info(f"✓ Stream closed for {table_key}")
            except Exception as e:
                logger.error(f"Error closing stream for {table_key}: {e}")
            finally:
                del self.streams[table_key]

    async def close_all(self):
        """Close all active streams gracefully."""
        logger.info("Closing all streams...")
        for table_key in list(self.streams.keys()):
            await self._close_stream(table_key)
        logger.info("✓ All streams closed")

    async def remove_table(self, table_key: str):
        """
        Remove a table's stream (called when table is removed from config).

        Args:
            table_key: Table identifier to remove
        """
        logger.info(f"Removing stream for table {table_key}")
        await self._close_stream(table_key)

    def get_active_tables(self) -> list:
        """Get list of tables with active streams."""
        return list(self.streams.keys())
