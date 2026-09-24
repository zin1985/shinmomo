# Goal13 dynamic probe

This directory contains the reproducible dynamic-analysis entry point for the
NPC/OAM path. It deliberately does not contain a ROM, savestate, or raw dump.

## Required runtime

Use a debugger-capable SNES emulator (Mesen2 or bsnes-plus) with Lua/debugger
support. The ROM is supplied out-of-tree by the operator. Start the emulator
with the supplied ROM, attach the probe script, and export only the aggregated
`0799_trace_summary.json` and `oam_append_summary.json` files. Do not commit
frame-by-frame traces or memory dumps.

## Probe contract

The probe must record, per `$0799,X` write/read event: PC, X, A/Y, flags,
before/after value, frame, NPC slot, caller, and whether the corresponding
append buffer/count changed. It must also record branch outcomes at the
`89:BA36`, `89:BA48`, `89:BA70`, and `89:BAC8` window. The reducer should emit
counts by PC, bit7 set/clear, and append/skip correlation.

## Current cycle

`2026-09-25`: the provided ROM was available and hashed, but no supported
debugger executable was installed in the Work environment. No dynamic result
is claimed. The next cycle should install or provision Mesen2/bsnes-plus and
run at least the normal-visible and off-screen cases before changing Goal13's
evidence percentage.
