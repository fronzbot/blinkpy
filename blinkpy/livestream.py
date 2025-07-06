"""Handles immis livestream."""

import asyncio
import logging
import urllib.parse
import ssl

_LOGGER = logging.getLogger(__name__)


class BlinkStream:
    """Class to initialize individual stream."""

    # Reference: https://github.com/amattu2/blink-liveview-middleware

    def __init__(self, camera, response):
        """Initialize BlinkStream."""
        self.camera = camera
        self.command_id = response["command_id"]
        self.polling_interval = response["polling_interval"]
        self.target = urllib.parse.urlparse(response["server"])
        self.server = None
        self.clients = []
        self.target_reader = None
        self.target_writer = None

    def get_auth_header(self):
        """Get authentication header."""
        auth_header = bytearray()

        # Magic numeber
        # fmt: off
        magic_number = [
            0x00, 0x00, 0x00, 0x28, # Magic number (4 bytes)
        ]
        # fmt: on
        auth_header.extend(magic_number)
        # Total packet length: 4 bytes

        # Unknown string field (4-byte length prefix, 16 unknown bytes)
        # fmt: off
        unknown_string_field = [
            0x00, 0x00, 0x00, 0x00, # Length prefix (4 bytes)
        ] + ([0x00] * 16) # Unknown bytes (16 bytes)
        # fmt: on
        auth_header.extend(unknown_string_field)
        # Total packet length: 24 bytes

        # Client ID field
        client_id = urllib.parse.parse_qs(self.target.query).get("client_id", [0])[0]
        _LOGGER.debug("Client ID: %s", client_id)
        client_id_field = int(client_id).to_bytes(4, byteorder="big")
        _LOGGER.debug("Client ID field: %s (%d)", client_id_field, len(client_id_field))
        auth_header.extend(client_id_field)
        # Total packet length: 28 bytes

        # Unknown prefix field (2-byte static prefix, 4-byte length prefix, 64 unknown bytes)
        # fmt: off
        unknown_prefix_field = [
            0x01, 0x08, # Static prefix (2 bytes)
            0x00, 0x00, 0x00, 0x00, # Length prefix (4 bytes)
        ] + ([0x00] * 64) # Unknown bytes (64 bytes)
        # fmt: on
        auth_header.extend(unknown_prefix_field)
        # Total packet length: 98 bytes

        # Connection ID length field (4-byte length prefix)
        connection_id_length_prefix = [
            0x00, 0x00, 0x00, 0x10,
        ]
        # fmt: on
        auth_header.extend(connection_id_length_prefix)
        # Total packet length: 102 bytes

        # Connection ID field (UTF-8-encoded, 16 bytes)
        connection_id = self.target.path.split("/")[-1].split("__")[0]
        _LOGGER.debug("Connection ID: %s", connection_id)
        connection_id_field = connection_id.encode("utf-8")[:16]
        _LOGGER.debug("Connection ID frame: %s (%d)", connection_id_field, len(connection_id_field))
        auth_header.extend(connection_id_field)
        # Total packet length: 118 bytes

        # Trailer (static 4-byte trailer)
        # fmt: off
        trailer_static = [
            0x00, 0x00, 0x00, 0x01,
        ]
        # fmt: on
        auth_header.extend(trailer_static)
        # Total packet length: 122 bytes

        _LOGGER.debug("Auth header length: %d", len(auth_header))
        return auth_header

    async def start(self):
        """Start the stream."""
        self.server = await asyncio.start_server(self.join, "127.0.0.1")
        return self.server

    @property
    def socket(self):
        """Return the socket."""
        return self.server.sockets[0]

    @property
    def url(self):
        """Return the URL of the stream."""
        sockname = self.socket.getsockname()
        return f"tcp://{sockname[0]}:{sockname[1]}"

    @property
    def is_serving(self):
        """Check if the stream is active."""
        return self.server and self.server.is_serving()

    async def feed(self):
        """Connect to and stream from the target server."""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.target_reader, self.target_writer = await asyncio.open_connection(
            self.target.hostname, self.target.port, ssl=ssl_context
        )

        auth_header = self.get_auth_header()
        self.target_writer.write(auth_header)
        await self.target_writer.drain()

        try:
            await asyncio.gather(self.copy(), self.ping())
        except Exception:
            _LOGGER.exception("Error while handling stream")
        finally:
            # Close all connections
            _LOGGER.debug("Streaming was aborted, stopping server")
            self.stop()

    async def join(self, client_reader, client_writer):
        """Join client to the stream."""
        # Client connected
        self.clients.append(client_writer)

        try:
            while not client_writer.is_closing():
                # Read data from the client
                data = await client_reader.read(1024)
                if not data:
                    break

                # Yield control to the event loop
                await asyncio.sleep(0)
        except ConnectionResetError:
            _LOGGER.debug("Client disconnected")
        except Exception:
            _LOGGER.exception("Error while handling client")
        finally:
            # Client disconnecting
            self.clients.remove(client_writer)
            if not client_writer.is_closing():
                client_writer.close()

            # If no clients are connected, stop everything
            if not self.clients:
                _LOGGER.debug("Last client disconnected, stopping server")
                self.stop()

    async def copy(self):
        """Copy data from one reader to multiple writers."""
        try:
            while not self.target_reader.at_eof():
                # Read data from the target server
                async with asyncio.timeout(3):
                    data = await self.target_reader.read(1024)
                    if not data:
                        break

                # Send data to all connected clients
                for writer in self.clients:
                    if not writer.is_closing():
                        writer.write(data)
                        await writer.drain()

                # Yield control to the event loop
                await asyncio.sleep(0)
        finally:
            # Abort ping by closing the target writer
            self.target_writer.close()

    async def ping(self):
        """Send keep-alive messages to the server."""
        # fmt: off
        keepalive_frame = [
            0x12, 0x00, 0x00, 0x03, 0xe8, 0x00, 0x00, 0x00, 0x18, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
        ]
        # fmt: on
        try:
            while not self.target_writer.is_closing():
                # Sleep and yield for the polling interval
                await asyncio.sleep(self.polling_interval)

                # Check if the target writer is still open
                if self.target_writer.is_closing():
                    break

                # Send keep-alive frame to the target server
                _LOGGER.debug("Sending keep-alive frame")
                self.target_writer.write(bytearray(keepalive_frame))
                await self.target_writer.drain()
        finally:
            # Abort copy by closing the target reader
            self.target_reader.feed_eof()

    def stop(self):
        """Stop the stream."""
        # Close all connections
        _LOGGER.debug("Stopping server, closing remaining connections")
        if self.server and self.server.is_serving():
            _LOGGER.debug("Closing listen server")
            self.server.close()
        if self.target_writer and not self.target_writer.is_closing():
            _LOGGER.debug("Closing target writer")
            self.target_writer.close()
        for writer in self.clients:
            if not writer.is_closing():
                _LOGGER.debug("Closing client writer")
                writer.close()
        _LOGGER.debug("All remaining connections closed")
