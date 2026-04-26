-- shinmomo_trace_object_oam_polling_snes9x_20260426.lua
-- Snes9x core fallback版: execute hookなしで、object/OAM周辺WRAMを毎フレーム監視する。
--
-- 目的:
--   $1569 に出ない画面上NPC/イベントspriteが、
--   $0A61 active list / $0B25 group / $0AE5 frame / $0BA5,$0C65 座標 /
--   OAM mirror $0EE9.. に出ているかを確認する。
--
-- 使い方:
--   BizHawk Lua Console -> Open Script
--   このLuaを開く
--   月の神殿などNPCが見えている場面で、画面移動・会話・戦闘前後を操作
--   TRACE_OBJ_OAM 行を貼ってください。
--
-- 注意:
--   これは「広めの網」です。ログが多い場合は DUMP_INTERVAL を大きくしてください。

local DUMP_INTERVAL = 30       -- 30フレームごとに定期dump
local MAX_SLOTS = 64           -- object slot候補の表示範囲
local OAM_BYTES = 64           -- OAM mirror先頭dump byte数

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

local function h2(v, n)
  n = n or 2
  if v == nil then return string.rep("?", n) end
  local mod = 1
  for i = 1, n do mod = mod * 16 end
  return string.format("%0" .. n .. "X", v % mod)
end

local function raw8(addr)
  return memory.read_u8(addr, DOMAIN)
end

local function wram8(addr)
  if DOMAIN == "System Bus" then
    return raw8(0x7E0000 + addr)
  else
    return raw8(addr)
  end
end

local function rangeHexWram(addr, len)
  local t = {}
  for i = 0, len - 1 do
    t[#t + 1] = h2(wram8(addr + i), 2)
  end
  return table.concat(t, " ")
end

local function logLine(s)
  if console and console.log then
    console.log(s)
  elseif client and client.log then
    client.log(s)
  else
    print(s)
  end
end

local function nonzeroCount(addr, len)
  local c = 0
  for i = 0, len - 1 do
    if wram8(addr + i) ~= 0 then c = c + 1 end
  end
  return c
end

local function compactSlots()
  local parts = {}
  for i = 0, MAX_SLOTS - 1 do
    local b25 = wram8(0x0B25 + i)
    local ae5 = wram8(0x0AE5 + i)
    local e27 = wram8(0x0E27 + i)
    local e67 = wram8(0x0E67 + i)
    local ea7 = wram8(0x0EA7 + i)
    local xlo = wram8(0x0BA5 + i)
    local xhi = wram8(0x0BE5 + i)
    local ylo = wram8(0x0C65 + i)
    local yhi = wram8(0x0CA5 + i)
    local anch = wram8(0x0CE5 + i)

    if b25 ~= 0 or ae5 ~= 0 or e27 ~= 0 or e67 ~= 0 or ea7 ~= 0
       or xlo ~= 0 or xhi ~= 0 or ylo ~= 0 or yhi ~= 0 or anch ~= 0 then
      parts[#parts + 1] = table.concat({
        "s" .. h2(i,2),
        "b25=" .. h2(b25,2),
        "ae5=" .. h2(ae5,2),
        "e27=" .. h2(e27,2),
        "e67=" .. h2(e67,2),
        "ea7=" .. h2(ea7,2),
        "x=" .. h2(xhi,2) .. ":" .. h2(xlo,2),
        "y=" .. h2(yhi,2) .. ":" .. h2(ylo,2),
        "ce5=" .. h2(anch,2)
      }, "/")
    end
  end
  return table.concat(parts, " | ")
end

local function keySummary()
  return table.concat({
    rangeHexWram(0x0A61, 32),
    rangeHexWram(0x0B25, 32),
    rangeHexWram(0x0AE5, 32),
    rangeHexWram(0x0E27, 32),
    rangeHexWram(0x0BA5, 32),
    rangeHexWram(0x0C65, 32),
    rangeHexWram(0x0EE9, OAM_BYTES)
  }, "|")
end

local function dump(tag)
  local parts = {
    "TRACE_OBJ_OAM",
    "frame=" .. emu.framecount(),
    "tag=" .. tag,
    "domain=" .. tostring(DOMAIN),
    "0A1B_dirty=" .. h2(wram8(0x0A1B),2),
    "0A1C_oam_work=" .. h2(wram8(0x0A1C),2),
    "active_0A61=" .. rangeHexWram(0x0A61, 32),
    "logical_1569=" .. rangeHexWram(0x1569, 10),
    "nz_obj_fields=" .. tostring(nonzeroCount(0x0A00, 0x0800)),
    "nz_oam_mirror=" .. tostring(nonzeroCount(0x0EE9, 0x0220)),
    "oam_head=" .. rangeHexWram(0x0EE9, OAM_BYTES),
    "slots=" .. compactSlots()
  }
  logLine(table.concat(parts, ","))
end

logLine("shinmomo object/OAM polling tracer loaded.")
logLine("memory domain=" .. tostring(DOMAIN))
logLine("DUMP_INTERVAL=" .. tostring(DUMP_INTERVAL))

local prevKey = keySummary()
dump("initial")

while true do
  emu.frameadvance()
  local f = emu.framecount()
  local curKey = keySummary()

  if curKey ~= prevKey then
    dump("changed")
    prevKey = curKey
  elseif f % DUMP_INTERVAL == 0 then
    dump("periodic")
  end
end
