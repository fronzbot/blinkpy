"""Tests for BlinkLiveStream class."""

import ssl
import urllib.parse
from unittest import mock
from unittest import IsolatedAsyncioTestCase

from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import BlinkURLHandler
from blinkpy.sync_module import BlinkSyncModule
from blinkpy.camera import BlinkCameraMini
from blinkpy.livestream import BlinkLiveStream

from .test_api import COMMAND_DONE


@mock.patch("blinkpy.auth.Auth.query", return_value={})
class TestBlinkLiveStream(IsolatedAsyncioTestCase):
    """Test BlinkLiveStream functions in blinkpy."""

    def setUp(self):
        """Set up Blink module."""
        self.blink = Blink(session=mock.Mock())
        self.blink.urls = BlinkURLHandler("test")
        self.blink.sync["test"] = BlinkSyncModule(self.blink, "test", 1234, [])
        self.camera = BlinkCameraMini(self.blink.sync["test"])
        self.camera.name = "test_camera"
        self.camera.camera_id = "5678"
        self.camera.network_id = "1234"
        self.camera.serial = "PONLMKJIHGFED"
        self.blink.sync["test"].cameras["test_camera"] = self.camera

        # Mock response for livestream initialization
        self.livestream_response = {
            "command_id": 987654321,
            "join_available": True,
            "join_state": "available",
            "server": "immis://1.2.3.4:443/ABCDEFGHIJKML__IMDS_1234567812345678?client_id=123456",
            "duration": 300,
            "extended_duration": 5400,
            "continue_interval": 300,
            "continue_warning": 0,
            "polling_interval": 15,
            "submit_logs": True,
            "new_command": True,
            "media_id": None,
            "options": {"poor_connection": False},
            "liveview_token": "abcdefghijklmnopqrstuv",
        }

        self.livestream = BlinkLiveStream(self.camera, self.livestream_response)

        self.command_status_response = {
            "status_code": 908,
            "commands": [
                {
                    "id": self.livestream.command_id,
                    "state_condition": "running",
                    "state_stage": "vs",
                }
            ],
        }

    def tearDown(self):
        """Clean up after test."""
        self.blink = None
        self.camera = None
        self.livestream = None

    def test_livestream_init(self, mock_resp):
        """Test BlinkLiveStream initialization."""
        self.assertEqual(self.livestream.camera, self.camera)
        self.assertEqual(self.livestream.command_id, 987654321)
        self.assertEqual(self.livestream.polling_interval, 15)
        self.assertIsInstance(self.livestream.target, urllib.parse.ParseResult)
        self.assertEqual(self.livestream.target.hostname, "1.2.3.4")
        self.assertEqual(self.livestream.target.port, 443)
        self.assertIsNone(self.livestream.server)
        self.assertEqual(self.livestream.clients, [])
        self.assertIsNone(self.livestream.target_reader)
        self.assertIsNone(self.livestream.target_writer)

    def test_get_auth_header(self, mock_resp):
        """Test authentication header generation."""
        auth_header = self.livestream.get_auth_header()

        # Check that auth header is a bytearray
        self.assertIsInstance(auth_header, bytearray)

        # Check expected length (122 bytes according to comments in code)
        self.assertEqual(len(auth_header), 122)

        # Check magic number at start (4 bytes: 0x00, 0x00, 0x00, 0x28)
        self.assertEqual(auth_header[0:4], bytearray([0x00, 0x00, 0x00, 0x28]))

        # Check camera serial length field at position 4-7
        expected_serial_length = (16).to_bytes(4, byteorder="big")
        self.assertEqual(auth_header[4:8], expected_serial_length)

        # Check camera serial at position 8-23
        expected_serial = b"PONLMKJIHGFED\x00\x00\x00"
        self.assertEqual(auth_header[8:24], expected_serial)

        # Check client ID field at position 24-27
        expected_client_id = (123456).to_bytes(4, byteorder="big")
        self.assertEqual(auth_header[24:28], expected_client_id)

        # Check connection ID length field at position 98-101
        expected_connection_id_length = (16).to_bytes(4, byteorder="big")
        self.assertEqual(auth_header[98:102], expected_connection_id_length)

        # Check connection ID at position 102-117
        expected_connection_id = b"ABCDEFGHIJKML\x00\x00\x00"
        self.assertEqual(auth_header[102:118], expected_connection_id)

        # Check static trailer at end (4 bytes: 0x00, 0x00, 0x00, 0x01)
        self.assertEqual(auth_header[-4:], bytearray([0x00, 0x00, 0x00, 0x01]))

    async def test_start(self, mock_resp):
        """Test starting the server."""
        with mock.patch("asyncio.start_server") as mock_start_server:
            mock_server = mock.Mock()
            mock_start_server.return_value = mock_server

            result = await self.livestream.start()

            mock_start_server.assert_called_once_with(
                self.livestream.join, "127.0.0.1", None
            )
            self.assertEqual(result, mock_server)
            self.assertEqual(self.livestream.server, mock_server)

    def test_socket_property(self, mock_resp):
        """Test socket property."""
        mock_socket = mock.Mock()
        mock_server = mock.Mock()
        mock_server.sockets = [mock_socket]
        self.livestream.server = mock_server

        self.assertEqual(self.livestream.socket, mock_socket)

    def test_url_property(self, mock_resp):
        """Test URL property."""
        mock_socket = mock.Mock()
        mock_socket.getsockname.return_value = ("127.0.0.1", 8080)
        mock_server = mock.Mock()
        mock_server.sockets = [mock_socket]
        self.livestream.server = mock_server

        expected_url = "tcp://127.0.0.1:8080"
        self.assertEqual(self.livestream.url, expected_url)

    def test_is_serving_property(self, mock_resp):
        """Test is_serving property."""
        # Test when server is None
        self.livestream.server = None
        self.assertFalse(self.livestream.is_serving)

        # Test when server exists and is serving
        mock_server = mock.Mock()
        mock_server.is_serving.return_value = True
        self.livestream.server = mock_server
        self.assertTrue(self.livestream.is_serving)

        # Test when server exists but is not serving
        mock_server.is_serving.return_value = False
        self.assertFalse(self.livestream.is_serving)

    @mock.patch("asyncio.open_connection")
    @mock.patch("ssl.SSLContext")
    @mock.patch("blinkpy.api.request_command_status")
    async def test_feed_success(
        self, mock_command_status, mock_ssl_context, mock_open_connection, mock_resp
    ):
        """Test successful feed method."""
        # Mock SSL context
        mock_ssl = mock.Mock()
        mock_ssl_context.return_value = mock_ssl

        # Mock connection
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        # Mock successful command status
        mock_command_status.return_value = self.command_status_response

        # Mock coroutines to avoid actual execution
        with (
            mock.patch.object(self.livestream, "recv", new_callable=mock.AsyncMock),
            mock.patch.object(self.livestream, "send", new_callable=mock.AsyncMock),
            mock.patch.object(self.livestream, "poll", new_callable=mock.AsyncMock),
            mock.patch.object(self.livestream, "stop") as mock_stop,
        ):
            await self.livestream.feed()

            # Verify SSL context setup
            mock_ssl_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
            self.assertFalse(mock_ssl.check_hostname)
            self.assertEqual(mock_ssl.verify_mode, ssl.CERT_NONE)

            # Verify connection was opened
            mock_open_connection.assert_called_once_with(
                self.livestream.target.hostname,
                self.livestream.target.port,
                ssl=mock_ssl,
            )

            # Verify auth header was sent
            mock_writer.write.assert_called_once()
            mock_writer.drain.assert_called_once()

            # Verify stop was called
            mock_stop.assert_called_once()

    @mock.patch("asyncio.open_connection")
    @mock.patch("ssl.SSLContext")
    @mock.patch("blinkpy.api.request_command_status")
    async def test_feed_failure(
        self, mock_command_status, mock_ssl_context, mock_open_connection, mock_resp
    ):
        """Test successful feed method."""
        # Mock SSL context
        mock_ssl = mock.Mock()
        mock_ssl_context.return_value = mock_ssl

        # Mock connection
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        # Mock successful command status
        mock_command_status.return_value = self.command_status_response

        # Mock coroutines to avoid actual execution
        with (
            mock.patch("logging.Logger.exception") as mock_logger,
            mock.patch("asyncio.gather", new_callable=mock.AsyncMock) as mock_gather,
            mock.patch.object(self.livestream, "recv", new_callable=mock.Mock),
            mock.patch.object(self.livestream, "send", new_callable=mock.Mock),
            mock.patch.object(self.livestream, "poll", new_callable=mock.Mock),
            mock.patch.object(self.livestream, "stop") as mock_stop,
        ):
            # Simulate an exception in the gather call
            mock_gather.side_effect = Exception("Test exception")
            await self.livestream.feed()

            # Verify exception was logged
            mock_logger.assert_called_once()

            # Verify stop was called
            mock_stop.assert_called_once()

    async def test_join_client_connect_disconnect(self, mock_resp):
        """Test client joining and disconnecting."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock client reading data then disconnecting
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [b"test_data", b""]
        mock_writer.is_closing.return_value = False

        # Start the join coroutine
        await self.livestream.join(mock_reader, mock_writer)

        # Verify client was added and removed
        self.assertEqual(len(self.livestream.clients), 0)
        mock_writer.close.assert_called_once()

    async def test_join_connection_reset(self, mock_resp):
        """Test client connection reset during join."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock connection reset error
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = ConnectionResetError()
        mock_writer.is_closing.return_value = False

        with mock.patch.object(self.livestream, "stop") as mock_stop:
            await self.livestream.join(mock_reader, mock_writer)

            # Verify client was removed and stop was called
            self.assertEqual(len(self.livestream.clients), 0)
            mock_writer.close.assert_called_once()
            mock_stop.assert_called_once()

    async def test_join_general_exception_logging(self, mock_resp):
        """Test general exception logging in join method."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock general exception (not ConnectionResetError)
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = ValueError("Test join exception")
        mock_writer.is_closing.return_value = False

        with (
            mock.patch("logging.Logger.exception") as mock_logger,
            mock.patch.object(self.livestream, "stop") as mock_stop,
        ):
            await self.livestream.join(mock_reader, mock_writer)

            # Verify exception was logged
            mock_logger.assert_called_once_with("Error while handling client")

            # Verify client was removed and stop was called
            self.assertEqual(len(self.livestream.clients), 0)
            mock_writer.close.assert_called_once()
            mock_stop.assert_called_once()

    async def test_recv_valid_packet(self, mock_resp):
        """Test receiving valid video packets."""
        mock_reader = mock.Mock()
        mock_client = mock.Mock()

        # Mock valid IMMI protocol header and payload
        header_data = bytearray(
            [
                0x00,  # msgtype (video stream)
                0x00,
                0x00,
                0x00,
                0x01,  # sequence
                0x00,
                0x00,
                0x00,
                0xBC,  # payload_length (188 bytes)
            ]
        )

        # Mock payload starting with 0x47 (transport stream packet start)
        payload_data = bytearray([0x47] + [0x00] * 187)  # 188 bytes total

        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [header_data, payload_data, b""]
        mock_reader.at_eof.side_effect = [False, False, True]
        mock_client.is_closing.return_value = False
        mock_client.write = mock.Mock()
        mock_client.drain = mock.AsyncMock()

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock.Mock()
        self.livestream.clients = [mock_client]

        await self.livestream.recv()

        # Verify data was written to client
        mock_client.write.assert_called_with(payload_data)
        mock_client.drain.assert_called()

    async def test_recv_invalid_msgtype(self, mock_resp):
        """Test receiving packet with invalid message type."""
        mock_reader = mock.Mock()
        mock_client = mock.Mock()

        # Mock header with invalid msgtype (not 0x00)
        header_data_invalid = bytearray(
            [
                0x01,  # invalid msgtype
                0x00,
                0x00,
                0x00,
                0x01,  # sequence
                0x00,
                0x00,
                0x00,
                0xBC,  # payload_length (188 bytes)
            ]
        )

        payload_data = bytearray([0x47] + [0x00] * 187)  # 188 bytes total

        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [header_data_invalid, payload_data, b""]
        mock_reader.at_eof.side_effect = [False, False, True]

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock.Mock()
        self.livestream.clients = [mock_client]

        await self.livestream.recv()

        # Verify data was not written to client (invalid msgtype)
        mock_client.write.assert_not_called()

    async def test_recv_incomplete_header(self, mock_resp):
        """Test receiving packet with incomplete header."""
        mock_reader = mock.Mock()
        mock_client = mock.Mock()

        # Simulate reading incomplete header
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [b"short", b""]
        mock_reader.at_eof.side_effect = [False, True]

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock.Mock()
        self.livestream.clients = [mock_client]

        # Should not raise exception, just log a warning message
        with mock.patch("logging.Logger.warning") as mock_logger:
            await self.livestream.recv()

            # Verify that a warning message was logged
            mock_logger.assert_called_once()

        # Verify no data was written to client (incomplete header)
        mock_client.write.assert_not_called()

    async def test_recv_empty_payload_skipped(self, mock_resp):
        """Test skipping packet with empty payload."""
        mock_reader = mock.Mock()
        mock_client = mock.Mock()

        # Mock valid IMMI protocol header and empty payload
        header_data_empty = bytearray(
            [
                0x00,  # msgtype (video stream)
                0x00,
                0x00,
                0x00,
                0x01,  # sequence
                0x00,
                0x00,
                0x00,
                0x00,  # payload_length (0 bytes)
            ]
        )

        # Mock valid IMMI protocol header and payload
        header_data = bytearray(
            [
                0x00,  # msgtype (video stream)
                0x00,
                0x00,
                0x00,
                0x01,  # sequence
                0x00,
                0x00,
                0x00,
                0xBC,  # payload_length (188 bytes)
            ]
        )

        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [header_data_empty, header_data, b"short", b""]
        mock_reader.at_eof.side_effect = [False, False, True]

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock.Mock()
        self.livestream.clients = [mock_client]

        # Should not raise exception, just log a warning message
        with mock.patch("logging.Logger.warning") as mock_logger:
            await self.livestream.recv()

            # Verify that a warning message was logged
            mock_logger.assert_called_once()

        # Verify that the first payload read was skipped (empty payload)
        self.assertEqual(mock_reader.read.call_count, 3)  # odd number of reads

        # Verify no data was written to client (incomplete header)
        mock_client.write.assert_not_called()

    async def test_recv_invalid_stream_marker(self, mock_resp):
        """Test receiving invalid video packets."""
        mock_reader = mock.Mock()
        mock_client = mock.Mock()

        # Mock valid IMMI protocol header and payload
        header_data = bytearray(
            [
                0x00,  # msgtype (video stream)
                0x00,
                0x00,
                0x00,
                0x01,  # sequence
                0x00,
                0x00,
                0x00,
                0xBC,  # payload_length (188 bytes)
            ]
        )

        # Mock payload starting with 0x42 (invalid transport stream packet start)
        payload_data = bytearray([0x42] + [0x00] * 187)  # 188 bytes total

        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = [header_data, payload_data, b""]
        mock_reader.at_eof.side_effect = [False, False, True]
        mock_client.is_closing.return_value = False
        mock_client.write = mock.Mock()
        mock_client.drain = mock.AsyncMock()

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock.Mock()
        self.livestream.clients = [mock_client]

        await self.livestream.recv()

        # Verify no data was written to client (incomplete header)
        mock_client.write.assert_not_called()

    async def test_send_keepalive_and_latency(self, mock_resp):
        """Test sending keep-alive and latency-stats packets."""
        mock_writer = mock.Mock()

        # Stop after 2 iterations
        mock_writer.is_closing.side_effect = [False, False, True]
        mock_writer.write = mock.Mock()
        mock_writer.drain = mock.AsyncMock()

        self.livestream.target_reader = mock.Mock()
        self.livestream.target_writer = mock_writer

        with mock.patch("asyncio.sleep", new_callable=mock.AsyncMock):
            await self.livestream.send()

        # Verify multiple writes occurred (keep-alive and latency-stats)
        self.assertGreater(mock_writer.write.call_count, 1)
        self.assertGreater(mock_writer.drain.call_count, 1)

    @mock.patch("blinkpy.api.request_command_status")
    @mock.patch("blinkpy.api.request_command_done")
    async def test_poll(self, mock_command_done, mock_command_status, mock_resp):
        """Test polling command API."""
        mock_reader = mock.Mock()
        mock_reader.at_eof.side_effect = [False, True]  # Stop after 1 iteration

        mock_command_status.return_value = self.command_status_response
        mock_command_done.return_value = COMMAND_DONE

        self.livestream.target_reader = mock_reader

        with mock.patch("asyncio.sleep", new_callable=mock.AsyncMock):
            await self.livestream.poll()

        # Verify reader was read until EOF
        self.assertGreater(mock_reader.at_eof.call_count, 1)

        # Verify command status was polled
        mock_command_status.assert_called_with(
            self.camera.sync.blink, self.camera.network_id, self.livestream.command_id
        )

        # Verify command done was called
        mock_command_done.assert_called_with(
            self.camera.sync.blink, self.camera.network_id, self.livestream.command_id
        )

    def test_stop(self, mock_resp):
        """Test stopping the livestream."""
        # Mock server and connections
        mock_server = mock.Mock()
        mock_server.is_serving.return_value = True
        mock_target_writer = mock.Mock()
        mock_target_writer.is_closing.return_value = False
        mock_client1 = mock.Mock()
        mock_client1.is_closing.return_value = False
        mock_client2 = mock.Mock()
        mock_client2.is_closing.return_value = False

        self.livestream.server = mock_server
        self.livestream.target_writer = mock_target_writer
        self.livestream.clients = [mock_client1, mock_client2]

        self.livestream.stop()

        # Verify server was closed
        mock_server.close.assert_called_once()

        # Verify target writer was closed
        mock_target_writer.close.assert_called_once()

        # Verify all clients were closed
        mock_client1.close.assert_called_once()
        mock_client2.close.assert_called_once()

    def test_server_url_parsing(self, mock_resp):
        """Test client ID parsing from URL query parameters."""
        # Test with different client ID
        test_response = {
            **self.livestream_response,
            "server": "immis://1.2.3.4:443/ABCDEFGH__IMDS_1234?client_id=999888",
        }

        test_livestream = BlinkLiveStream(self.camera, test_response)
        auth_header = test_livestream.get_auth_header()

        # Check value of client ID field at position 24-28
        expected_client_id = (999888).to_bytes(4, byteorder="big")
        self.assertEqual(auth_header[24:28], expected_client_id)

        # Check value of connection ID length field at position 98-102
        expected_connection_id_length = (16).to_bytes(4, byteorder="big")
        self.assertEqual(auth_header[98:102], expected_connection_id_length)

        # Check value of connection ID at position 102-118
        expected_connection_id = b"ABCDEFGH" + b"\x00" * 8  # Ensure it is 16 bytes
        self.assertEqual(auth_header[102:118], expected_connection_id)

    async def test_recv_ssl_error(self, mock_resp):
        """Test handling SSL errors during receive."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock SSL error
        ssl_error = ssl.SSLError()
        ssl_error.reason = "APPLICATION_DATA_AFTER_CLOSE_NOTIFY"
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = ssl_error
        mock_reader.at_eof.return_value = False

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock_writer
        self.livestream.clients = []

        # Should not raise exception for this specific SSL error
        await self.livestream.recv()

        # Verify target writer was closed
        mock_writer.close.assert_called_once()

    async def test_recv_ssl_error_other_reason(self, mock_resp):
        """Test SSL error handling with other reasons in recv."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock SSL error with different reason
        ssl_error = ssl.SSLError()
        ssl_error.reason = "SOME_OTHER_SSL_ERROR"
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = ssl_error
        mock_reader.at_eof.return_value = False

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock_writer
        self.livestream.clients = []

        with mock.patch("logging.Logger.exception") as mock_logger:
            # Should not raise exception for this specific SSL error
            await self.livestream.recv()

            # Verify exception was logged for non-ignored SSL errors
            mock_logger.assert_called_once_with("SSL error while receiving data")

        # Verify target writer was closed
        mock_writer.close.assert_called_once()

    async def test_recv_exception_logging(self, mock_resp):
        """Test exception logging in recv method."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock general exception
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = Exception("Test exception")
        mock_reader.at_eof.return_value = False

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock_writer
        self.livestream.clients = []

        with mock.patch("logging.Logger.exception") as mock_logger:
            await self.livestream.recv()

            # Verify exception was logged
            mock_logger.assert_called_once_with("Error while receiving data")

        # Verify target writer was closed
        mock_writer.close.assert_called_once()

    async def test_recv_timeout_exception(self, mock_resp):
        """Test timeout exception handling in recv method."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock asyncio timeout exception
        mock_reader.read = mock.AsyncMock()
        mock_reader.read.side_effect = TimeoutError()
        mock_reader.at_eof.return_value = False

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock_writer
        self.livestream.clients = []

        with mock.patch("logging.Logger.exception") as mock_logger:
            await self.livestream.recv()

            # Verify exception was logged
            mock_logger.assert_called_once_with("Error while receiving data")

        # Verify target writer was closed
        mock_writer.close.assert_called_once()

    async def test_send_exception_logging(self, mock_resp):
        """Test exception logging in send method."""
        mock_writer = mock.Mock()

        # Mock exception during send
        mock_writer.is_closing.return_value = False
        mock_writer.write = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        mock_writer.drain.side_effect = Exception("Test send exception")

        self.livestream.target_reader = mock.Mock()
        self.livestream.target_writer = mock_writer

        with mock.patch("logging.Logger.exception") as mock_logger:
            await self.livestream.send()

            # Verify exception was logged
            mock_logger.assert_called_once_with(
                "Error while sending keep-alive or latency-stats"
            )

    async def test_send_writer_closing_exception(self, mock_resp):
        """Test exception when writer is closing during send."""
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()

        # Mock exception when checking if writer is closing
        mock_writer.is_closing.side_effect = Exception("Writer check exception")

        self.livestream.target_reader = mock_reader
        self.livestream.target_writer = mock_writer

        with mock.patch("logging.Logger.exception") as mock_logger:
            await self.livestream.send()

            # Verify exception was logged
            mock_logger.assert_called_once_with(
                "Error while sending keep-alive or latency-stats"
            )

    @mock.patch("blinkpy.api.request_command_status")
    async def test_poll_exception_logging(self, mock_command_status, mock_resp):
        """Test exception logging in poll method."""
        mock_reader = mock.Mock()
        mock_reader.at_eof.return_value = False

        # Mock exception in command status request
        mock_command_status.side_effect = Exception("Test poll exception")

        self.livestream.target_reader = mock_reader

        with (
            mock.patch("logging.Logger.exception") as mock_logger,
            mock.patch(
                "blinkpy.api.request_command_done", new_callable=mock.AsyncMock
            ) as mock_command_done,
        ):
            await self.livestream.poll()

            # Verify exception was logged
            mock_logger.assert_called_once_with("Error while polling command API")

            # Verify command done was called since status failed
            mock_command_done.assert_called_once()

    @mock.patch("blinkpy.api.request_command_status")
    @mock.patch("blinkpy.api.request_command_done")
    async def test_poll_command_done(
        self, mock_command_done, mock_command_status, mock_resp
    ):
        """Test exception handling in poll when command_done fails."""
        mock_reader = mock.Mock()
        mock_reader.at_eof.side_effect = [False, True]  # Exit after one iteration

        # Mock successful command status
        response = self.command_status_response.copy()
        response["commands"][0] = response["commands"][0].copy()
        response["commands"][0]["state_condition"] = "error"
        mock_command_status.return_value = response

        self.livestream.target_reader = mock_reader

        await self.livestream.poll()

        # Verify command status was polled
        mock_command_status.assert_called_with(
            self.camera.sync.blink, self.camera.network_id, self.livestream.command_id
        )

        # Verify command done was called
        mock_command_done.assert_called_with(
            self.camera.sync.blink, self.camera.network_id, self.livestream.command_id
        )

    @mock.patch("blinkpy.api.request_command_status")
    @mock.patch("blinkpy.api.request_command_done")
    async def test_poll_command_done_exception(
        self, mock_command_done, mock_command_status, mock_resp
    ):
        """Test exception handling in poll when command_done fails."""
        mock_reader = mock.Mock()
        mock_reader.at_eof.side_effect = [False, True]  # Exit after one iteration

        # Mock successful command status
        mock_command_status.return_value = self.command_status_response.copy()
        mock_command_status.return_value["status_code"] = 1337
        # Mock exception in command done
        mock_command_done.side_effect = Exception("Command done exception")

        self.livestream.target_reader = mock_reader

        with (
            mock.patch("asyncio.sleep", new_callable=mock.AsyncMock),
            self.assertRaises(Exception),
        ):
            await self.livestream.poll()
