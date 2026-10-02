# Handoff: CC1160 phase discriminator frontier

Base main: `71d684c9f4da98826bba87a2c3693def659d0748`

The current highest-priority unresolved transition crosslink is `CC:1160 -> pack 0xCE entry 0x02 -> arrival (22,28)`. Bounds cannot distinguish its five candidate canonical configs. The committed configuration index now narrows the next inspection to five distinct commands: `CD:9156`, `CD:916D`, `CD:9186`, `CD:919F`, `CD:91CC`.

Important split: l086/l088/l089/l085 are tileset-4, flag-0x80; l087 is tileset-5, flag-0x00. Treat this only as a discriminator axis, not yet as a story-phase label.

Next ROM-enabled action: inspect control flow immediately around those commands and externalize predicate/state address, comparison, branch target, and selected config. Never commit ROM/raw dumps. If canonical Drive ROM is unavailable, skip runtime/ROM assertions and work the ten arrival-XY-only event-trigger gaps instead.

Canonical ROM was not accessible in this cycle. No alternate ROM was used.
