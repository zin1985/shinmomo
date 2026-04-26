-- shinmomo_trace_object_oam_compact_snes9x_20260426.lua
-- Snes9x core fallback: object/OAM compact tracer
-- 大量ログを避ける版。active chain / visible slot / OAM visible entriesだけを定期出力する。

local DUMP_INTERVAL = 60

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

local function logLine(s)
  if console and console.log then
    console.log(s)
  elseif client and client.log then
    client.log(s)
  else
    print(s)
  end
end

local function activeChain()
  local nexts = {}
  for i = 0, 31 do nexts[i] = wram8(0x0A61 + i) end

  local out = {}
  local seen = {}
  local cur = nexts[0] or 0xFF
  local guard = 0
  while cur ~= 0xFF and cur < 32 and not seen[cur] and guard < 32 do
    seen[cur] = true
    out[#out + 1] = h2(cur, 2)
    cur = nexts[cur]
    guard = guard + 1
  end
  out[#out + 1] = "FF"
  return table.concat(out, "->")
end

local function visibleSlots()
  local parts = {}
  for i = 0, 31 do
    local b25 = wram8(0x0B25 + i)
    local ae5 = wram8(0x0AE5 + i)
    local xlo = wram8(0x0BA5 + i)
    local xhi = wram8(0x0BE5 + i)
    local ylo = wram8(0x0C65 + i)
    local yhi = wram8(0x0CA5 + i)
    local e27 = wram8(0x0E27 + i)

    if ae5 ~= 0 or (b25 ~= 0 and b25 ~= 0x20) then
      parts[#parts + 1] =
        "s" .. h2(i,2) ..
        "/b25=" .. h2(b25,2) ..
        "/ae5=" .. h2(ae5,2) ..
        "/e27=" .. h2(e27,2) ..
        "/x=" .. h2(xhi,2) .. ":" .. h2(xlo,2) ..
        "/y=" .. h2(yhi,2) .. ":" .. h2(ylo,2)
    end
  end
  return table.concat(parts, " | ")
end

local function oamVisible()
  local parts = {}
  local count = 0
  for i = 0, 31 do
    local base = 0x0EE9 + i * 4
    local y = wram8(base)
    local tile = wram8(base + 1)
    local attr = wram8(base + 2)
    local x = wram8(base + 3)

    if y ~= 0xE0 then
      count = count + 1
      parts[#parts + 1] =
        "#" .. tostring(i) ..
        "/x=" .. h2(x,2) ..
        "/y=" .. h2(y,2) ..
        "/tile=" .. h2(tile,2) ..
        "/attr=" .. h2(attr,2)
    end
  end
  return count, table.concat(parts, " | ")
end

local function logical1569()
  local t = {}
  for i = 0, 9 do t[#t+1] = h2(wram8(0x1569 + i), 2) end
  return table.concat(t, " ")
end

local function snapshotKey()
  local c, oam = oamVisible()
  return activeChain() .. "::" .. visibleSlots() .. "::" .. tostring(c) .. "::" .. logical1569()
end

local function dump(tag)
  local count, oam = oamVisible()
  logLine(table.concat({
    "TRACE_OBJ_COMPACT",
    "frame=" .. emu.framecount(),
    "tag=" .. tag,
    "domain=" .. tostring(DOMAIN),
    "dirty=" .. h2(wram8(0x0A1B),2),
    "0A1C=" .. h2(wram8(0x0A1C),2),
    "logical_1569=" .. logical1569(),
    "active_chain=" .. activeChain(),
    "visible_slots=" .. visibleSlots(),
    "oam_visible_count=" .. tostring(count),
    "oam_visible=" .. oam
  }, ","))
end

logLine("shinmomo compact object/OAM tracer loaded.")
logLine("memory domain=" .. tostring(DOMAIN))
logLine("DUMP_INTERVAL=" .. tostring(DUMP_INTERVAL))

local prev = snapshotKey()
dump("initial")

while true do
  emu.frameadvance()
  local cur = snapshotKey()
  local f = emu.framecount()
  if cur ~= prev then
    dump("changed")
    prev = cur
  elseif f % DUMP_INTERVAL == 0 then
    dump("periodic")
  end
end
