"""Handles immis livestream"""
import asyncio
import urllib.parse
import ssl

class BlinkStream:
    """Class to initialize individual stream."""

    # Reference: https://github.com/amattu2/blink-liveview-middleware

    def __init__(self, camera, response):
        """Initialize BlinkStream."""
        self.camera = camera
        self.command_id = response["command_id"]
        self.polling_interval = response["polling_interval"]
        self.target = urllib.parse.urlparse(response["server"])
        self.clients = []

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
        self.server = await asyncio.start_server(self.proxy, "127.0.0.1",
                                                 start_serving=False)
        return self.server.sockets[0]

    async def stream(self):
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
            await asyncio.gather(self.copy(), self.ping(), self.server.serve_forever())
        except asyncio.CancelledError as e:
            raise RuntimeWarning from e
        finally:
            await self.stop()

    async def proxy(self, client_reader, client_writer):
        """Proxy the stream."""
        self.clients.append(client_writer)
        while not client_writer.is_closing():
            data = await client_reader.read(1024)
            if not data:
                break

        self.clients.remove(client_writer)
        if not client_writer.is_closing():
            client_writer.close()

    async def copy(self):
        """Copy data from one reader to multiple writers."""
        try:
            while True:
                data = await self.target_reader.read(1024)
                if not data:
                    return
                for writer in self.clients:
                    if not writer.is_closing():
                        writer.write(data)
                        await writer.drain()
                await asyncio.sleep(0)
        finally:
            self.server.close()
            self.target_writer.close()
            for writer in self.clients:
                if not writer.is_closing():
                    writer.close()

    async def ping(self):
        """Send keep-alive messages to the server."""
        keepalive_frame = [
            0x12, 0x00, 0x00, 0x03, 0xe8, 0x00, 0x00, 0x00, 0x18, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
        ]
        while not self.target_writer.is_closing():
            await asyncio.sleep(self.polling_interval)
            self.target_writer.write(bytearray(keepalive_frame))
            await self.target_writer.drain()

    async def stop(self):
        """Stop the stream."""
        # Close the server and any open connections
        self.server.close()
        self.target_writer.close()
        await self.server.wait_closed()
