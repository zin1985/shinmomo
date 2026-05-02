-- shinmomo_graphics_mapchip_oam_trace_v2_spec_20260501.lua
-- Specification stub for the next Snes9x/BizHawk polling logger.
-- This file is intentionally conservative: adapt memory-domain names per emulator.

-- Goals:
-- 1. Dump VRAM/CGRAM/OAM at stable field/town frames.
-- 2. Capture PPU registers required to decode BG tilemap/char base.
-- 3. Capture visible object chain snapshots for NPC/OAM throttling patch validation.

-- Required outputs:
--   vram_frameXXXXXX.bin
--   cgram_frameXXXXXX.bin
--   oam_frameXXXXXX.bin
--   ppu_state_frameXXXXXX.csv
--   visible_chain_frameXXXXXX.csv
--   manifest_graphics_oam_trace.csv

-- Key PPU registers to log if available:
--   $2105 BGMODE
--   $2107..$210A BG1SC..BG4SC
--   $210B..$210C BG12NBA/BG34NBA
--   $212C..$212D TM/TS

-- Key WRAM symbols to snapshot:
--   $0A61 active linked list head/entries
--   $0A1F prev link
--   $0AA3 sort/depth key
--   $0AE5 active count
--   $0EE9 OAM mirror

print('TRACE_GRAPHICS_MAPCHIP_OAM_V2_SPEC_READY')
