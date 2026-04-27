-- shinmomo_trace_dialogue_v22_mode02_display_compact_snes9x_20260427.lua
-- v22: v21で「別の台詞ブロック」を拾ってしまう問題への対策版
--
-- 目的:
--   1) $12AA=02 を current dialogue source として優先し、plain source(C7:02xx等)を混ぜない
--   2) mode02 rawは「圧縮/特殊source」として短く記録
--   3) 実際に画面へ出ている $12B2/$12B3/$12C4/$12C5 の表示tokenを低ログ量で蓄積
--
-- 出力:
--   TRACE_DIALOGUE_V22_MODE02_SOURCE
--   TRACE_DIALOGUE_V22_DISPLAY_LINE
--   TRACE_DIALOGUE_V22_SKIP
--
-- 注意:
--   mode02の完全デコードはまだ未対応。
--   ただし、v21のように無関係なplain sourceを現行台詞として混ぜることを避ける。

local READ_LEN = 32
local MODE02_SUPPRESS_PLAIN_FRAMES = 180
local DISPLAY_IDLE_FLUSH_FRAMES = 90

local function list_domains()
  local ok, domains = pcall(function() return memory.getmemorydomainlist() end)
  if ok and domains then return domains end
  return {}
end

local DOMAINS = list_domains()

local function choose_domain(preferred)
  for _, want in ipairs(preferred) do
    for _, got in ipairs(DOMAINS) do
      if got == want then return got end
    end
  end
  for _, want in ipairs(preferred) do
    local wl = string.lower(want)
    for _, got in ipairs(DOMAINS) do
      local gl = string.lower(got)
      if string.find(gl, wl, 1, true) then return got end
    end
  end
  return nil
end

local WRAM_DOMAIN = choose_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}) or DOMAINS[1]
local ROM_DOMAIN  = choose_domain({"CARTROM", "Cart ROM", "Cartridge ROM", "ROM", "Snes ROM", "SNES ROM"})

local function domain_size(domain)
  if domain == nil then return 0 end
  local ok, sz = pcall(function() return memory.getmemorydomainsize(domain) end)
  if ok and sz then return sz end
  if domain == WRAM_DOMAIN then return 0x20000 end
  if domain == ROM_DOMAIN then return 0x800000 end
  return 0
end

local function safe_read_u8(addr, domain)
  if domain == nil then return nil end
  local sz = domain_size(domain)
  if sz > 0 and (addr < 0 or addr >= sz) then return nil end
  local ok, v = pcall(function() return memory.read_u8(addr, domain) end)
  if ok then return v end
  return nil
end

local function wram8(addr)
  return safe_read_u8(addr, WRAM_DOMAIN) or 0
end

local function h2(v) if v == nil then return "??" end return string.format("%02X", v % 0x100) end
local function h4(v) if v == nil then return "????" end return string.format("%04X", v % 0x10000) end
local function h6(v) if v == nil then return "??????" end return string.format("%06X", v % 0x1000000) end

local function logLine(s)
  if console and console.log then console.log(s)
  elseif client and client.log then client.log(s)
  else print(s) end
end

local SINGLE = {
  ["50"]=" ", ["51"]="  ", ["52"]="   ",
  ["5C"]="!", ["7D"]="「", ["7E"]="」", ["80"]="ー",
  ["90"]="あ", ["91"]="い", ["92"]="う", ["93"]="え", ["94"]="お",
  ["95"]="か", ["96"]="き", ["97"]="く", ["98"]="け", ["99"]="こ",
  ["9A"]="さ", ["9B"]="し", ["9C"]="す", ["9D"]="せ", ["9E"]="そ", ["9F"]="た",
  ["A0"]="ち", ["A1"]="つ", ["A2"]="て", ["A3"]="と", ["A4"]="な", ["A5"]="に",
  ["A8"]="の", ["A9"]="は", ["AE"]="ま", ["B0"]="む", ["B2"]="も",
  ["B5"]="よ", ["B6"]="ら", ["B7"]="り", ["B8"]="る", ["B9"]="れ", ["BA"]="ろ",
  ["BC"]="を", ["BD"]="ん", ["BE"]="で", ["DF"]="び", ["F5"]="っ", ["F6"]="ゃ", ["F8"]="ゅ",
  ["D0"]="が", ["D6"]="じ", ["D9"]="だ"
}

local DICT02 = {
  ["84"]="行く",
  ["9B"]="旅の人",
  ["A0"]="桃太郎",
  ["AC"]="オニ",
  ["D7"]="入れ"
}

local KANJI = {
  ["1800"]="桃", ["1801"]="太", ["1802"]="郎",
  ["1811"]="西", ["1813"]="北", ["1815"]="体",
  ["184C"]="刀", ["1850"]="銀", ["1851"]="次",
  ["188F"]="火", ["18DB"]="鬼", ["18F2"]="無",
  ["19BF"]="行", ["19D7"]="入", ["19EB"]="穴",
  ["1A1A"]="言", ["1A31"]="理"
}

local function src_ptr()
  local lo = wram8(0x00B1)
  local hi = wram8(0x00B2)
  local bank = wram8(0x00B3)
  return bank, lo + hi * 0x100
end

local function hirom_offset(bank, addr)
  local b = bank
  if b >= 0xC0 then b = b - 0xC0
  elseif b >= 0x80 then b = b - 0x80 end
  return b * 0x10000 + addr
end

local function read_rom(bank, addr, n)
  if ROM_DOMAIN == nil then return nil, "no_rom_domain" end
  local base = hirom_offset(bank, addr)
  local sz = domain_size(ROM_DOMAIN)
  if base < 0 or base + n > sz then return nil, "rom_oob:" .. h6(base) end
  local t = {}
  for i=0,n-1 do
    local v = safe_read_u8(base+i, ROM_DOMAIN)
    if v == nil then return nil, "rom_read_failed" end
    t[#t+1] = v
  end
  return t, "rom:" .. h6(base)
end

local function hex_bytes(t)
  local out = {}
  for _, b in ipairs(t or {}) do out[#out+1] = h2(b) end
  return table.concat(out, " ")
end

local function decode_display_token()
  local b2 = wram8(0x12B2)
  local b3 = wram8(0x12B3)
  local c4 = wram8(0x12C4)
  local c5 = wram8(0x12C5)

  -- c4/c5 reverse dict
  if c5 == 0x02 then
    return DICT02[h2(c4)] or ("{02" .. h2(c4) .. "}")
  end

  -- b2/b3 kanji
  if b2 >= 0x18 and b2 < 0x20 then
    local key = h2(b2) .. h2(b3)
    return KANJI[key] or ("{K" .. key .. "}")
  end

  -- c4/c5 kanji
  if c4 >= 0x18 and c4 < 0x20 then
    local key = h2(c4) .. h2(c5)
    return KANJI[key] or ("{K" .. key .. "}")
  end

  local first = SINGLE[h2(c4)] or ""
  local second = SINGLE[h2(b2)] or ""

  if first ~= "" and second ~= "" and c4 == b2 then return first end
  return first .. second
end

local function state()
  return table.concat({
    "12AA=" .. h2(wram8(0x12AA)),
    "12A9=" .. h2(wram8(0x12A9)),
    "12AD=" .. h2(wram8(0x12AD)),
    "12B2=" .. h2(wram8(0x12B2)),
    "12B3=" .. h2(wram8(0x12B3)),
    "12B4=" .. h2(wram8(0x12B4)),
    "12B5=" .. h2(wram8(0x12B5)),
    "12B6=" .. h2(wram8(0x12B6)),
    "12BC=" .. h2(wram8(0x12BC)),
    "12C4=" .. h2(wram8(0x12C4)),
    "12C5=" .. h2(wram8(0x12C5))
  }, ",")
end

local function source_state_words()
  local out = {}
  for a = 0x1264, 0x1286, 2 do
    local lo = wram8(a)
    local hi = wram8(a+1)
    if lo ~= 0 or hi ~= 0 then out[#out+1] = "$" .. h4(a) .. "=" .. h2(hi) .. h2(lo) end
  end
  return table.concat(out, " ")
end

local function active_text()
  return wram8(0x12B4) == 0x50 or wram8(0x12AD) == 0x00 or wram8(0x12B2) ~= 0x00
end

logLine("shinmomo dialogue mode02/display compact tracer v22 loaded.")
logLine("domains=" .. table.concat(DOMAINS, "|") .. ", WRAM=" .. tostring(WRAM_DOMAIN) .. ", ROM=" .. tostring(ROM_DOMAIN))
logLine("Mode02 prioritized. Plain source is suppressed shortly after mode02.")
logLine("TRACE_DIALOGUE_V22_READY,frame=" .. emu.framecount() .. "," .. state())

local last_mode02_key = ""
local last_mode02_frame = -9999
local display_buf = ""
local last_display_key = ""
local last_display_frame = emu.framecount()
local last_plain_suppressed_log = -9999

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if active_text() then
    local mode = wram8(0x12AA)
    local bank, addr = src_ptr()

    -- actual/current special source
    if mode == 0x02 then
      local bytes, src = read_rom(bank, addr, READ_LEN)
      if bytes ~= nil then
        local key = h2(bank)..":"..h4(addr)..":"..hex_bytes(bytes)
        if key ~= last_mode02_key then
          logLine(table.concat({
            "TRACE_DIALOGUE_V22_MODE02_SOURCE",
            "frame=" .. f,
            "src_ptr=" .. h2(bank) .. ":" .. h4(addr),
            "source=" .. tostring(src),
            "raw=" .. hex_bytes(bytes),
            "note=mode02_special_or_compressed_source_not_plain",
            "source_state=" .. source_state_words(),
            state()
          }, ","))
          last_mode02_key = key
          last_mode02_frame = f
        end
      end
    else
      -- Do not mix old/plain fallback source immediately after mode02.
      if (f - last_mode02_frame) < MODE02_SUPPRESS_PLAIN_FRAMES then
        if f - last_plain_suppressed_log > 120 then
          logLine("TRACE_DIALOGUE_V22_SKIP,frame=" .. f .. ",reason=plain_source_suppressed_after_mode02,src_ptr=" .. h2(bank) .. ":" .. h4(addr) .. "," .. state())
          last_plain_suppressed_log = f
        end
      end
    end

    -- Display work token, low volume.
    local tok = decode_display_token()
    local dkey = tok .. ":" .. h2(wram8(0x12B2)) .. ":" .. h2(wram8(0x12B3)) .. ":" .. h2(wram8(0x12C4)) .. ":" .. h2(wram8(0x12C5)) .. ":" .. h2(wram8(0x12BC))
    if tok ~= "" and dkey ~= last_display_key then
      display_buf = display_buf .. tok
      last_display_key = dkey
      last_display_frame = f
    end

    if display_buf ~= "" and (f - last_display_frame) > DISPLAY_IDLE_FLUSH_FRAMES then
      logLine("TRACE_DIALOGUE_V22_DISPLAY_LINE,frame=" .. f .. ",display_decode=" .. display_buf .. "," .. state())
      display_buf = ""
      last_display_key = ""
    end
  else
    if display_buf ~= "" and (f - last_display_frame) > DISPLAY_IDLE_FLUSH_FRAMES then
      logLine("TRACE_DIALOGUE_V22_DISPLAY_LINE,frame=" .. f .. ",display_decode=" .. display_buf .. "," .. state())
      display_buf = ""
      last_display_key = ""
    end
  end
end
