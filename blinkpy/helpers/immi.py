"""Helpers for the IMMI media transport used by Blink LiveView.

Aside from video, the IMMI stream carries a command channel. A camera with a pan/tilt
mount attached is driven over it, and the mount reports its position back on the same
session, so control can be closed-loop.

Every layout below was recovered from the official Android app and verified against live
camera traffic on a Mini with the pan/tilt mount. See ``PROTOCOL.md`` for the write-up.

This module is deliberately pure: it encodes and decodes frames and holds the protocol
constants. Reading and writing the stream belongs to the caller.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Final

# Message types (the first byte of the IMMI header).
VIDEO: Final = 0x00
KEEPALIVE: Final = 0x0A
LATENCY_STATS: Final = 0x12
INLINE_COMMAND: Final = 0x14
ACCESSORY_MESSAGE: Final = 0x15
SESSION_COMMAND: Final = 0x17
SESSION_MESSAGE: Final = 0x18

# IMMI header: msgtype (1 byte), identifier (4 bytes), payload length (4 bytes).
HEADER_FORMAT: Final = ">BII"
HEADER_SIZE: Final = struct.calcsize(HEADER_FORMAT)

# Pan/tilt commands are sent as an INLINE_COMMAND whose identifier is the command id.
MOVE_PAYLOAD_SIZE: Final = 7
ANGLE_MINIMUM: Final = -128
ANGLE_MAXIMUM: Final = 127


class ImmiCommand(IntEnum):
    """Command identifiers sent to the device as INLINE_COMMAND messages."""

    MOVE = 3
    STOP = 4
    GO_HOME = 5
    SET_HOME = 6
    PAN_OVERVIEW = 7


class AccessoryMessage(IntEnum):
    """Identifiers the device uses when reporting accessory state."""

    LIGHTS_OFF = 0
    LIGHTS_ON = 1
    POSITION = 2
    HOME_POSITION = 3
    LIMITS = 4
    PAN_OVERVIEW_COMPLETE = 5
    SIREN_OFF = 6
    SIREN_ON = 7


class MotorStatus(IntEnum):
    """Motor state reported alongside a position."""

    IDLE = 0x00
    MOVING = 0x10


@dataclass(frozen=True)
class PanTiltPosition:
    """Where the mount is pointing, as reported by the device."""

    pan: int
    tilt: int
    status: int
    counter: int

    @property
    def is_moving(self) -> bool:
        """Return True while the mount reports motion in progress."""
        return self.status == MotorStatus.MOVING


@dataclass(frozen=True)
class PanTiltLimits:
    """Raw travel limits reported by the mount.

    The device sends four unsigned bytes and the app maps them to a four argument limits
    object. The meaning of each byte is not yet determined, so they are exposed as-is.
    """

    raw: bytes


def encode_message(msgtype: int, identifier: int, payload: bytes = b"") -> bytes:
    """Return a complete IMMI message for the given type, identifier and payload."""
    return struct.pack(HEADER_FORMAT, msgtype, identifier, len(payload)) + payload


def decode_header(header: bytes) -> tuple[int, int, int]:
    """Return ``(msgtype, identifier, payload_length)`` from a 9 byte IMMI header."""
    if len(header) != HEADER_SIZE:
        raise ValueError(f"header must be {HEADER_SIZE} bytes, got {len(header)}")
    return struct.unpack(HEADER_FORMAT, header)


def _angle_byte(angle: int) -> int:
    """Validate an angle and return it as a single signed byte value."""
    if not isinstance(angle, int):
        raise TypeError(f"angle must be an int, got {type(angle).__name__}")
    if not ANGLE_MINIMUM <= angle <= ANGLE_MAXIMUM:
        raise ValueError(
            f"angle must be between {ANGLE_MINIMUM} and {ANGLE_MAXIMUM}, got {angle}"
        )
    return angle & 0xFF


def move_payload(pan: int, tilt: int) -> bytes:
    """Return the payload that moves the mount to an absolute angle.

    The leading four bytes are zero in the app's own encoder; the device fills the
    equivalent field with a counter of its own when it reports a position.
    """
    return bytes([0, 0, 0, 0, _angle_byte(pan), _angle_byte(tilt), 0])


def build_move(pan: int, tilt: int) -> bytes:
    """Return a complete message that moves the mount to an absolute angle."""
    return encode_message(INLINE_COMMAND, ImmiCommand.MOVE, move_payload(pan, tilt))


def build_stop() -> bytes:
    """Return a complete message that stops the mount's motors."""
    return encode_message(INLINE_COMMAND, ImmiCommand.STOP)


def build_go_home() -> bytes:
    """Return a complete message that sends the mount to its saved home position."""
    return encode_message(INLINE_COMMAND, ImmiCommand.GO_HOME)


def build_set_home() -> bytes:
    """Return a complete message that saves the current position as home."""
    return encode_message(INLINE_COMMAND, ImmiCommand.SET_HOME)


def build_pan_overview() -> bytes:
    """Return a complete message that starts a 360 degree pan overview."""
    return encode_message(INLINE_COMMAND, ImmiCommand.PAN_OVERVIEW)


def parse_position(payload: bytes) -> PanTiltPosition:
    """Return the position carried by a POSITION or HOME_POSITION accessory message."""
    if len(payload) < MOVE_PAYLOAD_SIZE:
        raise ValueError(
            f"position payload must be at least {MOVE_PAYLOAD_SIZE} bytes, "
            f"got {len(payload)}"
        )
    counter, pan, tilt, status = struct.unpack(">IBBB", payload[:MOVE_PAYLOAD_SIZE])
    return PanTiltPosition(
        pan=struct.unpack("b", bytes([pan]))[0],
        tilt=struct.unpack("b", bytes([tilt]))[0],
        status=status,
        counter=counter,
    )


def parse_accessory_message(
    identifier: int, payload: bytes
) -> PanTiltPosition | PanTiltLimits | None:
    """Return the parsed contents of an ACCESSORY_MESSAGE, or None if not applicable.

    Returns a :class:`PanTiltPosition` for POSITION and HOME_POSITION, a
    :class:`PanTiltLimits` for LIMITS, and None for messages that carry no state this
    module models (lights, siren, overview completion).
    """
    if identifier in (AccessoryMessage.POSITION, AccessoryMessage.HOME_POSITION):
        return parse_position(payload)
    if identifier == AccessoryMessage.LIMITS:
        return PanTiltLimits(raw=payload)
    return None
