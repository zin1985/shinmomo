-- shinmomo_oam_static_guard_probe_v1_snes9x_20260427.lua
-- OAM/static object skip を本当にIPS化できるか見るための安全確認Lua
--
-- 目的:
--   「全objectが前回と同じ」かつ「OAM buildを丸ごと飛ばしてもよさそうな静止フレーム」が
--   どれくらいあるかを見る。
--
-- 出力:
--   TRACE_OAM_STATIC_GUARD
--
-- 判断:
--   all_static=1 が長く続く場面が多い → full-frame OAM build skipの候補
--   active_changed/object_changedが頻繁 → per-object skipは危険
--
-- 注意:
--   これは測定用。ROMは変更しません。

local function choose_domain()
  local domains = memory.getmemorydomainlist()
  local preferred = {"System Bus", "WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}
  for _, want in ipairs(preferred) do
    for _, got in ipairs(domains) do
      if got == want then return got end
    end
  end
  return domains[1]
end

local DOMAIN = choose_domain()

local function r8(addr)
  if DOMAIN == "System Bus" then
    return memory.read_u8(0x7E0000 + addr, DOMAIN)
  else
    return memory.read_u8(addr, DOMAIN)
  end
end

local function s16(lo, hi)
  local v = lo + hi * 0x100
  if v >= 0x8000 then v = v - 0x10000 end
  return v
end

local function h2(v) return string.format("%02X", v % 0x100) end

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

local function object_sig(phys)
  local x = s16(r8(0x0BA7 + phys), r8(0x0BE7 + phys))
  local y = s16(r8(0x0C67 + phys), r8(0x0CA7 + phys))
  local group_flags = r8(0x0B25 + phys)
  local frame = r8(0x0AE5 + phys)
  local anim_misc = r8(0x0E27 + phys)
  local attr = r8(0x0D25 + phys)
  return table.concat({x,y,group_flags,frame,anim_misc,attr}, ":")
end

local prev_all = nil
local stable_run = 0
local last_line = ""
local interval = 10

log("shinmomo OAM static guard probe loaded. domain=" .. tostring(DOMAIN))
log("TRACE_OAM_STATIC_GUARD_READY,frame=" .. emu.framecount())

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if f % interval == 0 then
    local sigs = {}
    local changed = 0
    local active_count = 0
    local nonzero_frame = 0
    local draw_hidden = 0

    -- B03D uses active list from $0A61, but for safety we snapshot the first 0x40 object slots.
    -- Summary also counts likely active slots by $0AE5 != 0.
    for phys = 0, 0x3F do
      local sig = object_sig(phys)
      sigs[#sigs+1] = sig
      if r8(0x0AE5 + phys) ~= 0 then active_count = active_count + 1 end
      if r8(0x0AE5 + phys) ~= 0 then nonzero_frame = nonzero_frame + 1 end
      if (r8(0x0B25 + phys) & 0x40) ~= 0 then draw_hidden = draw_hidden + 1 end
    end

    local all_sig = table.concat(sigs, "|")
    local all_static = 0
    if prev_all ~= nil and prev_all == all_sig then
      all_static = 1
      stable_run = stable_run + 1
    else
      stable_run = 0
    end
    prev_all = all_sig

    local line = table.concat({
      "TRACE_OAM_STATIC_GUARD",
      "frame=" .. f,
      "all_static=" .. all_static,
      "stable_run_samples=" .. stable_run,
      "active_like_slots=" .. active_count,
      "nonzero_frame_slots=" .. nonzero_frame,
      "draw_hidden_slots=" .. draw_hidden,
      "oam_budget_left_0A1C=" .. h2(r8(0x0A1C)),
      "active_head_0A61=" .. h2(r8(0x0A61)),
      "oam_index_1109=" .. h2(r8(0x1109)),
      "oam_pack_count_110C=" .. h2(r8(0x110C))
    }, ",")

    if line ~= last_line then
      log(line)
      last_line = line
    end
  end
end
