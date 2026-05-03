-- shinmomo_trace_graphics_runtime_bridge_v4_snes9x_20260503.lua
-- vol016 graphics thread differential logger skeleton.
-- Purpose: add OBSEL / OAM high table / stable-frame friendly columns
-- to the existing mapchip + OAM unified polling approach.

local OUT_PREFIX = "graphics_runtime_bridge_v4_20260503"

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

local function hex2(v) return string.format("%02X", (v or 0) & 0xFF) end
local function hex4(v) return string.format("%04X", (v or 0) & 0xFFFF) end

-- This skeleton intentionally keeps API calls conservative because BizHawk/Snes9x
-- domain names differ. Existing project Lua should supply read8/read_domain helpers.
-- Required new fields for future exact sprite reconstruction:
--   frame, obsel_2101, bgmode_2105, oam_high_hash, stable_frame_flag
--   plus existing bg_hash0,bg_hash1,bg_hash2,cgram_hash,oam_hash,obj_count,oam_visible_count.

local header = table.concat({
  "frame","obsel_2101","bgmode_2105","bg_hash0","bg_hash1","bg_hash2",
  "cgram_hash","oam_hash","oam_high_hash","obj_head","obj_count",
  "obj_chain_hash","oam_visible_count","dma_count","stable_frame_flag"
}, ",")

log("GRAPHICS_RUNTIME_BRIDGE_V4_LOADED")
log("CSV_HEADER," .. header)

-- Implementation note:
-- Merge this skeleton into shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua.
-- The key addition is reading $2101 OBSEL and the OAM high table in the same frame
-- as VRAM/CGRAM/OAM snapshots.
