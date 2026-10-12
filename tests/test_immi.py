"""Tests for the IMMI helpers module."""

import struct
from unittest import TestCase

from blinkpy.helpers.immi import (
    ACCESSORY_MESSAGE,
    HEADER_SIZE,
    INLINE_COMMAND,
    AccessoryMessage,
    ImmiCommand,
    MotorStatus,
    PanTiltLimits,
    PanTiltPosition,
    build_go_home,
    build_move,
    build_pan_overview,
    build_set_home,
    build_stop,
    decode_header,
    encode_message,
    move_payload,
    parse_accessory_message,
    parse_position,
)

# Payloads captured from a live session on a Mini with the pan/tilt mount attached.
# Layout is a four byte device counter followed by signed pan/tilt degrees and a status.
CAPTURED_POSITION_IDLE = bytes.fromhex("0164509b71b500")
CAPTURED_POSITION_MOVING = bytes.fromhex("017dd06e75b510")
CAPTURED_POSITION_ARRIVED = bytes.fromhex("017e290877b500")
CAPTURED_POSITION_RETURNED = bytes.fromhex("018939ec71b500")
CAPTURED_LIMITS = bytes.fromhex("06ae77f1")


class TestIMMIEncoding(TestCase):
    """Test message construction."""

    def test_encode_message_layout(self):
        """Test the nine byte header is msgtype, identifier then length."""
        message = encode_message(INLINE_COMMAND, ImmiCommand.MOVE, b"abc")
        self.assertEqual(message[0], INLINE_COMMAND)
        self.assertEqual(message[1:5], b"\x00\x00\x00\x03")
        self.assertEqual(message[5:9], b"\x00\x00\x00\x03")
        self.assertEqual(message[HEADER_SIZE:], b"abc")

    def test_encode_message_defaults_to_empty_payload(self):
        """Test a command without a payload still produces a full header."""
        message = encode_message(INLINE_COMMAND, ImmiCommand.STOP)
        self.assertEqual(len(message), HEADER_SIZE)
        self.assertEqual(message[5:9], b"\x00\x00\x00\x00")

    def test_move_payload_is_seven_bytes(self):
        """Test the move payload matches the layout the app builds."""
        self.assertEqual(move_payload(119, 0), bytes([0, 0, 0, 0, 119, 0, 0]))

    def test_build_move_matches_captured_angles(self):
        """Test a move to pan 119 tilt -75 reproduces the bytes seen on the wire."""
        # 0x14 = INLINE_COMMAND, identifier 3 = move, length 7, then the angle payload.
        self.assertEqual(
            build_move(119, -75),
            bytes.fromhex("1400000003000000070000000077b500"),
        )

    def test_build_move_encodes_negative_angles(self):
        """Test negative angles are stored as signed bytes."""
        self.assertEqual(move_payload(-75, 0)[4], 0xB5)

    def test_build_stop_has_no_payload(self):
        """Test stop carries the command id as the identifier of an empty message."""
        # 0x14 = INLINE_COMMAND, identifier 4 = stop, length 0.
        self.assertEqual(build_stop(), bytes.fromhex("140000000400000000"))

    def test_build_go_home_set_home_and_overview(self):
        """Test the remaining payload-free commands use their own identifiers."""
        self.assertEqual(build_go_home(), bytes.fromhex("140000000500000000"))
        self.assertEqual(build_set_home(), bytes.fromhex("140000000600000000"))
        self.assertEqual(build_pan_overview(), bytes.fromhex("140000000700000000"))

    def test_angle_must_be_a_byte(self):
        """Test out of range angles are rejected rather than silently wrapped."""
        for angle in (128, -129, 1000):
            with self.assertRaises(ValueError):
                build_move(angle, 0)

    def test_angle_must_be_an_integer(self):
        """Test non integer angles raise a TypeError."""
        with self.assertRaises(TypeError):
            build_move(10.5, 0)


class TestIMMIDecoding(TestCase):
    """Test message parsing."""

    def test_decode_header_roundtrip(self):
        """Test a header encoded by this module decodes back to its parts."""
        message = encode_message(ACCESSORY_MESSAGE, AccessoryMessage.LIMITS, b"1234")
        self.assertEqual(
            decode_header(message[:HEADER_SIZE]),
            (ACCESSORY_MESSAGE, AccessoryMessage.LIMITS, 4),
        )

    def test_decode_header_rejects_wrong_size(self):
        """Test a short header raises rather than reading garbage."""
        with self.assertRaises(ValueError):
            decode_header(b"\x15\x00\x00")

    def test_parse_captured_idle_position(self):
        """Test a captured idle position decodes to the expected angle."""
        position = parse_position(CAPTURED_POSITION_IDLE)
        self.assertIsInstance(position, PanTiltPosition)
        self.assertEqual((position.pan, position.tilt), (113, -75))
        self.assertEqual(position.status, MotorStatus.IDLE)
        self.assertFalse(position.is_moving)

    def test_parse_captured_moving_position(self):
        """Test a captured in-motion report decodes as moving."""
        position = parse_position(CAPTURED_POSITION_MOVING)
        self.assertEqual((position.pan, position.tilt), (117, -75))
        self.assertEqual(position.status, MotorStatus.MOVING)
        self.assertTrue(position.is_moving)

    def test_parse_captured_move_completion(self):
        """Test the reports either side of a six degree move."""
        arrived = parse_position(CAPTURED_POSITION_ARRIVED)
        returned = parse_position(CAPTURED_POSITION_RETURNED)
        self.assertEqual(arrived.pan, 119)
        self.assertEqual(returned.pan, 113)
        self.assertFalse(arrived.is_moving)
        self.assertFalse(returned.is_moving)

    def test_parse_position_keeps_device_counter(self):
        """Test the leading counter is exposed rather than discarded."""
        self.assertEqual(parse_position(CAPTURED_POSITION_IDLE).counter, 0x0164509B)

    def test_parse_position_rejects_short_payload(self):
        """Test a truncated position payload raises."""
        with self.assertRaises(ValueError):
            parse_position(b"\x00\x00\x00")

    def test_parse_accessory_limits(self):
        """Test limits decode to the raw four bytes the device sent."""
        limits = parse_accessory_message(AccessoryMessage.LIMITS, CAPTURED_LIMITS)
        self.assertIsInstance(limits, PanTiltLimits)
        self.assertEqual(limits.raw, CAPTURED_LIMITS)

    def test_parse_accessory_home_position(self):
        """Test HOME_POSITION shares the position layout."""
        position = parse_accessory_message(
            AccessoryMessage.HOME_POSITION, CAPTURED_POSITION_IDLE
        )
        self.assertEqual((position.pan, position.tilt), (113, -75))

    def test_parse_accessory_ignores_unmodelled_messages(self):
        """Test lights and siren messages return None instead of guessing."""
        for identifier in (
            AccessoryMessage.LIGHTS_ON,
            AccessoryMessage.SIREN_OFF,
            AccessoryMessage.PAN_OVERVIEW_COMPLETE,
        ):
            self.assertIsNone(parse_accessory_message(identifier, b""))

    def test_move_frame_roundtrip(self):
        """Test a built move frame parses back to the angle that was requested."""
        message = build_move(-30, 45)
        msgtype, identifier, length = decode_header(message[:HEADER_SIZE])
        self.assertEqual(msgtype, INLINE_COMMAND)
        self.assertEqual(identifier, ImmiCommand.MOVE)
        self.assertEqual(length, 7)
        self.assertEqual(
            struct.unpack("b", message[HEADER_SIZE + 4 : HEADER_SIZE + 5])[0], -30
        )
