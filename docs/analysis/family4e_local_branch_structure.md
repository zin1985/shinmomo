# Family 0x4E local branch structure

Updated: 2026-09-26

Canonical Drive ROM verified: 2,097,152 bytes, SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98.

Confirmed from ROM script pack family 0x4E:

- A4 15 at CC:1B18 and A4 16 at CC:1B1E precede a compact local control structure at CC:1B20.
- The structure contains five tagged local targets: 0x48 -> CC:1B34, 0x49 -> CC:1B3B, 0x7C -> CC:1B42, 0x6C -> CC:1B45, 0x7B -> CC:1B52, then 0x00 terminator.
- The 0x7C arm lands exactly on A4 17 at CC:1B42.

Strong hypothesis: control 0x43 introduces a multi-arm selector/dispatch table with tagged 16-bit local targets. This gives 0x4E:17 explicit branch-arm provenance and shows family 0x4E should not inherit family 0x50 fixed record lengths.

Unconfirmed: exact tag semantics, runtime-selected arm, display reachability of 0x15/0x16, exact speaker/location.

Next: identify the 0x43 handler and tag semantics, trace the CC:1B42 arm to merge/termination, then apply branch-aware context classification to recovered source pairs.
