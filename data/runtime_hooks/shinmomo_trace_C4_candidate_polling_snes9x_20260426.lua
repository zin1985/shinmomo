-- shinmomo_trace_C4_candidate_polling_snes9x_20260426.lua
-- Snes9x core fallback版
-- event.onmemoryexecute が使えない場合に、毎フレームWRAMを監視して
-- $1923/$1924/$192A/$1957/$1958/$195E/$1569 の変化をログする。

local CANDIDATE_KEYS = {
  [0x10] = "relation_candidate_slot_0",
  [0x11] = "relation_candidate_slot_1",
  [0x12] = "relation_candidate_slot_2",
  [0x13] = "relation_candidate_slot_3",
}

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
  local mask = (n == 2) and 0xFF or ((n == 4) and 0xFFFF or 0xFFFFFF)
  return string.format("%0" .. n .. "X", v & mask)
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

local function entityFlag180A(entity)
  if entity == nil or entity <= 0 then return 0 end
  return wram8(0x180A + entity - 1)
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

local function snapshot()
  local e = wram8(0x192A)
  return {
    frame = emu.framecount(),
    p1923 = wram8(0x1923),
    p1924 = wram8(0x1924),
    p192A = e,
    p192B = wram8(0x192B),
    p1957 = wram8(0x1957),
    p1958 = wram8(0x1958),
    p195E = wram8(0x195E),
    p195F = wram8(0x195F),
    p1620 = wram8(0x1620),
    flag180A = entityFlag180A(e),
    list1569 = rangeHexWram(0x1569, 10),
  }
end

local function key(s)
  return table.concat({
    h2(s.p1923), h2(s.p1924), h2(s.p192A), h2(s.p192B),
    h2(s.p1957), h2(s.p1958), h2(s.p195E), h2(s.p195F),
    h2(s.p1620), h2(s.flag180A), s.list1569
  }, "|")
end

local function candidateLabel(k)
  return CANDIDATE_KEYS[k] or ""
end

local function dump(tag, s)
  local parts = {
    "TRACE_C4_POLL",
    "frame=" .. s.frame,
    "tag=" .. tag,
    "1923=" .. h2(s.p1923),
    "1923_label=" .. candidateLabel(s.p1923),
    "1924=" .. h2(s.p1924),
    "192A=" .. h2(s.p192A),
    "192B=" .. h2(s.p192B),
    "1957=" .. h2(s.p1957),
    "1958=" .. h2(s.p1958),
    "195E=" .. h2(s.p195E),
    "195F=" .. h2(s.p195F),
    "1620=" .. h2(s.p1620),
    "180A_entity_flag=" .. h2(s.flag180A),
    "1569=" .. s.list1569
  }
  logLine(table.concat(parts, ","))
end

logLine("shinmomo Snes9x polling tracer loaded.")
logLine("memory domain=" .. tostring(DOMAIN))
logLine("This fallback does not use event.onmemoryexecute.")
logLine("Watch TRACE_C4_POLL lines when 1923/192A/1958/195E/1569 changes.")

local prev = snapshot()
dump("initial", prev)

while true do
  emu.frameadvance()
  local cur = snapshot()
  if key(cur) ~= key(prev) then
    local tag = "changed"

    if cur.p195E ~= prev.p195E then
      tag = "195E_changed"
    elseif cur.p1958 ~= prev.p1958 then
      tag = "1958_changed"
    elseif cur.p192A ~= prev.p192A then
      tag = "192A_changed"
    elseif cur.p1923 ~= prev.p1923 then
      tag = "1923_changed"
    elseif cur.list1569 ~= prev.list1569 then
      tag = "1569_changed"
    end

    dump(tag, cur)
    prev = cur
  end
end
