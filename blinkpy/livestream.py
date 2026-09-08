"""Handles immis livestream."""

import asyncio
import logging
import urllib.parse
import ssl
from blinkpy import api

_LOGGER = logging.getLogger(__name__)

# IMMI packet msgtypes. Most are handled generically as
# [1-byte msgtype][4-byte sequence][4-byte payload_length][payload], but
# MSGTYPE_AUDIO_CONFIG is a fixed, self-contained 9-byte message (see
# recv()) with no separate payload.
MSGTYPE_VIDEO = 0x00
MSGTYPE_AUDIO = 0x05
MSGTYPE_KEEPALIVE = 0x0A
MSGTYPE_AUDIO_CONFIG = 0x0C
MSGTYPE_LATENCY_STATS = 0x12
MSGTYPE_SESSION_COMMAND = 0x17

# SESSION_COMMAND sub-commands relevant to two-way audio (the remaining
# values control lights/siren/clip-saving and are out of scope here).
SESSION_COMMAND_START_AUDIO = 3
SESSION_COMMAND_STOP_AUDIO = 4

# Outgoing audio frames use their own sequence range, disjoint from the
# keep-alive counter below. The server appears to track sequence numbers
# per-session rather than per-msgtype: reusing small, overlapping sequence
# numbers between msgtype 0x0A and msgtype 0x05 causes the server to reset
# the connection after only a few audio frames.
AUDIO_SEQUENCE_START = 100_000


def build_packet(msgtype, sequence, payload=b""):
    """Build a 9-byte IMMI packet header plus payload."""
    header = bytearray(9)
    header[0] = msgtype
    header[1:5] = sequence.to_bytes(4, byteorder="big")
    header[5:9] = len(payload).to_bytes(4, byteorder="big")
    return bytes(header) + payload


class BlinkLiveStream:
    """Class to initialize individual stream."""

    # Reference: https://github.com/amattu2/blink-liveview-middleware

    def __init__(self, camera, response):
        """Initialize BlinkLiveStream."""
        self.camera = camera
        self.command_id = response["command_id"]
        self.polling_interval = response["polling_interval"]
        self.target = urllib.parse.urlparse(response["server"])
        self.liveview_token = response.get("liveview_token", "")
        self.server = None
        self.clients = []
        self.target_reader = None
        self.target_writer = None

        # Two-way audio (talk) state. Sending audio is opt-in: callers
        # that only want video never touch these. See request_audio()
        # and send_audio().
        self._audio_sequence = AUDIO_SEQUENCE_START
        self.audio_format = None
        self.audio_format_flags = None
        self.audio_format_received = asyncio.Event()

    def add_auth_header_string_field(self, auth_header, field_string, max_length):
        """Add string field to authentication header."""
        _LOGGER.debug("Field string: %s", field_string)
        field_bytes = field_string.encode("utf-8")[:max_length]
        field_bytes = field_bytes.ljust(max_length, b"\x00")
        _LOGGER.debug("Field bytes: %s", field_bytes)
        field_length = len(field_bytes).to_bytes(4, byteorder="big")
        _LOGGER.debug("Field length: %s (%d)", field_length, len(field_length))
        auth_header.extend(field_length)
        auth_header.extend(field_bytes)

    def get_auth_header(self):
        """Get authentication header."""
        auth_header = bytearray()
        serial_max_length = 16
        token_field_max_length = 64
        conn_id_max_length = 16

        # Magic number (4 bytes)
        # fmt: off
        magic_number = [
            0x00, 0x00, 0x00, 0x28, # Magic number (4 bytes)
        ]
        # fmt: on
        auth_header.extend(magic_number)
        # Total packet length: 4 bytes

        # Device Serial field (4-byte length prefix, 16 serial bytes)
        serial = self.camera.serial
        self.add_auth_header_string_field(auth_header, serial, serial_max_length)
        # Total packet length: 24 bytes

        # Client ID field (4 bytes)
        client_id = urllib.parse.parse_qs(self.target.query).get("client_id", [0])[0]
        _LOGGER.debug("Client ID: %s", client_id)
        client_id_field = int(client_id).to_bytes(4, byteorder="big")
        _LOGGER.debug("Client ID field: %s (%d)", client_id_field, len(client_id_field))
        auth_header.extend(client_id_field)
        # Total packet length: 28 bytes

        # Static field (2 bytes)
        # fmt: off
        static_field = [
            0x01, 0x08, # Static value (2 bytes)
        ]
        # fmt: on
        auth_header.extend(static_field)
        # Total packet length: 30 bytes

        # Auth Token field (4-byte length prefix, 64 token bytes)
        self.add_auth_header_string_field(
            auth_header, self.liveview_token, token_field_max_length
        )
        # Total packet length: 98 bytes

        # Connection ID field (4-byte length prefix, 16 connection ID bytes)
        conn_id = self.target.path.split("/")[-1].split("__")[0]
        self.add_auth_header_string_field(auth_header, conn_id, conn_id_max_length)
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

    async def start(self, host="127.0.0.1", port=None):
        """Start the stream."""
        self.server = await asyncio.start_server(self.join, host, port)
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
        await self.auth()
        try:
            await asyncio.gather(self.recv(), self.send(), self.poll())
        except Exception:
            _LOGGER.exception("Error while handling stream")
        finally:
            # Close all connections
            _LOGGER.debug("Streaming was aborted, stopping server")
            self.stop()

    async def auth(self):
        """Connect to and authenticate with the target server."""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.target_reader, self.target_writer = await asyncio.open_connection(
            self.target.hostname, self.target.port, ssl=ssl_context
        )

        auth_header = self.get_auth_header()
        self.target_writer.write(auth_header)
        await self.target_writer.drain()

    async def join(self, client_reader, client_writer):
        """Join client to the stream."""
        # Client connected
        self.clients.append(client_writer)

        try:
            while not client_writer.is_closing():
                # Read data from the client
                data = await client_reader.read(1024)
                if not data:
                    _LOGGER.debug("Client disconnected")
                    break

                # Yield control to the event loop
                await asyncio.sleep(0)
        except ConnectionResetError:
            _LOGGER.debug("Client connection reset")
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

    async def recv(self):
        """Copy data from one reader to multiple writers."""
        try:
            _LOGGER.debug("Starting copy from target to clients")
            while not self.target_reader.at_eof():
                # Read header from the target server
                try:
                    data = await self.target_reader.readexactly(9)
                except asyncio.IncompleteReadError as err:
                    _LOGGER.warning(
                        "Insufficient data for header: %d bytes, expected 9",
                        len(err.partial),
                    )
                    break

                # Handle the 9-byte IMMI protocol header
                msgtype = data[0]

                # MSGTYPE_AUDIO_CONFIG is a fixed, self-contained 9-byte
                # message announcing the AAC-LC audio format (and AEC
                # support) the camera expects for two-way audio - it does
                # not follow the [sequence][payload_length] framing every
                # other msgtype uses, and carries no separate payload.
                if msgtype == MSGTYPE_AUDIO_CONFIG:
                    self.audio_format = int.from_bytes(data[1:5], byteorder="big")
                    self.audio_format_flags = int.from_bytes(data[5:9], byteorder="big")
                    _LOGGER.debug(
                        "Received audio format: 0x%08x (flags=0x%08x)",
                        self.audio_format,
                        self.audio_format_flags,
                    )
                    self.audio_format_received.set()
                    continue

                sequence = int.from_bytes(data[1:5], byteorder="big")
                payload_length = int.from_bytes(data[5:9], byteorder="big")
                _LOGGER.debug(
                    "Received packet: msgtype=%d, sequence=%d, payload_length=%d",
                    msgtype,
                    sequence,
                    payload_length,
                )

                # Skip packets with invalid payload length
                if payload_length <= 0:
                    _LOGGER.debug("Invalid payload length: %d", payload_length)
                    continue

                # Read payload from the target server
                try:
                    data = await self.target_reader.readexactly(payload_length)
                except asyncio.IncompleteReadError as err:
                    _LOGGER.warning(
                        "Insufficient data for payload: %d bytes, expected %d",
                        len(err.partial),
                        payload_length,
                    )
                    break

                # Skip packets other than msgtype 0x00 (regular video stream)
                if msgtype != MSGTYPE_VIDEO:
                    _LOGGER.debug("Skipping unsupported msgtype %d", msgtype)
                    continue

                # Skip video payloads missing 0x47 (transport stream packet start)
                if data[0] != 0x47:
                    _LOGGER.debug("Skipping video payload missing 0x47 at start")
                    continue

                # Send data to all connected clients
                _LOGGER.debug("Sending %d bytes to clients", len(data))
                for writer in self.clients:
                    if not writer.is_closing():
                        writer.write(data)
                        await writer.drain()

                # Yield control to the event loop
                await asyncio.sleep(0)
        except ssl.SSLError as e:
            if e.reason != "APPLICATION_DATA_AFTER_CLOSE_NOTIFY":
                _LOGGER.exception("SSL error while receiving data")
        except Exception:
            _LOGGER.exception("Error while receiving data")
        finally:
            # Abort sending by closing the target writer
            self.target_writer.close()
            _LOGGER.debug("Receiving was aborted, aborting sending")

    async def send(self):
        """Send keep-alive and latency-stats messages to the server."""
        # fmt: off
        latency_stats_payload = bytes([
            0x00, 0x00, 0x00, 0x00, # 4-byte audioAverageLatencyInMS
            0x00, 0x00, 0x00, 0x00, # 4-byte audioMaxLatencyInMS
            0x00, 0x00, # 2-byte audioFramesPresented
            0x00, 0x00, # 2-byte audioFramesDropped
            0x00, 0x00, 0x00, 0x00, # 4-byte videoAverageLatencyInMS
            0x00, 0x00, 0x00, 0x00, # 4-byte videoMaxLatencyInMS
            0x00, 0x00, # 2-byte videoFramesPresented
            0x00, 0x00, # 2-byte videoFramesDropped
        ])
        # fmt: on
        latency_stats_packet = build_packet(
            MSGTYPE_LATENCY_STATS, 1000, latency_stats_payload
        )
        every10s = 0
        sequence = 0
        try:
            while not self.target_writer.is_closing():
                if (every10s % 10) == 0:
                    every10s = 0
                    sequence += 1

                    # Send keep-alive packet to the target server
                    _LOGGER.debug("Sending keep-alive packet")
                    self.target_writer.write(build_packet(MSGTYPE_KEEPALIVE, sequence))
                    await self.target_writer.drain()

                # Send latency-stats packet to the target server
                _LOGGER.debug("Sending latency-stats packet")
                self.target_writer.write(latency_stats_packet)
                await self.target_writer.drain()

                # Yield and sleep for the latency-stats interval
                every10s += 1
                await asyncio.sleep(1)
        except Exception:
            _LOGGER.exception("Error while sending keep-alive or latency-stats")
        finally:
            # Abort receiving by closing the target reader
            self.target_reader.feed_eof()
            _LOGGER.debug("Sending was aborted, aborting receiving")

    async def request_audio(self):
        """Ask the camera to start two-way audio.

        This only sends the SESSION_COMMAND that arms two-way audio on
        the camera side - it does not, by itself, mean the camera is
        ready to receive audio. Await audio_format_received (or poll
        audio_format) before calling send_audio(), since the camera
        replies asynchronously with the AAC-LC format (sample rate,
        channel count) it expects, via a MSGTYPE_AUDIO_CONFIG message.
        """
        await self._send_session_command(SESSION_COMMAND_START_AUDIO)

    async def stop_audio(self):
        """Tell the camera two-way audio is no longer needed."""
        await self._send_session_command(SESSION_COMMAND_STOP_AUDIO)

    async def _send_session_command(self, command_id):
        """Send a SESSION_COMMAND message to the target server."""
        self.target_writer.write(build_packet(MSGTYPE_SESSION_COMMAND, command_id))
        await self.target_writer.drain()

    async def send_audio(self, payload):
        """Send one AAC-LC/ADTS audio frame to the camera's speaker.

        blinkpy does not capture or encode audio - as with video, callers
        are responsible for producing frames in the format the camera
        announced (see audio_format_received / audio_format) and passing
        each ADTS frame to this method individually.
        """
        self._audio_sequence += 1
        self.target_writer.write(
            build_packet(MSGTYPE_AUDIO, self._audio_sequence, payload)
        )
        await self.target_writer.drain()

    async def poll(self):
        """Poll the command API for the stream."""
        try:
            while not self.target_reader.at_eof():
                _LOGGER.debug("Polling command API")
                response = await api.request_command_status(
                    self.camera.sync.blink, self.camera.network_id, self.command_id
                )
                _LOGGER.debug("Polling response: %s", response)

                # Check if the response is successful
                if response.get("status_code", 0) != 908:
                    _LOGGER.error("Polling command API failed: %s", response)
                    break

                # Check if the command is still running
                for commands in response.get("commands", []):
                    if commands.get("id") == self.command_id:
                        _LOGGER.debug("Command %d state found", self.command_id)
                        state_condition = commands.get("state_condition")
                        _LOGGER.debug("Command state condition: %s", state_condition)
                        state_stage = commands.get("state_stage")
                        _LOGGER.debug("Command state stage: %s", state_stage)
                        if state_condition in ("new", "running"):
                            break
                        else:
                            return

                # Sleep and yield for the polling interval
                await asyncio.sleep(self.polling_interval)
        except Exception:
            _LOGGER.exception("Error while polling command API")
        finally:
            _LOGGER.debug("Done polling command API")
            response = await api.request_command_done(
                self.camera.sync.blink, self.camera.network_id, self.command_id
            )
            _LOGGER.debug("Done polling response: %s", response)

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
