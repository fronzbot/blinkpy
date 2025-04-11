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

    def get_auth_frames(self):
        """Get authentication frames."""
        # Frame 1 (unknown)
        frame1 = [
            0x00, 0x00, 0x00, 0x28, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ]

        # Frame 2 (Client ID)
        client_id = urllib.parse.parse_qs(self.target.query).get("client_id")[0]
        frame2 = int(client_id).to_bytes(4, byteorder="big")

        # Frame 3 (unknown)
        frame3 = [
            0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x10,
        ]

        # Frame 4 (Connection ID)
        frame4 = self.target.path.split("/")[-1].split("__")[0].encode("ascii")

        # Frame 5 (unknown)
        frame5 = [
            0x00, 0x00, 0x00, 0x01, 0x0a, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00,
        ]

        return (
            frame1,
            frame2,
            frame3,
            frame4,
            frame5,
        )

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

        for frame in self.get_auth_frames():
            self.target_writer.write(bytearray(frame))
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
        keepalive_frame = [
            0x12, 0x00, 0x00, 0x03, 0xe8, 0x00, 0x00, 0x00, 0x18, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
        ]
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
        _LOGGER.debug("Stopping server, closing connections")
        if self.server and not self.server.is_serving():
            self.server.close()
        if self.target_writer and not self.target_writer.is_closing():
            self.target_writer.close()
        for writer in self.clients:
            if not writer.is_closing():
                writer.close()
