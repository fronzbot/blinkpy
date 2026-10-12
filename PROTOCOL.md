# Blink LiveView Protocol Notes

Unofficial documentation of the LiveView streaming path, derived from
the official Android app and verified against live camera traffic.
Covers the cloud API and the IMMI media transport. No firmware,
trust-store, or onboarding internals are documented here.

## 0. Provenance

Every layout, field size and behavior below was cross-checked two ways:
decompilation of the official app (session construction, native player
calls) and live captures from real cameras (handshake bytes, framing,
keepalive cadence, session lifecycle). Values marked "observed" held
across multiple sessions and camera families; anything account- or
firmware-version-dependent is noted inline.

## 1. Creating a session

```text
POST {base}/api/v6/accounts/{account}/networks/{network}/cameras/{camera}/liveview   (battery/catalina)
POST {base}/api/v2/accounts/{account}/networks/{network}/owls/{camera}/liveview       (Mini/owl)
POST {base}/api/v2/accounts/{account}/networks/{network}/doorbells/{camera}/liveview  (doorbell)
```

Body:

```json
{"intent": "liveview", "motion_event_start_time": null}
```

`intent` may also be `"extended_liveview"`; entitled accounts receive
`type: "elv"` with 5400 s durations instead of `type: "lv"`.

Response (fields actually returned):

```text
server                  immis://host:443/<conn>__IMDS_<…>?client_id=N
liveview_token          ~22 chars, required for media auth
command_id              pollable command id
parent_command_id
polling_interval        seconds (typically 15)
session_duration        seconds (typically 300)
continue_interval       seconds (typically 30; 5400 on elv)
continue_warning        seconds
extended_duration       seconds (typically 5400)
type                    "lv" or "elv"
is_mclv                 multi-client session flag
first_joiner
video_id / media_id
options                 e.g. {"poor_connection": false}
```

Poll `GET /network/{network}/command/{command_id}` (complete when the
command leaves `new`/`running`; success marker `status_code` 908),
then `POST /network/{network}/command/{command_id}/done/` when finished.
`command/done` is best-effort; sessions age out server-side regardless.

## 2. IMMI media transport

TLS to the `server` host/port, then a 122-byte authentication header:

```text
magic              00 00 00 28
serial             u32 len (=16) + 16 bytes, null-padded (camera serial)
client_id          u32, big-endian (from ?client_id=)
static             01 08
token              u32 len (=64) + 64 bytes, null-padded (liveview_token)
conn_id            u32 len (=16) + 16 bytes (URL path tail split on "__", head)
trailer            00 00 00 01
```

Sending null bytes for the token is rejected by the relay; the real
`liveview_token` is required.

Packets: 9-byte header (`msgtype(1) + sequence(4) + length(4)`), then
payload. Type `0x00` with a `0x47`-leading payload is MPEG-TS (188-byte
packets, H.264 + AAC observed). Other message types exist (session
commands, audio config, accessory messages) and should be skipped by
video-only consumers.

Liveness: keepalive packet (`0x0A` header, empty payload) roughly every
10 s and latency-stats packet (`0x12`) every 1 s. Relays drop consumers
that go silent (~15 s observed). Session lifetimes are server-managed
(`session_duration`, `continue_interval`); renew or re-create per policy.

## 3. Client guidance

- Parse the full session response; at minimum keep token, command id,
  polling interval and durations.
- Authenticate with the real token; never log it (length only).
- Run keepalive/latency + command polling alongside reading.
- Guarantee `command/done` + socket close in a `finally` path.
- Expect `is_mclv`/join flags when a second viewer joins an active
  session; prefer joining over creating duplicates.
- Throughput is ~1–1.5 Mbps per camera; setup is fast once the session
  exists, but command pickup can take 30 s–2 min.
